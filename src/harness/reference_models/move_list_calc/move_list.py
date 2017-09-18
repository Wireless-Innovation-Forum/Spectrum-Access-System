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
# Based on WINNF-TS-0112, Version V1.2.0-r5.6, 17 August 2017.
# This version of the code only addresses 'co-channel' frequency range protection
# in R2-SGN-24.

# The main routine is 'move_list.findMoveList()'
#==================================================================================

import numpy as np
from operator import itemgetter
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon

# Import WINNF reference models including propagation, geo, and CBSD antenna gain models
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.antenna_gain import cbsd_antenna_gain

# Set constant parameters based on requirements in the WINNNF-TS-0112
CAT_A_NBRHD_DIST = 150          # neighborhood distance for Cat-A CBSD (in km) [R2-SGN-24]
CAT_B_NBRHD_DIST = 200          # neighborhood distance for Cat-B CBSD (in km) [R2-SGN-24]
CAT_B_NBRHD_DIST_FOR_HT = 300   # neighborhood distance for Cat-B CBSD (in km) in
                                # consideration of antenna height [R2-SGN-24]
CAT_B_LONG_HT = 200             # height of Cat_B CBSD (in meters) in consideration of
                                # neighborhood distance Cat_B_NBRHD_DIST_FOR_HT [R2-SGN-24]
PROTECTION_PERCENTILE = 95      # Monte Carlo percentile for protection [R2-SGN-24]

REF_INC_ANTENNA_HT = 50         # reference radar's antenna height (in meters) [R2-IPM-04]
RADAR_BEAMWIDTH = 3.0           # reference radar's attenna beamwidth (in degrees)
                                # [R2-IPM-04]
INTRF_ATTEN_OUTSIDE_MAIN_BEAM = -25.0   # attenuation of interference for CBSD outsides of
                                        # radar main beam [R2-IPM-04]
BLDG_CLUTTER_LOSS = 15          # attenuation due to building loss to be added to indoor CBSD
                                # (in dB) [R2-SGN-03]

def haat(lat, lon, ht):

    """
    Convert height above ground level (AGL) to height above average terrain (HAAT) height.
    TO BE PROVIDED. Just return 'ht' for now.
    """

    return ht

