# This software was developed by employees of the National Institute
# of Standards and Technology (NIST), an agency of the Federal
# Government. Pursuant to title 17 United States Code Section 105, works
# of NIST employees are not subject to copyright protection in the United
# States and are considered to be in the public domain. Permission to freely
# use, copy, modify, and distribute this software and its documentation
# without fee is hereby granted, provided that this notice and disclaimer
# of warranty appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
# WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
# ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
# BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
# ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS
# SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR
# OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY
# OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT
# OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#
# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with
# the code in compliance with the conditions of those licenses.

#==================================================================================
# DPA Move List Reference Model.
# Based on WINNF-TS-0112, Version V1.4.1, 16 January 2018.

# The main routine is 'move_list.findMoveList()'.
#==================================================================================

import numpy as np
from operator import attrgetter, iadd
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
from shapely.geometry import MultiPolygon as MPolygon
from collections import namedtuple
from multiprocessing import Pool
from functools import partial
from enum import Enum

# Import WINNF reference models including propagation, geo, and CBSD antenna gain models
from reference_models.propagation import wf_itm
# from reference_models.geo import terrain
from reference_models.geo import vincenty
from reference_models.antenna import antenna

# Initialize terrain driver
# terrainDriver = terrain.TerrainDriver()
terrainDriver = wf_itm.terrainDriver

# Set constant parameters based on requirements in the WINNF-TS-0112 [R2-SGN-24]
CAT_A_NBRHD_DIST = 150          # neighborhood distance for Cat-A CBSD (in km)
CAT_B_NBRHD_DIST = 200          # neighborhood distance for Cat-B CBSD (in km)
CAT_B_NBRHD_DIST_FOR_HT = 300   # neighborhood distance for Cat-B CBSD (in km) in
                                # consideration of antenna height
CAT_B_LONG_HT = 200             # height of Cat_B CBSD (in meters) in consideration of
                                # neighborhood distance Cat_B_NBRHD_DIST_FOR_HT
CAT_B_NBRHD_DIST_OOB = 25       # neighborhood distance for Cat-B CBSD
                                # for out-of-band inland DPA (in km)
PROTECTION_PERCENTILE = 95      # Monte Carlo percentile for protection

# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0

# Frequency range of co-channel DPAs (Hz)
LOW_FREQ_COCH = 3550000000
HIGH_FREQ_COCH = 3700000000

# Out-of-band maximum conducted power (dBm/MHz) (FCC Part 96 Rules (96.41))
OOB_POWER_WITHIN_10MHZ = -13
OOB_POWER_OUTSIDE_10MHZ = -25
OOB_POWER_BELOW_3530MHZ = -40

# Define CBSD grant, i.e., a tuple with named fields of 'latitude', 'longitude', 'height',
# 'indoorDeployment', 'antennaAzimuth', 'antennaGain', 'antennaBeamwidth', 'grantIndex',
# 'maxEirp', 'lowFrequency', 'highFrequency'
CBSDGrant = namedtuple('CBSDGrant',
                       ['latitude', 'longitude', 'height', 'indoorDeployment',
                        'antennaAzimuth', 'antennaGain', 'antennaBeamwidth',
                        'grantIndex', 'maxEirp', 'lowFrequency', 'highFrequency'])

# Define interference contribution, i.e., a tuple with named fields of
# 'grantIndex', 'medianInterference', 'randomInterference', 'bearing_c_cbsd'
InterferenceContribution = namedtuple('InterferenceContribution',
                                      ['grantIndex', 'medianInterference',
                                       'randomInterference', 'bearing_c_cbsd'])

# Define protection constraint, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'lowFrequency', 'highFrequency'
ProtectionConstraint = namedtuple('ProtectionConstraint',
                                  ['latitude', 'longitude',
                                   'lowFrequency', 'highFrequency'])

# Define an enumeration class named DpaType with members
# 'CO_CHANNEL', 'OUT_OF_BAND'
class DpaType(Enum):
    CO_CHANNEL = 1
    OUT_OF_BAND = 2


