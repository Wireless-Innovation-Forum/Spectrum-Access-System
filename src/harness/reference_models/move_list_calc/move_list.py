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
# Based on WINNF-TS-0112, Version V1.3.0, 27 September 2017.

# The main routine is 'move_list.findMoveList()'.
#==================================================================================

import numpy as np
from operator import attrgetter
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
from collections import namedtuple

# Import WINNF reference models including propagation, geo, and CBSD antenna gain models
from reference_models.propagation import wf_itm
from reference_models.geo import terrain
from reference_models.geo import vincenty
from reference_models.antenna import antenna

# Initialize terrain driver
terrainDriver = terrain.TerrainDriver()

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

# Reference incumbent radar's antenna height (in meters) [R2-IPM-04]
REF_INC_ANTENNA_HT_COCH_OFFSHORE = 50   # co-channel offshore DPA
REF_INC_ANTENNA_HT_COCH_INLAND = 10     # co-channel inland DPA
REF_INC_ANTENNA_HT_OOB_INLAND = 5       # out-of-band inland DPA

# Reference incumbent radar's antenna rotation step size beginning
# with the main beam boresight at true north (in degrees) [R2-IPM-04]
REF_INC_ANTENNA_ROT_STEP_SIZE = 1.5

# Frequency range of co-channel offshore DPAs (Hz)
LOW_FREQ_COCH_OFFSHORE = 3550000000
HIGH_FREQ_COCH_OFFSHORE = 3650000000

# Frequency range of co-channel inland DPAs (Hz)
LOW_FREQ_COCH_INLAND = 3650000000
HIGH_FREQ_COCH_INLAND = 3700000000

# Upper frequency of out-of-band inland DPAs (Hz)
HIGH_FREQ_OOB_INLAND = 3500000000

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