def findGrantsInsideNeighborhood(reg_request, grant_request, grant_index, constraint,
                                 exclusion_zone):

    """
    Identify the Nc CBSD grants in the neighborhood of protection constraint (c).

    Inputs:
        reg_request:    a list of CBSD registration requests
        grant_request:  a list of grant requests
        grant_index:    an array contains index of grant
        constraint:     protection constraint c = (p, f)
        exclusion_zone: a list of locations used to form the exclusion zone

    Returns:
        grant_inside:   a dictionary contains installation and grant information of all
                        CBSDs inside the neighborhood of the protection constraint.
    """

    grants_inside = []
    polygon_ez = SPolygon(exclusion_zone)  # create polygon of the exclusion zone

    # Loop over each CBSD grant
    for i in range(len(reg_request)):

        # Check CBSD location
        cbsd_cat = reg_request[i].get('cbsdCategory')
        lat_cbsd = reg_request[i].get('installationParam', {}).get('latitude')
        lon_cbsd = reg_request[i].get('installationParam', {}).get('longitude')
        height_cbsd = reg_request[i].get('installationParam', {}).get('height')
                      # assume AGL height (in m)
        lat_c = constraint['latitude']
        lon_c = constraint['longitude']
        dist_km, bearing, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd,
                                                               lat_c, lon_c)
        flag_geo = False
        if cbsd_cat == 'A':
            point_cbsd = SPoint(lat_cbsd, lon_cbsd)  # create point
            if dist_km <= CAT_A_NBRHD_DIST and polygon_ez.contains(point_cbsd):
                flag_geo = True
        elif cbsd_cat == 'B':
            if dist_km <= CAT_B_NBRHD_DIST:
                flag_geo = True
            elif (dist_km <= CAT_B_NBRHD_DIST_FOR_HT) and \
                    (haat(lat_cbsd, lon_cbsd, height_cbsd) >= CAT_B_LONG_HT):
                flag_geo = True
        else:  # unknown category, include this CBSD in the neighborhood
            flag_geo = True

        # Check frequency range
        low_freq_cbsd = grant_request[i].get('operationParam', {}).\
            get('operationFrequencyRange', {}).get('lowFrequency')
        high_freq_cbsd = grant_request[i].get('operationParam', {}).\
            get('operationFrequencyRange', {}).get('highFrequency')
        low_freq_c = constraint['lowFrequency']
        high_freq_c = constraint['highFrequency']
        overlapping_bw = min(high_freq_cbsd, high_freq_c) - max(low_freq_cbsd, low_freq_c)
        flag_freq = (overlapping_bw > 0)

        # Return CBSD information if it is inside the neighborhood of protection constraint
        if (flag_geo == True) and (flag_freq == True):
            cbsd_grant = {
                # Get information from the registration request
                'latitude': lat_cbsd,
                'longitude': lon_cbsd,
                'height': height_cbsd,
                'indoorDeployment': reg_request[i].get('installationParam', {}).
                    get('indoorDeployment'),
                'antennaAzimuth': reg_request[i].get('installationParam', {}).
                    get('antennaAzimuth'),
                'antennaGain': reg_request[i].get('installationParam', {}).
                    get('antennaGain'),
                'antennaBeamwidth': reg_request[i].get('installationParam', {}).
                    get('antennaBeamwidth'),
                # Get information from the grant request
                'grantIndex': grant_index[i],
                'maxEirp': grant_request[i].get('operationParam', {}).get('maxEirp'),
                'lowFrequency': low_freq_cbsd,
                'highFrequency': high_freq_cbsd}
            grants_inside.append(cbsd_grant)

    return grants_inside