# A Cache for storing the height-above-average-terrain computed for neighborhood
# determination.
HaatCache = {}
def GetHaat(lat_cbsd, lon_cbsd, height_cbsd, height_is_agl):
    
    global HaatCache
    
    # Simple technique (non-LRU) to prevent the cache size from increasing forever
    if len(HaatCache) > 1e7:
       HaatCache = {}  # Simply restart from scratch

    key = (lat_cbsd, lon_cbsd, height_cbsd, height_is_agl)
    if key not in HaatCache:
       HaatCache[key] = wf_itm.ComputeHaat(lat_cbsd, lon_cbsd, height_cbsd, height_is_agl)

    return HaatCache[key]


def findGrantsInsideNeighborhood(reg_requests, grant_requests, grant_index, constraint,
                                 exclusion_zone, dpa_type):

    """
    Identify the Nc CBSD grants in the neighborhood of protection constraint.

    Inputs:
        reg_requests:   a list of CBSD registration requests
        grant_requests: a list of grant requests
        grant_index:    an array of grant indices
        constraint:     protection constraint of type ProtectionConstraint
        exclusion_zone: a polygon object or a list of locations.
                        If it is a list of locations, each one is a tuple
                        with fields 'latitude' and 'longitude'.
                        Default value is 'None'.
        dpa_type:       an enum member of class DpaType

    Returns:
        grants_inside:  a list of grants, each one being a namedtuple of type CBSDGrant,
                        of all CBSDs inside the neighborhood of the protection constraint.
    """

    # Initialize an empty list
    grants_inside = []

    # For co-channel offshore/inland DPAs, make sure exclusion zone is a polygon
    if dpa_type is not DpaType.OUT_OF_BAND:
        if isinstance(exclusion_zone, SPolygon) or isinstance(exclusion_zone, MPolygon):
            polygon_ex_zone = exclusion_zone
        else:
            polygon_ex_zone = SPolygon(exclusion_zone)

    # Loop over each CBSD grant
    for i in range(len(reg_requests)):

        # Check CBSD location
        cbsd_cat = reg_requests[i].get('cbsdCategory')
        lat_cbsd = reg_requests[i].get('installationParam', {}).get('latitude')
        lon_cbsd = reg_requests[i].get('installationParam', {}).get('longitude')
        height_cbsd = reg_requests[i].get('installationParam', {}).get('height')
        height_type_cbsd = reg_requests[i].get('installationParam', {}).get('heightType')
        if height_type_cbsd == 'AMSL':
            altitude_cbsd = terrainDriver.GetTerrainElevation(lat_cbsd, lon_cbsd)
            height_cbsd = height_cbsd - altitude_cbsd

        # Sanity check on CBSD antenna height
        if height_cbsd < 1 or height_cbsd > 1000:
            raise ValueError('CBSD height is less than 1 m or greater than 1000 m.')

        # Compute distance from CBSD location to protection constraint location
        lat_c = constraint.latitude
        lon_c = constraint.longitude
        dist_km, bearing, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd,
                                                               lat_c, lon_c)

        # Check if CBSD is inside the neighborhood of protection constraint
        cbsd_in_nbrhd = False

        if cbsd_cat == 'A':
            if dpa_type is not DpaType.OUT_OF_BAND:
                point_cbsd = SPoint(lat_cbsd, lon_cbsd)
                if dist_km <= CAT_A_NBRHD_DIST and polygon_ex_zone.contains(point_cbsd):
                    cbsd_in_nbrhd = True
        elif cbsd_cat == 'B':
            if dpa_type is not DpaType.OUT_OF_BAND:
                if dist_km <= CAT_B_NBRHD_DIST:
                    cbsd_in_nbrhd = True
                elif dist_km <= CAT_B_NBRHD_DIST_FOR_HT:
                    height_cbsd_haat = GetHaat(lat_cbsd, lon_cbsd, height_cbsd,
                                               height_is_agl=(height_type_cbsd != 'AMSL'))
                    if height_cbsd_haat >= CAT_B_LONG_HT:
                        cbsd_in_nbrhd = True
            else:
                if dist_km <= CAT_B_NBRHD_DIST_OOB:
                    cbsd_in_nbrhd = True
        else:
            raise ValueError('Unknown category %s' % cbsd_cat)

        # Check frequency range
        low_freq_cbsd = grant_requests[i].get('operationParam', {}). \
            get('operationFrequencyRange', {}).get('lowFrequency')
        high_freq_cbsd = grant_requests[i].get('operationParam', {}). \
            get('operationFrequencyRange', {}).get('highFrequency')
        if dpa_type is not DpaType.OUT_OF_BAND:
            low_freq_c = constraint.lowFrequency
            high_freq_c = constraint.highFrequency
            overlapping_bw = min(high_freq_cbsd, high_freq_c) \
                             - max(low_freq_cbsd, low_freq_c)
            freq_check = (overlapping_bw > 0)
        else:
            freq_check = True

        # Return CBSD information if it is inside the neighborhood of protection constraint
        if cbsd_in_nbrhd and freq_check:
            cbsd_grant = CBSDGrant(
                # Get information from the registration request
                latitude=lat_cbsd,
                longitude=lon_cbsd,
                height=height_cbsd,
                indoorDeployment=reg_requests[i].get('installationParam',{}).get('indoorDeployment'),
                antennaAzimuth=reg_requests[i].get('installationParam',{}).get('antennaAzimuth'),
                antennaGain=reg_requests[i].get('installationParam',{}).get('antennaGain'),
                antennaBeamwidth=reg_requests[i].get('installationParam',{}).get('antennaBeamwidth'),
                # Get information from the grant request
                grantIndex=grant_index[i],
                maxEirp=grant_requests[i].get('operationParam',{}).get('maxEirp'),
                lowFrequency=low_freq_cbsd,
                highFrequency=high_freq_cbsd)

            grants_inside.append(cbsd_grant)

    return grants_inside