def findGrantsInsideNeighborhood(reg_request, grant_request, grant_index, constraint,
                                 exclusion_zone, dpa_type):

    """
    Identify the Nc CBSD grants in the neighborhood of protection constraint.

    Inputs:
        reg_request:    a list of CBSD registration requests
        grant_request:  a list of grant requests
        grant_index:    an array of grant indices
        constraint:     protection constraint, a tuple with named fields of
                        'latitude', 'longitude', 'lowFrequency', 'highFrequency'
        exclusion_zone: a polygon object or a list of locations.
                        If it is a list of locations, each one being a tuple
                        with fields 'latitude' and 'longitude'.
                        Default value is 'None'.
        dpa_type:       DPA type, i.e., 'co-channel offshore',
                        'co-channel inland', or 'out-of-band inland'

    Returns:
        grants_inside:  a list of grants, each one being a tuple with named fields including
                        installation and grant information, of all
                        CBSDs inside the neighborhood of the protection constraint.
    """

    # Initialize an empty list
    grants_inside = []

    # For co-channel offshore/inland DPAs, make sure exclusion zone is a polygon
    if dpa_type != 'out-of-band inland':
        if isinstance(exclusion_zone, SPolygon):
            polygon_ex_zone = exclusion_zone
        else:
            polygon_ex_zone = SPolygon(exclusion_zone)

    # Loop over each CBSD grant
    for i in range(len(reg_request)):

        # Check CBSD location
        cbsd_cat = reg_request[i].get('cbsdCategory')
        lat_cbsd = reg_request[i].get('installationParam', {}).get('latitude')
        lon_cbsd = reg_request[i].get('installationParam', {}).get('longitude')
        height_cbsd = reg_request[i].get('installationParam', {}).get('height')
        height_type_cbsd = reg_request[i].get('installationParam', {}).get('heightType')
        if height_type_cbsd == 'AMSL':
            altitude_cbsd = terrainDriver.GetTerrainElevation(lat_cbsd, lon_cbsd)
            height_cbsd = height_cbsd - altitude_cbsd

        lat_c = constraint.latitude
        lon_c = constraint.longitude
        dist_km, bearing, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd,
                                                               lat_c, lon_c)
        cbsd_in_nbrhd = False
        if cbsd_cat == 'A':
            if dpa_type != 'out-of-band inland':
                point_cbsd = SPoint(lat_cbsd, lon_cbsd)
                if dist_km <= CAT_A_NBRHD_DIST and polygon_ex_zone.contains(point_cbsd):
                    cbsd_in_nbrhd = True
        elif cbsd_cat == 'B':
            if dpa_type != 'out-of-band inland':
                if dist_km <= CAT_B_NBRHD_DIST:
                    cbsd_in_nbrhd = True
                elif dist_km <= CAT_B_NBRHD_DIST_FOR_HT:
                    height_cbsd_haat = wf_itm.ComputeHaat(lat_cbsd, lon_cbsd, height_cbsd,
                                                          height_is_agl=(height_type_cbsd != 'AMSL'))
                    if height_cbsd_haat >= CAT_B_LONG_HT:
                        cbsd_in_nbrhd = True
            else:
                if dist_km <= CAT_B_NBRHD_DIST_OOB:
                    cbsd_in_nbrhd = True
        else:
            raise ValueError('Unknown category %s' % cbsd_cat)

        # Check frequency range
        low_freq_cbsd = grant_request[i].get('operationParam', {}). \
            get('operationFrequencyRange', {}).get('lowFrequency')
        high_freq_cbsd = grant_request[i].get('operationParam', {}). \
            get('operationFrequencyRange', {}).get('highFrequency')
        if dpa_type != 'out-of-band inland':
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
                indoorDeployment=reg_request[i].get('installationParam',{}).get('indoorDeployment'),
                antennaAzimuth=reg_request[i].get('installationParam',{}).get('antennaAzimuth'),
                antennaGain=reg_request[i].get('installationParam',{}).get('antennaGain'),
                antennaBeamwidth=reg_request[i].get('installationParam',{}).get('antennaBeamwidth'),
                # Get information from the grant request
                grantIndex=grant_index[i],
                maxEirp=grant_request[i].get('operationParam',{}).get('maxEirp'),
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
        power_within_10MHz = OOB_POWER_WITHIN_10MHZ \
                             + 10 * np.log10(overlap_bw_within_10MHz / 1000000.0)
        power_within_10MHz_mW = np.power(10.0, power_within_10MHz/10.0)
    if overlap_bw_outside_10MHz > 0:
        power_outside_10MHz = OOB_POWER_OUTSIDE_10MHZ \
                              + 10 * np.log10(overlap_bw_outside_10MHz / 1000000.0)
        power_outside_10MHz_mW = np.power(10.0, power_outside_10MHz/10.0)
    if overlap_bw_below_3530MHz > 0:
        power_below_3530MHz = OOB_POWER_BELOW_3530MHZ \
                              + 10 * np.log10(overlap_bw_below_3530MHz / 1000000.0)
        power_below_3530MHz_mW = np.power(10.0, power_below_3530MHz/10.0)

    power_mW = power_within_10MHz_mW + power_outside_10MHz_mW + power_below_3530MHz_mW

    return 10 * np.log10(power_mW)