def computeInterference(cbsd_grant, c, K):

    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.

    Inputs:
        cbsd_grant:     a dictionary contains installation and grant information of the CBSD
        c: 				a dictionary contains information of the protection constraint
                        c = (p, f)
        K: 				number of Monte Carlo iterations

    Returns:
        interference: 	a dictionary contains CBSD index, median interference contribution,
                        K random interference contributions of the grant to the protection
                        constraint c, and bearing from c to CBSD location.
    """

    # Get CBSD grant information 	
    grant_index = cbsd_grant.get('grantIndex')
    lat_cbsd = cbsd_grant.get('latitude')
    lon_cbsd = cbsd_grant.get('longitude')
    h_cbsd = cbsd_grant.get('height')
    indoor_cbsd = cbsd_grant.get('indoorDeployment')
    # ant_gain_cbsd = cbsd_grant.get('antennaGain')     # unused
    ant_beamwidth_cbsd = cbsd_grant.get('antennaBeamwidth')
    ant_az_cbsd = cbsd_grant.get('antennaAzimuth')
    maxEirp_cbsd = cbsd_grant.get('maxEirp')
    low_freq_cbsd = cbsd_grant.get('lowFrequency')
    high_freq_cbsd = cbsd_grant.get('highFrequency')

    # Get protection constraint information (protection point and frequency range)
    lat_c = c.get('latitude')
    lon_c = c.get('longitude')
    low_freq_c = c.get('lowFrequency')
    high_freq_c = c.get('highFrequency')
    h_c = REF_INC_ANTENNA_HT

    # Compute CBSD conducted EIRP within the frequency range ch
    if (ant_beamwidth_cbsd is None) or (ant_az_cbsd is None): # use maxEirp for CBSD EIRP
        eirp_cbsd = maxEirp_cbsd
    else:  # compute CBSD antenna gain ratio in the direction of the protection point p,
           # and subtract it from maxEirp
        _, bearing, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd, lat_c, lon_c)
        ant_gain_ratio = cbsd_antenna_gain.GetCBSDAntennaGain(bearing, ant_az_cbsd,
                                                              ant_beamwidth_cbsd)
        eirp_cbsd = maxEirp_cbsd + ant_gain_ratio

    # Consider only CBSD transmitted power inside the frequency range of
    # protection constraint
    eff_bandwidth = min(high_freq_cbsd, high_freq_c) - max(low_freq_cbsd, low_freq_c)
    FDR = 10 * np.log10((high_freq_cbsd-low_freq_cbsd) / eff_bandwidth)
    eirp_cbsd = eirp_cbsd - FDR

    # Compute median and K random realizations of path loss/interference contribution
    # based on ITM model as defined in [R2-SGN-03] (in dB)
    center_freq_mhz = (low_freq_c + (high_freq_c - low_freq_c) / 2.0) / 1000000.0
    reliabilities = np.random.rand(K)       # get K random reliability values from a
                                            # uniform distribution over [0,1)
    reliabilities = np.append(reliabilities, [0.5])  # add 0.5 (for median loss) as
                                            # a last value to reliabilities array
    results = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd, lat_c, lon_c, h_c,
                                            reliability=reliabilities,
                                            freq_mhz=center_freq_mhz)
    path_loss = np.array(results.db_loss)
    # If the CBSD is indoors, account for attenuation due to building loss [R2-SGN-03]
    if indoor_cbsd:
        path_loss += BLDG_CLUTTER_LOSS

    # Calculate the interference contributions
    interf = eirp_cbsd - path_loss
    median_interf = interf[-1]      # last element is the median interference
    K_interf = interf[:-1]          # first 'K' interference

    # Compute bearing from protection constraint c to the CBSD for later usage
    _, bearing_c_cbsd, _ = vincenty.GeodesicDistanceBearing(lat_c, lon_c, lat_cbsd,
                                                            lon_cbsd)

    # Store interference contributions		
    interference = {
        'grantIndex': grant_index,
        'medianInterference': median_interf,
        'randomInterference': K_interf,
        'bearing_c_cbsd': bearing_c_cbsd}

    return interference


def formInterferenceMatrix(cbsd_grant_list, constraint, num_iter):

    """
    Form the matrix of interference contributions to protection constraint c.

    Inputs:
        cbsd_grant_list:    a list contains cbsd grants
        constraint:         a dictionary contains information of protection constraint (c)
        num_iter:           number of random iterations

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
        interf = computeInterference(cbsd_grant, constraint, num_iter)
        interf_list.append(interf)

    # Sort grants by their median interference contribution, smallest to largest
    interf_list.sort(key=itemgetter('medianInterference'))

    # Get indices, bearings, interference contributions of the sorted grants
    sorted_grant_index = [i.get('grantIndex') for i in interf_list]
    sorted_bearing = [i.get('bearing_c_cbsd') for i in interf_list]
    I = np.array([i.get('randomInterference') for i in interf_list]).transpose()

    return I, sorted_grant_index, sorted_bearing


def grantsInMainBeam(ant_az, bearing):

    """
    Identify the grants in the main beam of the receiver antenna.

    Inputs:
        ant_az:     antenna azimuth (degrees)
        bearing:    a list of bearing values (due north) from the protection point
                    to the CBSDs

    Returns:
        an array contains index of CBSD inside the main beam
    """

    idx = []

    # Compute off-axis angle between the axis of the main-beam of the incumbent
    # receiver and the line between the protection point and each CBSD
    for i in range(len(bearing)):
        theta = ant_az - bearing[i]
        if theta > 180:
            theta -= 360
        elif theta < -180:
           theta += 360

        # Check if the CBSD is inside or outside the antenna main-beam
        if (theta >= (-1) * RADAR_BEAMWIDTH/2.0) and (theta <= RADAR_BEAMWIDTH/2.0):
            idx.append(i)

    return np.array(idx)	