def ComputeOOBConductedPower(low_freq_cbsd, low_freq_c, high_freq_c):

    """
    Compute maximum conducted power of a CBSD grant to an out-of-band
    protection constraint based on FCC Part 96 Rules (96.41)

    Inputs:
        low_freq_cbsd:  low frequency of CBSD grant channel (Hz)
        low_freq_c:     low frequency of protection constraint (Hz)
        high_freq_c:    high frequency of protection constraint (Hz)

    Returns:
        Maximum out-of-band conducted power (dBm)
    """

    # Compute overlapping bandwidths
    overlap_bw_within_10MHz = min(low_freq_cbsd, high_freq_c) \
                              - max(low_freq_cbsd-10000000.0, low_freq_c)
    overlap_bw_outside_10MHz = min(low_freq_cbsd-10000000.0, high_freq_c) \
                               - max(3530000000.0, low_freq_c)
    overlap_bw_below_3530MHz = min(3530000000.0, high_freq_c) \
                               - low_freq_c

    # Compute total conducted power
    power_within_10MHz_mW = 0
    power_outside_10MHz_mW = 0
    power_below_3530MHz_mW = 0
    if overlap_bw_within_10MHz > 0:
        power_within_10MHz_mW = 10 ** (OOB_POWER_WITHIN_10MHZ / 10.) \
                                * overlap_bw_within_10MHz / 1000000.0

    if overlap_bw_outside_10MHz > 0:
        power_outside_10MHz_mW = 10 ** (OOB_POWER_OUTSIDE_10MHZ / 10.) \
                                 * overlap_bw_outside_10MHz / 1000000.0

    if overlap_bw_below_3530MHz > 0:
        power_below_3530MHz_mW = 10 ** (OOB_POWER_BELOW_3530MHZ / 10.) \
                                 * overlap_bw_below_3530MHz / 1000000.0

    power_mW = power_within_10MHz_mW + power_outside_10MHz_mW + power_below_3530MHz_mW

    return 10 * np.log10(power_mW)