def computeInterference(cbsd_grant, constraint, h_inc_ant, num_iteration, dpa_type):

    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.

    Inputs:
        cbsd_grant:     a tuple with named fields including installation and
                        grant information of the CBSD
        constraint: 	protection constraint, a tuple with named fields of
                        'latitude', 'longitude', 'lowFrequency', 'highFrequency'
        h_inc_ant:      reference incumbent antenna height (in meters)
        num_iteration:  a number of Monte Carlo iterations
        dpa_type:       DPA type, i.e., 'co-channel offshore',
                        'co-channel inland', or 'out-of-band inland'

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

    # Compute EIRP of CBSD grant inside the frequency range of protection constraint
    if dpa_type != 'out-of-band inland': # For co-channel offshore/inland DPAs

        # CBSD co-channel bandwidth overlapping with
        # frequency range of protection constraint
        co_channel_bw = min(high_freq_cbsd, high_freq_c) - max(low_freq_cbsd, low_freq_c)

        # Overlapping bandwidth between the first 10 MHz of CBSD grant adjacent-channel and
        # the frequency range of protection constraint
        adj_channel_bw = min(10000000.0, high_freq_c - low_freq_c - co_channel_bw)

        if adj_channel_bw == 0:    # Consider only co-channel bandwidth
            eirpPerMHz_cbsd = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                                              ant_az_cbsd, ant_beamwidth_cbsd,
                                                              maxEirpPerMHz_cbsd)
            eirp_cbsd = eirpPerMHz_cbsd + 10 * np.log10(co_channel_bw / 1000000.0)

        else:   # Consider both co-channel bandwidth and first 10 MHz adjacent-bandwidth
            # Compute CBSD antenna gain in the direction of protection point
            ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                                       ant_az_cbsd, ant_beamwidth_cbsd,
                                                       ant_gain_cbsd)

            # Compute conducted CBSD power within co-channel bandwidth
            power_co_channel_bw = (maxEirpPerMHz_cbsd - ant_gain_cbsd) \
                                   + 10 * np.log10(co_channel_bw / 1000000.0)

            # Compute conducted CBSD power within adjacent-channel bandwidth
            power_adj_channel_bw = OOB_POWER_WITHIN_10MHZ \
                                   + 10 * np.log10(adj_channel_bw / 1000000.0)

            # Compute total EIRP
            power_cbsd_mW = np.power(10.0, power_co_channel_bw / 10.0)\
                            + np.power(10.0, power_adj_channel_bw / 10.0)
            eirp_cbsd = 10 * np.log10(power_cbsd_mW) + ant_gain

    else:   # For out-of-band inland DPAs
        # Compute CBSD antenna gain in the direction of protection point
        ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                                   ant_az_cbsd, ant_beamwidth_cbsd,
                                                   ant_gain_cbsd)

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
        cbsd_grant_list:    a list of CBSD grants, each one being a tuple with named fields 
                            including installation and grant information, of all
                            CBSDs inside the neighborhood of the protection constraint.
        constraint:         protection constraint, a tuple with named fields of
                            'latitude', 'longitude', 'lowFrequency', 'highFrequency'
        h_inc_ant:          reference incumbent antenna height (in meters)
        num_iter:           number of random iterations
        dpa_type:           DPA type, i.e., 'co-channel offshore',
                            'co-channel inland', or 'out-of-band inland'

    Returns:
        I:                  a matrix of interference contributions to protection
                            constraint (c) with dimensions (num_iter x len(cbsd_grant_list))
        sorted_grant_index: a list of indices of the sorted grant list
        sorted_bearing:     a list of bearings from protection point to CBSDs of the
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
    sorted_grant_index = [interf.grantIndex for interf in interf_list]
    sorted_bearing = [interf.bearing_c_cbsd for interf in interf_list]
    I = np.array([interf.randomInterference for interf in interf_list]).transpose()

    return I, sorted_grant_index, sorted_bearing


def find_nc(I, bearings, t):

    """
    Return the index (nc) of the grant in the ordered list of grants such that
    the protection percentile of the interference from the first nc grants is below the
    threshold for all azimuths of the receiver antenna.

    Inputs:
        I:      2D array of interference contributions (dBm); columns
                correspond to grants, and rows correspond to Monte Carlo iterations
        bearings: a list of bearings from protection point to CBSDs
        t:      protection percentile threshold (dBm)

    Returns:
        nc:     index nc that defines the move list to be {G_nc+1, G_nc+2, ..., G_Nc}
    """

    # Create array of incumbent antenna azimuth angles (degrees).
    azimuths = np.arange(0.0, 360.0, REF_INC_ANTENNA_ROT_STEP_SIZE)

    # Initialize nc to Nc.
    Nc = I.shape[1]
    nc = Nc

    # Convert protection threshold and interference matrix to linear units.
    t_mW = np.power(10.0, t/10.0)
    I_mW = np.power(10.0, I/10.0)

    # Loop through every azimuth angle.
    for azi in azimuths:
        # Calculate interference contributions at output of receiver antenna.
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