def find_nc(I, bearing, t):

    """
    Return the index (nc) of the grant in the ordered list of grants such that
    the 95th percentile of the interference from the first nc grants is below the
    threshold for all azimuths of the receiver antenna.

    Inputs:
        I:      2D array of interference contributions (dBm/10 MHz); columns
                correspond to grants, and rows correspond to Monte Carlo iterations
        t:      95th-percentile protection threshold (dBm/10 MHz)

    Returns:
        nc:     index nc that defines the move list to be {G_nc+1, G_nc+2, ..., G_Nc}
    """

    # Create array of incumbent antenna azimuth angles (degrees).
    azimuths = np.arange(0.0, 360.0, RADAR_BEAMWIDTH/2.0)

    # Initialize nc to Nc.
    Nc = I.shape[1]
    nc = Nc

    # Convert protection threshold, interference matrix, and antenna
    # discrimination to linear units.
    t_mW = np.power(10.0, t/10.0)
    I_mW = np.power(10.0, I/10.0)
    G_discrim = np.power(10.0, INTRF_ATTEN_OUTSIDE_MAIN_BEAM/10.0)

    # Loop through every azimuth angle.
    for a in azimuths:
        # Calculate interference contributions at output of receiver antenna.
        G = np.full((1,Nc),G_discrim)

        idx = grantsInMainBeam(a,bearing)
        if idx.size:
            G[:,idx] = 1.0
        IG = I_mW*G

        # Compute the 95th percentile of the aggregate interference, and remove
        # grants until the protection threshold is met or all grants are moved.
        A95 = np.percentile(IG.sum(1), PROTECTION_PERCENTILE, interpolation='lower')
        while (A95 > t_mW):
            I_mW[:, nc - 1] = 0.0  # zero-out the nc-th column of I_mW
            IG[:, nc - 1] = 0.0    # zero-out the nc-th column of IG
            nc = nc - 1
            if nc == 0:
                return 0
            A95 = np.percentile(IG.sum(1), PROTECTION_PERCENTILE, interpolation='lower')

    return nc


def findMoveList(protection_points, low_freq, high_freq, threshold, num_iter,
                 registration_request, grant_request, exclusion_zone):

    """
    Main routine to find CBSD indices on the move-list.

    Inputs:
        protection_points:  a list of protection points
        low_freq:           low frequency
        high_freq:          high frequency
        threshold:          protection threshold
        registration_request: a list of CBSD registration requests
        grant_request:      a list of grant requests
        exclusion_zone:     a list of locations used to form the exclusion zone

    Returns:
        result:             a Boolean array (same size as the registration_request/
                            grant_request) with TRUE elements at indices having
                            CBSDs on the move-list
    """

    # Index the grant requests in the same order in the registration_request and
    # grant_request lists [1, 2,..., N].
    grant_index = range(1, len(registration_request) + 1)

    # Loop over each protection point and find the move-list
    M_temp = []
    for p in range(len(protection_points)):

        Mc = []         # Initialize move-list for current protection constraint c

        # Define protection constraint c = (p, f)
        c = {
            'latitude': protection_points[p].get('latitude'),
            'longitude': protection_points[p].get('longitude'),
            'lowFrequency': low_freq,
            'highFrequency': high_freq}

        # Identify Nc CBSD grants in the neighborhood of protection constraint c
        Nc_grants = findGrantsInsideNeighborhood(registration_request, grant_request,
                                                 grant_index, c, exclusion_zone)

        if len(Nc_grants):  # Found CBSDs in the neighborhood

            # Form the matrix of interference contributions
            I, sorted_grant_index, bearing = formInterferenceMatrix(Nc_grants, c,
                                                                    num_iter)

            # Find the index (nc) of the grant in the ordered list of grants such that
            # the 95th percentile of the interference from the first nc grants is below
            # the threshold for all azimuths of the receiver antenna.
            nc = find_nc(I, bearing, threshold)

            # Determine the associated move-list (Mc)
            Mc = sorted_grant_index[nc:]

            # Add Mc to M_temp list
            M_temp = M_temp + Mc

    # Find unique CBSD index in the M_temp list
    M = np.unique(M_temp)

    # Set to TRUE the elements of the output Boolean array that have grant_index in
    # the move-list
    result = np.zeros(len(grant_index), bool)
    if M.size:
        result[M - 1] = True

    return result.tolist()