def computeInterference(cbsd_grant, constraint, h_inc_ant, num_iteration, dpa_type):

    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.

    Inputs:
        cbsd_grant:     a namedtuple of type CBSDGrant
        constraint: 	protection constraint of type ProtectionConstraint
        h_inc_ant:      reference incumbent antenna height (in meters)
        num_iteration:  a number of Monte Carlo iterations
        dpa_type:       an enum member of class DpaType

    Returns:
        interference: 	interference contribution, a tuple with named fields
                        'grantIndex', 'medianInterference', 'randomInterference'
                        (K random interference contributions of the grant to
                        protection constraint c), and 'bearing_c_cbsd'
                        (bearing from c to CBSD grant location).
    """

    # Get CBSD grant information
    grant_index = cbsd_grant.grantIndex
    lat_cbsd = cbsd_grant.latitude
    lon_cbsd = cbsd_grant.longitude
    h_cbsd = cbsd_grant.height
    indoor_cbsd = cbsd_grant.indoorDeployment
    ant_beamwidth_cbsd = cbsd_grant.antennaBeamwidth
    ant_gain_cbsd = cbsd_grant.antennaGain
    ant_az_cbsd = cbsd_grant.antennaAzimuth
    maxEirpPerMHz_cbsd = cbsd_grant.maxEirp
    low_freq_cbsd = cbsd_grant.lowFrequency
    high_freq_cbsd = cbsd_grant.highFrequency

    # Get protection constraint information (protection point and frequency range)
    lat_c = constraint.latitude
    lon_c = constraint.longitude
    low_freq_c = constraint.lowFrequency
    high_freq_c = constraint.highFrequency

    # Compute median and K random realizations of path loss/interference contribution
    # based on ITM model as defined in [R2-SGN-03] (in dB)
    reliabilities = np.random.uniform(0.001, 0.999, num_iteration)  # get K random
                # reliability values from an uniform distribution over [0.001,0.999)
    reliabilities = np.append(reliabilities, [0.5])  # add 0.5 (for median loss) as
                                            # a last value to reliabilities array
    results = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=reliabilities,
                                            freq_mhz=FREQ_PROP_MODEL)
    path_loss = np.array(results.db_loss)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                               ant_az_cbsd, ant_beamwidth_cbsd,
                                               ant_gain_cbsd)

    # Compute EIRP of CBSD grant inside the frequency range of protection constraint
    if dpa_type is not DpaType.OUT_OF_BAND: # For co-channel offshore/inland DPAs

        # CBSD co-channel bandwidth overlapping with
        # frequency range of protection constraint
        co_channel_bw = min(high_freq_cbsd, high_freq_c) - max(low_freq_cbsd, low_freq_c)

        # Compute EIRP within co-channel bandwidth
        eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain \
                    + 10 * np.log10(co_channel_bw / 1000000.0)

        # Overlapping bandwidth between the first 10 MHz adjacent-channel of CBSD grant and
        # the frequency range of protection constraint
        adj_channel_bw = min(10000000.0, high_freq_c - low_freq_c - co_channel_bw)

        # Incorporate EIRP within the adjacent-bandwidth into the total EIRP
        if adj_channel_bw != 0:

            # Compute EIRP within the adjancent-bandwidth
            eirp_adj_channel_bw = OOB_POWER_WITHIN_10MHZ + ant_gain \
                                   + 10 * np.log10(adj_channel_bw / 1000000.0)

            # Compute total EIRP
            eirp_cbsd = 10 * np.log10(10**(eirp_cbsd/10.) + 10**(eirp_adj_channel_bw/10.))

    else:   # For out-of-band inland DPAs

        # Compute out-of-band conducted power
        oob_power = ComputeOOBConductedPower(low_freq_cbsd, low_freq_c, high_freq_c)

        # Compute out-of-band EIRP
        eirp_cbsd = oob_power + ant_gain

    # Calculate the interference contributions
    interf = eirp_cbsd - path_loss
    median_interf = interf[-1]      # last element is the median interference
    K_interf = interf[:-1]          # first 'K' interference

    # Store interference contributions
    interference = InterferenceContribution(grantIndex=grant_index,
                                            medianInterference=median_interf,
                                            randomInterference=K_interf,
                                            bearing_c_cbsd=results.incidence_angles.hor_rx)
    return interference


def formInterferenceMatrix(cbsd_grant_list, constraint, h_inc_ant, num_iter, dpa_type):

    """
    Form the matrix of interference contributions to protection constraint c.

    Inputs:
        cbsd_grant_list:    a list of CBSD grants, each one being a namedtuple of type CBSDGrant,
                            of all CBSDs inside the neighborhood of the protection constraint.
        constraint:         protection constraint of type ProtectionConstraint
        h_inc_ant:          reference incumbent antenna height (in meters)
        num_iter:           number of random iterations
        dpa_type:           an enum member of class DpaType

    Returns:
        I:                  a matrix of interference contributions to protection
                            constraint (c) with dimensions (num_iter x len(cbsd_grant_list))
        sorted_grant_indices: a list of indices of the sorted grant list
        sorted_bearings:    a list of bearings from protection point to CBSDs of the
                            sorted grant list
    """

    # Compute interference contributions of each grant to the protection constraint
    interf_list = []
    for cbsd_grant in cbsd_grant_list:
        interf = computeInterference(cbsd_grant, constraint, h_inc_ant, num_iter, dpa_type)
        interf_list.append(interf)

    # Sort grants by their median interference contribution, smallest to largest
    interf_list.sort(key=attrgetter('medianInterference'))

    # Get indices, bearings, interference contributions of the sorted grants
    sorted_grant_indices = [interf.grantIndex for interf in interf_list]
    sorted_bearings = [interf.bearing_c_cbsd for interf in interf_list]
    I = np.array([interf.randomInterference for interf in interf_list]).transpose()

    return I, sorted_grant_indices, sorted_bearings


def find_nc(I, bearings, t, beamwidth):

    """
    Return the index (nc) of the grant in the ordered list of grants such that
    the protection percentile of the interference from the first nc grants is below the
    threshold for all azimuths of the receiver antenna.

    Inputs:
        I:      2D array of interference contributions (dBm/10 MHz); columns
                correspond to grants, and rows correspond to Monte Carlo iterations
        bearings: a list of bearings from protection point to CBSDs
        t:      protection percentile threshold (dBm/10 MHz)
        beamwidth: protection antenna beamwidth (degree)

    Returns:
        nc:     index nc that defines the move list to be {G_nc+1, G_nc+2, ..., G_Nc}
    """

    # Create array of incumbent antenna azimuth angles (degrees).
    if beamwidth == 360.0:
        azimuths = [0]
    else:
        azimuths = np.arange(0.0, 360.0, beamwidth/2.0)

    # Initialize nc to Nc.
    Nc = I.shape[1]
    nc = Nc

    # Convert protection threshold and interference matrix to linear units.
    t_mW = np.power(10.0, t/10.0)
    I_mW = np.power(10.0, I/10.0)

    # Loop through every azimuth angle.
    for azi in azimuths:

        # Calculate interference contributions at output of receiver antenna.
        if beamwidth == 360.0:
            dpa_gains = 0
        else:
            dpa_gains = antenna.GetRadarNormalizedAntennaGains(bearings, azi)
        IG = I_mW * 10**(dpa_gains/10.0)

        # Compute the protection percentile of the aggregate interference, and remove
        # grants until the protection threshold is met or all grants are moved.
        agg_interf = np.percentile(np.sum(IG[:, 0:nc], axis=1), PROTECTION_PERCENTILE, interpolation='lower')

        if agg_interf <= t_mW:
            continue

        # Conduct binary search for nc.
        hi = nc
        lo = 0
        while (hi - lo) > 1:
            mid = (hi + lo) / 2
            agg_interf = np.percentile(np.sum(IG[:, 0:mid], axis=1), PROTECTION_PERCENTILE, interpolation='lower')
            if agg_interf > t_mW:
                hi = mid
            else:
                lo = mid

        nc = lo
        if nc == 0:
            return 0

    return nc


def moveListConstraint(protectionPoint, lowFreq, highFreq, registrationReq,
                       grantReq, grantInd, exclusionZone, dpaType, hIncAnt,
                       numIter, threshold, beamwidth):
    """
    Return the move list for a given protection constraint.

    Inputs:
        protectionPoint:    latitude and longitude of protection constraint
        lowFreq:            low frequency of protection constraint (Hz)
        highFreq:           high frequency of protection constraint (Hz)
        registrationReq:    a list of CBSD registration requests, each one being
                            a dictionary containing CBSD registration information
        grantReq:           a list of grant requests, each one being a dictionary
                            containing grant information
        grantInd:           indices of grant requests
        exclusionZone:      a polygon object or a list of locations.
                            If it is a list of locations, each one being a tuple
                            with fields 'latitude' and 'longitude'.
        dpaType:            an enum member of class DpaType
        hIncAnt:            reference incumbent antenna height (m)
        numIter:            number of Monte Carlo iterations
        threshold:          protection threshold (dBm/10 MHz)
        beamwidth:          protection antenna beamwidth (degree)

    Returns:                the list of indices of grants on the move list for the
                            given protection constraint
    """

    # Assign values to the protection constraint
    constraint = ProtectionConstraint(latitude=protectionPoint.latitude,
                                      longitude=protectionPoint.longitude,
                                      lowFrequency=lowFreq,
                                      highFrequency=highFreq)

    # Identify Nc CBSD grants in the neighborhood of the protection constraint
    Nc_grants = findGrantsInsideNeighborhood(registrationReq, grantReq, grantInd,
                                             constraint, exclusionZone, dpaType)

    if len(Nc_grants):  # Found CBSDs in the neighborhood

        # Form the matrix of interference contributions
        I, sorted_grant_indices, bearings = formInterferenceMatrix(Nc_grants, constraint,
                                                                hIncAnt, numIter, dpaType)

        # Find the index (nc) of the grant in the ordered list of grants such that
        # the protection percentile of the interference from the first nc grants is below
        # the threshold for all azimuths of the receiver antenna.
        nc = find_nc(I, bearings, threshold, beamwidth)

        # Determine the associated move list (Mc)
        Mc = sorted_grant_indices[nc:]

        return Mc

    else:
        
        return []


def findMoveList(protection_specs, protection_points, registration_requests,
                 grant_requests, num_iter, num_processes, exclusion_zone=None):

    """
    Main routine to find CBSD indices on the move list.

    Inputs:
        protection_specs:   protection specifications, an object with attributes
                            'lowFreq' (in Hz), 'highFreq' (in Hz),
                            'antHeight' (in meters), 'beamwidth' (in degrees),
                            'threshold' (in dBm/10MHz)
        protection_points:  a list of protection points, each one being an object
                            providing attributes 'latitude' and 'longitude'
        registration_requests: a list of CBSD registration requests, each one being
                            a dictionary containing CBSD registration information
        grant_requests:     a list of grant requests, each one being a dictionary
                            containing grant information
        num_iter:           number of Monte Carlo iterations
        num_processes:      number of parallel processes to use
        exclusion_zone:     a polygon object or a list of locations.
                            If it is a list of locations, each one is a tuple
                            with fields 'latitude' and 'longitude'.
                            Default value is 'None'.
    Returns:
        result:             a Boolean list (same size as registration_requests/
                            grant_requests) with TRUE elements at indices having
                            grants on the move list
    """

    # Determine DPA type based on frequency range.
    if protection_specs.lowFreq >= LOW_FREQ_COCH and protection_specs.highFreq <= HIGH_FREQ_COCH:
        dpa_type = DpaType.CO_CHANNEL
    elif protection_specs.highFreq <= LOW_FREQ_COCH:
        dpa_type = DpaType.OUT_OF_BAND
    else:
        raise ValueError('Invalid DPA frequency range')

    # Index the grant requests in the same order in the registration_requests and
    # grant_requests lists, [1, 2,..., N].
    grant_index = range(1, len(registration_requests) + 1)

    # Find the move list of each protection constraint with a pool of parallel processes.
    pool = Pool(processes=min(num_processes, len(protection_points)))
    moveListC = partial(moveListConstraint, lowFreq=protection_specs.lowFreq,
                        highFreq=protection_specs.highFreq,
                        registrationReq=registration_requests, grantReq=grant_requests,
                        grantInd=grant_index, exclusionZone=exclusion_zone,
                        dpaType=dpa_type, hIncAnt=protection_specs.antHeight,
                        numIter=num_iter, threshold=protection_specs.threshold,
                        beamwidth=protection_specs.beamwidth)
    M_c = pool.map(moveListC, protection_points)
    pool.close()
    pool.join()

    # Find the unique CBSD indices in the M_c list of lists.
    M = set().union(*M_c)
    M = np.array(list(M))

    # Set to TRUE the elements of the output Boolean array that have grant_index in
    # the move list.
    result = np.zeros(len(grant_index), bool)
    if M.size:
        result[M - 1] = True

    return result.tolist()