def findMoveList(dpa_type, protection_points, low_freq, high_freq, threshold, num_iter,
                 registration_request, grant_request, exclusion_zone=None):

    """
    Main routine to find CBSD indices on the move list.

    Inputs:
        dpa_type:           DPA type, i.e., 'co-channel offshore',
                            'co-channel inland', or 'out-of-band inland'
        protection_points:  a list of protection points, each one being a tuple with
                            named fields of 'latitude' and 'longitude'
        low_freq:           low frequency of protection constraint (Hz)
        high_freq:          high frequency of protection constraint (Hz)
        threshold:          protection threshold (dBm/10 MHz)
        num_iter:           number of Monte Carlo iterations
        registration_request: a list of CBSD registration requests, each one being
                            a dictionary containing CBSD registration information
        grant_request:      a list of grant requests, each one being a dictionary
                            containing grant information
        exclusion_zone:     a polygon object or a list of locations.
                            If it is a list of locations, each one being a tuple
                            with fields 'latitude' and 'longitude'.
                            Default value is 'None'.

    Returns:
        result:             a Boolean array (same size as registration_request/
                            grant_request) with TRUE elements at indices having
                            grants on the move list
    """

    # Check consistency of DPA type against frequency range.
    # If correct, get reference incumbent antenna height above sea/ground level
    if dpa_type == 'co-channel offshore':
        if low_freq>=LOW_FREQ_COCH_OFFSHORE and high_freq<=HIGH_FREQ_COCH_OFFSHORE:
            h_inc_ant = REF_INC_ANTENNA_HT_COCH_OFFSHORE
        else:
            raise ValueError('Inconsistency between DPA type %s and frequency range [%s,%s]'
                             % (dpa_type, low_freq, high_freq))
    elif dpa_type == 'co-channel inland':
        if low_freq>=LOW_FREQ_COCH_INLAND and high_freq<=HIGH_FREQ_COCH_INLAND:
            h_inc_ant = REF_INC_ANTENNA_HT_COCH_INLAND
        else:
            raise ValueError('Inconsistency between DPA type %s and frequency range [%s,%s]'
                             % (dpa_type, low_freq, high_freq))
    elif dpa_type == 'out-of-band inland':
        if high_freq<=HIGH_FREQ_OOB_INLAND:
            h_inc_ant = REF_INC_ANTENNA_HT_OOB_INLAND
        else:
            raise ValueError('Inconsistency between DPA type %s and frequency range [%s,%s]'
                             % (dpa_type, low_freq, high_freq))
    else:
        raise ValueError('Unknown DPA type %s. Valid type: co-channel offshore, '
                         'co-channel inland, out-of-band inland.' % dpa_type)

    # Index the grant requests in the same order in the registration_request and
    # grant_request lists [1, 2,..., N].
    grant_index = range(1, len(registration_request) + 1)

    # Loop over each protection point and find the move list
    M_temp = []

    for point in protection_points:

        Mc = []         # Initialize move list for current protection constraint c

        # Assign values to the protection constraint
        constraint = ProtectionConstraint(latitude=point.latitude,
                                          longitude=point.longitude,
                                          lowFrequency=low_freq,
                                          highFrequency=high_freq)

        # Identify Nc CBSD grants in the neighborhood of protection constraint c
        Nc_grants = findGrantsInsideNeighborhood(registration_request, grant_request,
                                                 grant_index, constraint, exclusion_zone, dpa_type)

        if len(Nc_grants):  # Found CBSDs in the neighborhood

            # Form the matrix of interference contributions
            I, sorted_grant_index, bearing = formInterferenceMatrix(Nc_grants, constraint,
                                                                    h_inc_ant, num_iter, dpa_type)

            # Find the index (nc) of the grant in the ordered list of grants such that
            # the protection percentile of the interference from the first nc grants is below
            # the threshold for all azimuths of the receiver antenna.
            nc = find_nc(I, bearing, threshold)

            # Determine the associated move list (Mc)
            Mc = sorted_grant_index[nc:]

            # Add Mc to M_temp list
            M_temp = M_temp + Mc

    # Find unique CBSD index in the M_temp list
    M = np.unique(M_temp)

    # Set to TRUE the elements of the output Boolean array that have grant_index in
    # the move list
    result = np.zeros(len(grant_index), bool)
    if M.size:
        result[M - 1] = True

    return result.tolist()



