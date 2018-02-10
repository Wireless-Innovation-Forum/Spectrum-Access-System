#    Copyright 2018 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# ==================================================================================
# Iterative Allocation Process(IAP) Reference Model.
# Based on WINNF-TS-0112, Version V1.3.0-r5.0, 29 January 2018.

# ==================================================================================

import numpy as np
from operator import attrgetter, iadd
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
from shapely.geometry import MultiPolygon as MPolygon
from collections import namedtuple
from multiprocessing import Pool
from functools import partial
from enum import Enum
import sys
sys.path.append('../..')
from util import getFUGPoints, getChannels
import sas_objects
from reference_models.antenna import antenna
from reference_models.antenna import fss_pointing
from reference_models.geo import vincenty
from reference_models.examples import entities
#from reference_models.propagation import wf_itm  ##TODO

# Set constant parameters based on requirements in the WINNF-TS-0112 [R2-SGN-16]
GWPZ_NBRHD_DIST = 40  # neighborhood distance from a CBSD to a given protection point (in km)
# in GWPZ protection area
PPA_NBRHD_DIST = 40  # neighborhood distance from a CBSD to a given protection point (in km)
# in PPA protection area

FSS_CO_CHANNEL_NBRHD_DIST = 150  # neighborhood distance from a CBSD to FSS for co-channel protection

FSS_BLOCKING_NBRHD_DIST = 40  # neighborhood distace from a CBSD to FSS for blocking protection

ESC_NBRHD_DIST_A = 40  # neighborhood distance from a ESC to category A CBSD

ESC_NBRHD_DIST_B = 50  # neighborhood distance from a ESC to category B CBSD

NUM_OF_PROCESSES = 6

# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0

# CBRS Band Frequency Range (Hz)
CBRS_LOW_FREQ = 3550000000.0
CBRS_HIGH_FREQ = 3700000000.0

# FSS Passband low frequency range  (Hz)
FSS_LOW_FREQ = 3600000000.0

# PPA Frequency Range (Hz)
PPA_LOW_FREQ = 3550000000.0
PPA_HIGH_FREQ = 3680000000.0

# ESC IAP for Out-of-Band Categoroy A CBSDs in Frequency Range (Hz)
ESC_CAT_A_LOW_FREQ = 3550000000.0
ESC_CAT_A_HIGH_FREQ = 3660000000.0

# ESC IAP for Out-of-Band Categoroy B CBSDs in Frequency Range (Hz)
ESC_CAT_B_LOW_FREQ = 3550000000.0
ESC_CAT_B_HIGH_FREQ = 3680000000.0

# ESC Channel 21 Center Frequency
ESC_CH21_CF = 3652500000.0

# One Mega Herts
ONE_MHZ = 1000000.0

# Channel bandwidth over which SASs execute the IAP process
IAPBW = 5000000.0

# GWPZ Area Protection reference bandwidth for the IAP process
GWPZ_RBW = 10000000.0

# PPA Area Protection reference bandwidth for the IAP process
PPA_RBW = 10000000.0

# GWPZ and PPA height (m)
GWPZ_PPA_HEIGHT = 1.5

# Number of SASs - NSAS
NUM_SAS = 3

#In-band insertion loss
IN_BAND_INSERTION_LOSS = 0.5

# Grant Index Global counter
grant_index = 1

# Define an enumeration class named ProtectionEntityType with members
# 'GWPZ_AREA', 'PPA_AREA'
class ProtectionEntityType(Enum):
    GWPZ_AREA = 1
    PPA_AREA = 2
    FSS_CO_CHA = 3
    FSS_BLOCKING = 4
    ESC_CAT_A = 5
    ESC_CAT_B = 6


# Define CBSD grant, i.e., a tuple with named fields of 'latitude', 'longitude', 'height',
# 'indoorDeployment', 'antennaAzimuth', 'antennaGain', 'antennaBeamwidth', 'cbsdCategory', 
# 'grantIndex', 'maxEirp', 'maxEirp', 'lowFrequency', 'highFrequency', 'isManagedGrant'
CBSDGrant = namedtuple('CBSDGrant',
                       ['latitude', 'longitude', 'height', 'indoorDeployment',
                        'antennaAzimuth', 'antennaGain', 'antennaBeamwidth',
                        'cbsdCategory', 'grantIndex', 'maxEirp', 'lowFrequency', 
                        'highFrequency','isManagedGrant'])

# Define protection constraint, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'lowFrequency', 'highFrequency'
ProtectionConstraint = namedtuple('ProtectionConstraint',
                                  ['latitude', 'longitude',
                                   'lowFrequency', 'highFrequency', 'entityType'])

# Define Post IAP Grant information, i.e., a tuple with named fields of
# 'eirp', 'interference'
PostIAPGrantInfo = namedtuple('PostIAPGrantInfo',
                          ['eirp', 'interference'])

# Global Post IAP managed grants container
post_iap_managed_grants = {}

# Global common leftover container
common_leftover = {}

# Global IAP Allowed Margin container 
iap_allowed_margin = {}


def findGrantsInsideNeighborhood(cbsdGrantReqs, constraint):
    """
    Identify the Nc CBSD grants in the neighborhood of protection constraint.
    Inputs:
        cbsdGrantReqs:     a list of grant requests
        constraint:        protection constraint of type ProtectionConstraint
    Returns:
        grants_inside:  a list of grants, each one being a namedtuple of type CBSDGrant,
                        of all CBSDs inside the neighborhood of the protection constraint.
    """
    # Initialize an empty list
    grants_inside = []

    # Loop over each CBSD grant
    for grantReq in cbsdGrantReqs:

        # Check CBSD location
        lat_cbsd = grantReq.latitude
        lon_cbsd = grantReq.longitude

        # Compute distance from CBSD location to protection constraint location
        lat_c = constraint.latitude
        lon_c = constraint.longitude
        dist_km, bearing, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd,
                                                               lat_c, lon_c)

        # Check if CBSD is inside the neighborhood of protection constraint
        cbsd_in_nbrhd = False

        if constraint.entityType is ProtectionEntityType.GWPZ_AREA:
            if dist_km <= GWPZ_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.PPA_AREA:
            if dist_km <= PPA_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.FSS_CO_CHA:
            if dist_km <= FSS_CO_CHANNEL_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.FSS_BLOCKING:
            if dist_km <= FSS_BLOCKING_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.ESC_CAT_A:
            if cbsdGrantReqs.cbsdCategory == 'A':
                if dist_km <= ESC_NBRHD_DIST_A:
                    cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.ESC_CAT_B:
            if cbsdGrantReqs.cbsdCategory == 'B':
                if dist_km <= ESC_NBRHD_DIST_B:
                    cbsd_in_nbrhd = True
        else:
             raise ValueError('Unknown protection entity type %s' % constraint.entityType)

        if cbsd_in_nbrhd: 
           # Check frequency range
           low_freq_cbsd = grantReq.lowFrequency
           high_freq_cbsd = grantReq.highFrequency

           low_freq_c = constraint.lowFrequency
           high_freq_c = constraint.highFrequency
           overlapping_bw = min(high_freq_cbsd, high_freq_c) \
                            - max(low_freq_cbsd, low_freq_c)
           freq_check = (overlapping_bw > 0)

           # Return CBSD information if it is inside the neighborhood of protection constraint
           if freq_check:
              grants_inside.append(grantReq)

    return grants_inside


def computeInterference(cbsd_grant, constraint, h_inc_ant, iap_eirp):
    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.
    Inputs:
        cbsd_grant:        a namedtuple of type CBSDGrant
        constraint: 	   protection constraint of type ProtectionConstraint
        h_inc_ant:         reference incumbent antenna height (in meters)
        iap_eirp:          EIRP to be considered for IAP
    Returns:
        interference: 	interference contribution
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
    maxEirpPerMHz_cbsd = iap_eirp
    low_freq_cbsd = cbsd_grant.lowFrequency
    high_freq_cbsd = cbsd_grant.highFrequency

    # Get protection constraint information (protection point and frequency range)
    lat_c = constraint.latitude
    lon_c = constraint.longitude
    low_freq_c = constraint.lowFrequency
    high_freq_c = constraint.highFrequency

    # Compute median and K random realizations of path loss/interference contribution
    # based on ITM model as defined in [R2-SGN-03] (in dB)
    reliabilities = np.random.uniform(0.001, 0.999)  # get K random
    # reliability values from an uniform distribution over [0.001,0.999)
    reliabilities = np.append(reliabilities, [0.5])  # add 0.5 (for median loss) as
    # a last value to reliabilities array
    results = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=reliabilities,
                                            freq_mhz=FREQ_PROP_MODEL)  #TODO --Should this be center freq of the channel ?
    path_loss = np.array(results.db_loss)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                           ant_az_cbsd, ant_beamwidth_cbsd,
                                           ant_gain_cbsd)

    eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain \
                + 10 * np.log10(IAPBW/ONE_MHZ)

    # Calculate the interference contributions
    interference = eirp_cbsd - path_loss

    return interference


def computeInterferenceESC(cbsd_grant, constraint, h_inc_ant, az_inc_ant, iap_eirp):
    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.
    Inputs:
        cbsd_grant:        a namedtuple of type CBSDGrant
        constraint: 	   protection constraint of type ProtectionConstraint
        h_inc_ant:         reference incumbent antenna height (in meters)
        az_inc_ant:        reference incumbent antenna azimuth (in degrees)
        iap_eirp:          EIRP to be considered for IAP
    Returns:
        interference: 	interference contribution
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
    maxEirpPerMHz_cbsd = iap_eirp
    low_freq_cbsd = cbsd_grant.lowFrequency
    high_freq_cbsd = cbsd_grant.highFrequency

    # Get protection constraint information (protection point and frequency range)
    lat_c = constraint.latitude
    lon_c = constraint.longitude
    low_freq_c = constraint.lowFrequency
    high_freq_c = constraint.highFrequency

    # Compute median and K random realizations of path loss/interference contribution
    # based on ITM model as defined in [R2-SGN-03] (in dB)
    reliabilities = np.random.uniform(0.001, 0.999)  # get K random
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

    # Compute ESC antenna gain in the direction of ESC
    pattern = np.arange(360)
    esc_ant_gain = antenna.GetAntennaPatternGains(results.incidence_angles.hor_cbsd,
                                              az_inc_ant, pattern,
                                              ant_gain_esc)

    eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain + esc_ant_gain \
            + 10 * np.log10(IAPBW/ONE_MHZ) - IN_BAND_INSERTION_LOSS

    # Calculate the interference contributions
    interference = eirp_cbsd - path_loss

    return interference


def computeInterferenceFSS(cbsd_grant, constraint, h_inc_ant, fss_entities, iap_eirp):
    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.
    Inputs:
        cbsd_grant:        a namedtuple of type CBSDGrant
        constraint: 	   protection constraint of type ProtectionConstraint
        h_inc_ant:         reference incumbent antenna height (in meters)
        iap_eirp:          EIRP to be considered for IAP
    Returns:
        interference: 	interference contribution
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
    maxEirpPerMHz_cbsd = iap_eirp
    low_freq_cbsd = cbsd_grant.lowFrequency
    high_freq_cbsd = cbsd_grant.highFrequency

    # Get protection constraint information (protection point and frequency range)
    lat_c = constraint.latitude
    lon_c = constraint.longitude
    low_freq_c = constraint.lowFrequency
    high_freq_c = constraint.highFrequency

    # Compute median and K random realizations of path loss/interference contribution
    # based on ITM model as defined in [R2-SGN-03] (in dB)
    reliabilities = np.random.uniform(0.001, 0.999)  # get K random
    # reliability values from an uniform distribution over [0.001,0.999)
    reliabilities = np.append(reliabilities, [0.5])  # add 0.5 (for median loss) as
    # a last value to reliabilities array
    results = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=reliabilities,
                                            freq_mhz=FREQ_PROP_MODEL)
    path_loss = np.array(results.db_loss)
    incidence_angles = np.array(results.incidence_angles)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                               ant_az_cbsd, ant_beamwidth_cbsd,
                                               ant_gain_cbsd)
    # TODO Do we need to consider interference from all the FSS entities
    fss_total_interference = []
    for fss_entity in fss_entities:
        hor_dirs = [inc_angle.hor_rx for inc_angle in incidence_angles]
        ver_dirs = [inc_angle.ver_rx for inc_angle in incidence_angles]

        # Compute FSS antenna gain in the direction of CBSD
        fss_ant_gains = antenna.GetFssAntennaGains(
            hor_dirs, ver_dirs,
            fss_entity.pointing_azimuth,
            fss_entity.pointing_elevation,
            fss_entity.max_gain_dbi)

        # Compute EIRP of CBSD grant inside the frequency range of protection constraint
        eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain + fss_ant_gain \
                    + 10 * np.log10(IAPBW/ONE_MHZ) - IN_BAND_INSERTION_LOSS

        # Calculate the interference contributions
        interference = eirp_cbsd - path_loss
        fss_total_interference.append(interference)

    return fss_total_interference


def computeInterferenceFSSBlocking(cbsd_grant, constraint, h_inc_ant, fss_entities, iap_eirp):
    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.
    Inputs:
        cbsd_grant:        a namedtuple of type CBSDGrant
        constraint: 	   protection constraint of type ProtectionConstraint
        h_inc_ant:         reference incumbent antenna height (in meters)
        iap_eirp:          EIRP to be considered for IAP
    Returns:
        interference: 	interference contribution
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
    maxEirpPerMHz_cbsd = iap_eirp
    low_freq_cbsd = cbsd_grant.lowFrequency
    high_freq_cbsd = cbsd_grant.highFrequency

    # Get protection constraint information (protection point and frequency range)
    lat_c = constraint.latitude
    lon_c = constraint.longitude
    low_freq_c = constraint.lowFrequency
    high_freq_c = constraint.highFrequency

    # Compute median and K random realizations of path loss/interference contribution
    # based on ITM model as defined in [R2-SGN-03] (in dB)
    reliabilities = np.random.uniform(0.001, 0.999)  # get K random
    # reliability values from an uniform distribution over [0.001,0.999)
    reliabilities = np.append(reliabilities, [0.5])  # add 0.5 (for median loss) as
    # a last value to reliabilities array
    results = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=reliabilities,
                                            freq_mhz=FREQ_PROP_MODEL)
    path_loss = np.array(results.db_loss)
    incidence_angles = np.array(results.incidence_angles)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                               ant_az_cbsd, ant_beamwidth_cbsd,
                                               ant_gain_cbsd)
    # TODO Need to update as per James reply
    fss_total_interference = []
    for fss_entity in fss_entities:
        hor_dirs = [inc_angle.hor_rx for inc_angle in incidence_angles]
        ver_dirs = [inc_angle.ver_rx for inc_angle in incidence_angles]

        # Compute FSS antenna gain in the direction of CBSD
        fss_ant_gains = antenna.GetFssAntennaGains(
            hor_dirs, ver_dirs,
            fss_entity.pointing_azimuth,
            fss_entity.pointing_elevation,
            fss_entity.max_gain_dbi)

        # Compute EIRP of CBSD grant inside the frequency range of protection constraint
        eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain + fss_ant_gain \
                    + 10 * np.log10((high_freq_cbsd - low_freq_cbsd) / ONE_MHZ)

        # Get 50MHz offset below the lower edge of the FSS earth station
        offset = low_freq_c - 50000000

        # Get CBSD grant frequency range
        cbsd_freq_range = high_freq_cbsd - low_freq_cbsd

        # if lower edge of the FSS passband is less than CBSD grant
        # lowFrequency and highFrequency
        if low_freq_c < low_freq_cbsd and low_freq_c < high_freq_cbsd:
            fss_mask = 0.5
        # if CBSD grant lowFrequency and highFrequency is less than
        # 50MHz offset from the FSS passband lower edge
        elif low_freq_cbsd < offset and high_freq_cbsd < offset:
            fss_mask = 10 * np.log10((cbsd_freq_range / ONE_MHZ) * 0.25)
        # if CBSD grant lowFrequency is less than 50MHz offset and
        # highFrequency is greater than 50MHz offset
        elif low_freq_cbsd < offset and high_freq_cbsd > offset:
            fss_mask = 10 * np.log10(((offset - low_freq_cbsd) / ONE_MHZ) * 0.25)
            fss_mask = fss_mask + 10 * np.log10(((high_freq_cbsd - offset) / ONE_MHZ) * 0.6)
        # if FSS Passband lower edge frequency is grater than CBSD grant
        # lowFrequency and highFrequency and
        # CBSD grand low and high frequencies are greater than 50MHz offset
        elif low_freq_c > low_freq_cbsd and low_freq_c > high_freq_cbsd and \
                low_freq_cbsd > offset and high_freq_cbsd > offset:
            fss_mask = 10 * np.log10((cbsd_freq_range / ONE_MHZ) * 0.6)

        # Calculate the interference contributions
        interference = eirp_cbsd - fss_mask - path_loss
        fss_total_interference.append(interference)

    return fss_total_interference


def iapAreaConstraint(protectionPoints, channels, lowFreq, highFreq, cbsdGrantReqs, threshold, protection_ent_type):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protectionPoints:     List of protection points inside protection area
        channels:             Channels over which area incumbent needs protection
        lowFreq:              low frequency of protection constraint (Hz)
        highFreq:             high frequency of protection constraint (Hz)
        cbsdGrantReqs:        a list of grant requests, each one being a dictionary
                              containing grant information
        threshold:            protection threshold (dBm/5 MHz)
        protection_ent_type:    Type of the protection entity
    Returns:                  the list of indices of grants on the move list for the
                              given protection constraint
    """
    # Initialize an empty list
    # List of fair share of interference to which grants are entitled for
    # a particular protectionPoint, channel
    fairshare_p_ch = []

    # List of interference quota at a particular protectionpoint, channel
    Q_p_ch = []

    # Number of grants to be considered at a particular protectionpoint, channel
    N_p_ch = []

    # For each point p_i in protectionPoints
    for protectionPoint in protectionPoints:
        # For each channel c_j in channels
        for channel in channels:
            # Set interference quota Q for protectionPoint, channel combination
            Q = threshold

            # Get protection constrain over 5MHz channel range
            chConstraint = ProtectionConstraint(latitude=protectionPoint[0],
                                               longitude=protectionPoint[1],
                                               lowFrequency=channel[0],
                                               highFrequency=channel[1],
                                               entityType=protection_ent_type)

            # Identify Nc CBSD grants in the neighborhood of the protection point and channel
            Nc_grants = findGrantsInsideNeighborhood(cbsdGrantReqs, chConstrain)

            N = len(Nc_grants)
            # calculate the fair share
            FS = Q / N

            fairshare_p_ch.append(FS)
            Q_p_ch.append(Q)
            N_p_ch.append(N)

    # For each point p_i in protectionPoints
    for protectionPoint in protectionPoints:

        # Find all the GAA grants inside 40kms of p_i
        # Assign values to the protection constraint
        constraint = ProtectionConstraint(latitude=protectionPoint[0],
                                          longitude=protectionPoint[1],
                                          lowFrequency=lowFreq,
                                          highFrequency=highFreq,
                                          entityType=protection_ent_type)

        # Identify Na CBSD grants in the neighborhood of the protection constrain
        Na_grants = findGrantsInsideNeighborhood(cbsdGratReqs, constraint)

        num_grants = len(Na_grants)

        if num_grants:  # Number of CBSD grants that fully/partially interfere with protection point p
            # over at least one channel in channels
            # Empty list of final IAP EIRP assigned to the grant
            grantEirp = []
            # Empty list of power assigned indicator for the grant
            grant_powerAssigned = []
            for i, grant in enumerate(Na_grants):
                grant_powerAssigned[i] = False
                grantEirp[i] = grant.maxEirp
                while (True):
                    goodOverAllChannels = True
                    # Compute interference contributions of each grant to the protection constraint
                    # over 5MHz IAP channel
                    interference_list = []
                    # For each channel c_j in channels
                    for i, channel in enumerate(channels):
                        # Get protection constrain over 5MHz channel range
                        ch_constrain = ProtectionConstraint(latitude=protectionPoint[0],
                                                            longitude=protectionPoint[1],
                                                            lowFrequency=channel[0],
                                                            highFrequency=channel[1],
                                                            entityType=protection_ent_type)

                        # Get the fair share for a protection point and channel combination
                        fairshare = fairshare_p_ch[i]

                        # Compute interference grant causes to protection point over channel
                        interference = computeInterference(grant, ch_constraint, 
                                                     GWPZ_PPA_HEIGHT, grantEirp[i])
                        interference_list[i] = interference

                        # calculated interference exceeds fair share of interference to which the grants are entitled
                        if interference > fairshare:
                            goodOverAllChannels = False
                            break

                    if goodOverAllChannels is True:
                        grantPowerassigned[i] = True
                        # For each channel c_j in channels
                        for i, channel in enumerate(channels):
                            # Remove satisfied CBSD grant from consideration
                            Q_p_ch[i] = Q_p_ch[i] - interference_list[i]
                            N_p_ch[i] = N_p_ch[i] - 1
                            # re-calculate fair share
                            fairshare_p_ch[i] = Q_p_chi[i] / N_p_ch[i]

                            # Get protection constrain over 5MHz channel range
                            ch_constrain = ProtectionConstraint(latitude=protectionPoint[0],
                                                            longitude=protectionPoint[1],
                                                            lowFrequency=channel[0],
                                                            highFrequency=channel[1],
                                                            entityType=protection_ent_type)

                            common_leftover[ch_constrain] =  Q_p_ch[i]
                            # Update EIRP and Interference only if managed grant
                            if grant.isManagedGrant:
                               # Nested dictionary - contains dictionary of protection
                               # constraint over which grant extends
                               post_iap_managed_grants[grant.grantIndex] = {}
                               post_iap_grant = PostIAPGrantInfo(eirp=grantEirp[i],
                                                    interference=interference_list[i])
                               post_iap_managed_grants[grant.grantIndex][ch_constrain] = \
										post_iap_grant
                        else:
                            grantEirp[i] = grantEirp[i] - 1

                    if all(i is True for i in grant_powerAssigned):
                        break

        return

# TODO -- Need to update as per pseudo code- but crux of the logic is same as 
# Area protection without considering for loop for protection point
def iapPointConstraint(protectionPoint, channels, lowFreq, highFreq, cbsdGrantReqs,
                       hIncAnt, azIncAnt, fssEntities, threshold, protection_ent_type):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
     protectionPoints:   List of protection points inside protection area
     channels:           Channels over which reference incumbent needs protection
     lowFreq:            low frequency of protection constraint (Hz)
     highFreq:           high frequency of protection constraint (Hz)
     cbsdGrantReqs:           a list of grant requests, each one being a dictionary
                         containing grant information
     hIncAnt:            reference incumbent antenna height (m)
     threshold:          protection threshold (dBm/5 MHz)
     protection_ent_type:  an enum member of class ProtectionEntityType
    Returns:              Updates common_leftover and post_iap_managed_grants
                          global container with leftover margin, power and interference
    """
    # Initialize an empty list
    # List of fair share of interference to which grants are entitled for
    # a particular protectionPoint, channel
    fairshare_p_ch = []

    # List of interference quota at a particular protectionpoint, channel
    Q_p_ch = []

    # Number of grants to be considered at a particular protectionpoint, channel
    N_p_ch = []

    # For each channel c_j in channels
    for channel in channels:

        # Set interference quota Q for protectionPoint, channel combination
        if protection_ent_type is ProtectionEntityType.ESC_CAT_A or\
            protection_ent_type is ProtectionEntityType.ESC_CAT_B:
            if channel[0] >= 3650000000.0:
                center_freq = (channel[0] + channel[1]) / 2
                Q = threshold - (2.5 + ((center_freq - ESC_CH21_CF) / ONE_MHZ))
                iap_allowed_margin['iapQEsc'+`channel`] = Q
        else:
            # FSS Co-channel threshold
            Q = threshold

        # Get protection constrain over 5MHz channel range
        chConstrain = ProtectionConstraint(latitude=protectionPoint[0],\
					longitude=protectionPoint[1],\
					lowFrequency=channel[0],\
					highFrequency=channel[1],\
					entityType=protection_ent_type)

        # Identify Nc CBSD grants in the neighborhood of the protection point and channel
        Nc_grants = findGrantsInsideNeighborhood(cbsdGrantReqs, chConstrain)

        N = len(Nc_grants)

        # calculate the fair share
        FS = Q / N

        fairshare_p_ch.append(FS)
        Q_p_ch.append(Q)
        N_p_ch.append(N)

    # Find all the GAA grants inside neighborhood of p_i
    # Assign values to the protection constraint
    constraint = ProtectionConstraint(latitude=protectionPoint[0],
                                      longitude=protectionPoint[1],
                                      lowFrequency=lowFreq,
                                      highFrequency=highFreq,
                                      entityType=protection_ent_type)

    # Identify Na CBSD grants in the neighborhood of the protection constrain
    Na_grants = findGrantsInsideNeighborhood(cbsdGratReqs, constraint)

    num_grants = len(Na_grants)

    if num_grants:  # Number of CBSD grants that fully/partially interfere with protection point p
       # over at least one channel in channels
       # Empty list of final IAP EIRP assigned to the grant
       grantEirp = []
       # Empty list of power assigned indicator for the grant
       grant_powerAssigned = []
       for i, grant in enumerate(Na_grants):
           grant_powerAssigned[i] = False
           grantEirp[i] = grant.maxEirp
           while (True):
               goodOverAllChannels = True
               # Compute interference contributions of each grant to the protection constraint
               # over 5MHz IAP channel
               interference_list = []
               # For each channel c_j in channels
               for i, channel in enumerate(channels):
                   # Get protection constrain over 5MHz channel range
                   ch_constrain = ProtectionConstraint(latitude=protectionPoint[0],
                                                       longitude=protectionPoint[1],
                                                       lowFrequency=channel[0],
                                                       highFrequency=channel[1],
                                                       entityType=protection_ent_type)

                   # Get the fair share for a protection point and channel combination
                   fairshare = fairshare_p_ch[i]

                   # Compute interference grant causes to protection point over channel
                   if protection_ent_type is ProtectionEntityType.FSS_CO_CHA:
                      fss_interference_list = computeInterferenceFSS(grant, 
                               ch_constraint, hIncAnt, fssEntities, grantEirp[i])
                      interference = sum(fss_interference_list)
                   else:
                       interference = computeInterferenceESC(grant, ch_constraint, hIncAnt,
                                                              azIncAnt, grantEirp[i])

                   interference_list[i] = interference

                   # calculated interference exceeds fair share of 
                   # interference to which the grants are entitled
                   if interference > fairshare:
                      goodOverAllChannels = False
                      break

                   if goodOverAllChannels is True:
                      grantPowerassigned[i] = True
                      # For each channel c_j in channels
                      for i, channel in enumerate(channels):
                          # Remove satisfied CBSD grant from consideration
                          Q_p_ch[i] = Q_p_ch[i] - interference_list[i]
                          N_p_ch[i] = N_p_ch[i] - 1
                          # re-calculate fair share
                          fairshare_p_ch[i] = Q_p_chi[i] / N_p_ch[i]
                          # Get protection constrain over 5MHz channel range
                          ch_constrain = ProtectionConstraint(latitude=protectionPoint[0],
                                                          longitude=protectionPoint[1],
                                                          lowFrequency=channel[0],
                                                          highFrequency=channel[1],
                                                          entityType=protection_ent_type)

                          common_leftover[ch_constrain] =  Q_p_ch[i]
                          # Update EIRP and Interference only if managed grant
                          if grant.isManagedGrant:
                             # Nested dictionary - contains dictionary of protection
                             # constraint over which grant extends
                             post_iap_managed_grants[grant.grantIndex] = {}
                             post_iap_grant = PostIAPGrantInfo(eirp=grantEirp[i],
                                                    interference=interference_list[i])
                             post_iap_managed_grants[grant.grantIndex][ch_constrain] =\
                                                         post_iap_grant
                      else:
                          grantEirp[i] = grantEirp[i] - 1

                   if all(i is True for i in grant_powerAssigned):
                      break

def iapFSSBlockingConstraint(protectionPoint, lowFreq, highFreq, cbsdGrantReqs,
                                     hIncAnt, fssEntities, threshold, protection_ent_type):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protectionPoints:   List of protection points inside protection area
        channels:           Channels over which reference incumbent needs protection
        lowFreq:            low frequency of protection constraint (Hz)
        highFreq:           high frequency of protection constraint (Hz)
        cbsdGrantReqs:           a list of grant requests, each one being a dictionary
                            containing grant information
        hIncAnt:            reference incumbent antenna height (m)
        threshold:          protection threshold (dBm/5 MHz)
        protection_ent_type:  an enum member of class ProtectionEntityType
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint
    """

    # Find all the GAA grants inside 150kms of p_i
    # Assign values to the protection constraint
    constraint = ProtectionConstraint(latitude=protectionPoint[0],
                                      longitude=protectionPoint[1],
                                      lowFrequency=lowFreq,
                                      highFrequency=highFreq,
                                      entityType=protection_ent_type)

    # Identify Na CBSD grants in the neighborhood of the protection constrain
    Na_grants = findGrantsInsideNeighborhood(cbsdGratReqs, constraint)

    num_grants = len(Na_grants)

    # calculate the fair share
    fair_share = threshold / num_grants

    Q = threshold

    if num_grants:  # Number of CBSD grants that fully/partially interfere with protection point p
        # over at least one channel in channels
        # Empty list of final IAP EIRP assigned to the grant
        grantEirp = []
        # Empty list of power assigned indicator for the grant
        grant_powerAssigned = []
        for i, grant in enumerate(Na_grants):
            grant_powerAssigned[i] = False
            grantEirp[i] = grant.maxEirp
            while True:
                # Compute interference contributions of each grant to the protection constraint
                interference_list = []

                # Compute interference grant causes to protection point over
                # band non-overlapping with FSS Passband
                interference = computeInterferenceFSSBlocking(grant, 
                         constraint, hIncAnt, fssEntities, grantEirp[i])
                interference_list[i] = interference

                # calculated interference exceeds fair share of interference to which the grants are entitled
                if interference > fairshare:
                    goodOverAllChannels = False

                if goodOverAllChannels is True:
                    grantPowerassigned[i] = True
                    # Remove satisfied CBSD grant from consideration
                    Q = Q - interference_list[i]
                    num_grants = num_grants - 1
                    # re-calculate fair share
                    fairshare = threshold / num_grants
                    common_leftover[constraint] = Q
                    # Update EIRP and Interference only if managed grant
                    if grant.isManagedGrant:
                       # Nested dictionary - contains dictionary of protection
                       # constraint over which grant extends
                       post_iap_managed_grants[grant.grantIndex] = {}
                       post_iap_grant = PostIAPGrantInfo(eirp=grantEirp[i],
                                          interference=interference_list[i])
                       post_iap_managed_grants[grant.grantIndex][constraint] =\
                                                   post_iap_grant
                else:
                    grantEirp[i] = grantEirp[i] - 1
                    continue

            if all(i is True for i in grant_powerAssigned):
                break

def performIAPforESC(protection_entity, grant_objects, iapQEsc):
    """
     Return the interference margin list for a given protection constraint.
     Inputs:
         protection_entity:  List of protection points inside protection area
         grant_objects:      a list of grant requests, each one being a dictionary
                             containing grant information
         iapQEsc:            Pre IAP threshold value for ESC incumbent type
     Returns:                the list of indices of grants on the move list for the
                             given protection constraint 
     """
    # Get the protection point of the ESC
    esc_point = protection_entity['installationParam']
    protection_point = [(esc_point['latitude'], esc_point['longitude'])]

    # Get ESC Antenna Height
    antenna_height = esc_point['height']

    # Get ESC Antenna Azimuth
    antenna_azimuth = esc_point['antennaAzimuth']

    pool = Pool(processes=min(NUM_OF_PROCESSES, len(protection_point)))

    # ESC Category A CBSDs between 3550 - 3660 MHz within 40 km
    protection_channels = getChannels(ESC_CAT_A_LOW_FREQ, ESC_CAT_A_HIGH_FREQ)

    # ESC algorithm
    partial(iapPointConstraint, protectionPoint=protection_point,
            channels=protection_channels,
            lowFreq=ES_CAT_A_LOW_FREQ,
            highFreq=ESC_CAT_A_HIGH_FREQ,
            cbsdGrantReqs=grant_objects,
            hIncAnt=antenna_height,
            azIncAnt=antenna_azimuth,
            fssEntities=None,
            threshold=iapQEsc,
            protection_ent_type=ProtectionEntityType.ESC_CAT_A)

    # ESC Category B CBSDs between 3550 - 3680 MHz within 80 km
    protection_channels = getChannels(ESC_CAT_B_LOW_FREQ, ESC_CAT_B_HIGH_FREQ)

    partial(iapPointConstraint, protectionPoint=protection_point,
            channels=protection_channels,
            lowFreq=ESC_CAT_B_LOW_FREQ,
            highFreq=ESC_CAT_B_HIGH_FREQ,
            cbsdGrantReqs=grant_objects,
            hIncAnt=antenna_height,
            azIncAnt=antenna_azimuth,
            fssEntities=None,
            threshold=iapQEsc,
            protection_ent_type=ProtectionEntityType.ESC_CAT_B)

    pool.close()
    pool.join()

    return

def performIAPforGWPZ(protection_entity, grant_objects, iapQGwpz):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protection_entity:  List of protection points inside protection area
        grant_objects:      a list of grant requests, each one being a dictionary
                            containing grant information
        iapQGwpz:           Pre IAP threshold value for GWPZ incumbent type
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint 
    """

    # Get Fine Grid Points for a GWPZ protoection area
    protection_points = getFUGPoints(protection_entity)

    gwpz_freqRange = protection_entity['deploymentParam'][0]['operationParam']['operationFrequencyRange']
    gwpz_lowFreq = gwpz_freqRange['lowFrequency']
    gwpz_highFreq = gwpz_freqRange['highFrequency']

    # Get channels over which area incumbent needs partial/full protection
    protection_channels = getChannels(gwpz_lowFreq, gwpz_highFreq)

    # Apply IAP for each protection constraint with a pool of parallel processes.
    pool = Pool(processes=min(NUM_OF_PROCESSES, len(protection_points)))

    partial(iapAreaConstraint, protectionPoints=protection_points,
            channels=protection_channels,
            lowFreq=gwpz_lowFreq,
            highFreq=gwpz_highFreq,
            cbsdGrantReqs=grant_objects,
            threshold=iapQGwpz,
            protection_ent_type=ProtectionEntityType.GWPZ_AREA)

    pool.close()
    pool.join()

    return

def performIAPforPPA(protection_entity, grant_objects, iapQPpa):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protection_entity:  List of protection points inside protection area
        grant_objects:      a list of grant requests, each one being a dictionary
                            containing grant information
        iapQPpa:            Pre IAP threshold value for PPA incumbent type 
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint 
    """

    # Get Fine Grid Points for a PPA protoection area
    protection_points = getFUGPoints(protection_entity)


   #TODO -- PAL -- freq range -
    # Get channels over which area incumbent needs partial/full protection
    protection_channels = getChannels(PPA_LOW_FREQ, PPA_HIGH_FREQ)

    # Apply IAP for each protection constraint with a pool of parallel processes.
    pool = Pool(processes=min(NUM_OF_PROCESSES, len(protection_points)))

    partial(iapAreaConstraint, protectionPoints=protection_points,
            channels=protection_channels,
            lowFreq=PPA_LOW_FREQ,
            highFreq=PPA_HIGH_FREQ,
            cbsdGrantReqs=grant_objects,
            threshold=iapQPpa,
            protection_ent_type=ProtectionEntityType.PPA_AREA)

    pool.close()
    pool.join()

    return

def performIAPforFSS(protection_entity, grant_objects, iapQCochannel, iapQBlocking):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protection_entity:  List of protection points inside protection area
        grant_objects:      a list of grant requests, each one being a dictionary
                            containing grant information
        iapQCochannel:      Pre IAP threshold value for FSS co-channel incumbent type
        iapQBlocking:       Pre IAP threshold value for FSS Blocking incumbent type
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint 
    """

    # Get FSS T&C Flag value
    fss_ttc_flag = protection_entity['deploymentParam'][0]['ttc_flag']

    # Get the protection point of the FSS
    fss_point = protection_entity['deploymentParam'][0]['installationParam']
    protection_point = [(fss_point['latitude'], fss_point['longitude'])]

    # Get FSS Antenna Height
    antenna_height = fss_point['height']
   
    # Get FSS Antenna Gain
    antenna_gain = fss_point['antennaGain']

    # Get the frequency range of the FSS
    fss_freqRange = protection_entity['deploymentParam'][0]['operationParam']['operationFrequencyRange']
    fss_lowFreq = fss_freqRange['lowFrequency']
    fss_highFreq = fss_freqRange['highFrequency']

    # TODO -- How to pass satellite info ? 
    # Protect the following FSS near Kansas City defined here:
    #    http://licensing.fcc.gov/myibfs/displayLicense.do?filingKey=-205179
    fss_info = entities.FssLicenseInfo(latitude=protection_point[0],
                                       longitude=protection_point[1],
                                       height_agl=antenna_height,
                                       max_gain_dbi=antenna_gain,
                                       satellite_arc_east_limit=-60,
                                       satellite_arc_west_limit=-143,
                                       elevation_east_limit=32.8,
                                       elevation_west_limit=22.9,
                                       azimuth_east_limit=132.6,
                                       azimuth_west_limit=241.2)

    # Get all the FSS "protection points".
    fss_entities = fss_pointing.GetAllFssFromLicenseInfo(fss_info)

    pool = Pool(processes=min(NUM_OF_PROCESSES, len(protection_point)))

    # FSS Passband is between 3600 and 4200
    if (fss_lowFreq >= FSS_LOW_FREQ and fss_lowFreq < CBRS_HIGH_FREQ):
        # Get channels for co-channel CBSDs
        protection_channels = getChannels(fss_lowFreq, CBRS_HIGH_FREQ)

        # FSS Co-channel algorithm
        partial(iapPointConstraint, protectionPoint=protection_point,
                channels=protection_channels,
                lowFreq=fss_lowFreq,
                highFreq=CBRS_HIGH_FREQ,
                cbsdGrantReqs=grant_objects,
                hIncAnt=antenna_height,
                azIncAnt=None,
                fssEntities=fss_entities,
                threshold=iapQCochannel,
                protection_ent_type=ProtectionEntityType.FSS_CO_CHA)

        # 5MHz channelization is not required for Blocking protection
        # FSS in-band blocking algorithm
        partial(iapFSSBlockingConstraint, protectionPoints=protection_point,
                lowFreq=CBRS_LOW_FREQ,
                highFreq=fss_lowFreq,
                cbsdGrantReqs=grant_objects,
                hIncAnt=antenna_height,
                fssEntities=fss_entities,
                QBlocking=iapQBlocking,
                protection_ent_type=ProtectionEntityType.FSS_BLOCKING)


    # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
    elif (fss_lowFreq >= 3700 and fss_highFreq <= 4200) and (fss_ttc_flag == True):
        # 5MHz channelization is not required for Blocking protection
        # FSS TT&C Blocking Algorithm
        partial(iapFSSBlockingConstraint, protectionPoints=protection_point,
                lowFreq=CBRS_LOW_FREQ,
                highFreq=fss_lowFreq,
                cbsdGrantReqs=grant_objects,
                hIncAnt=antenna_height,
                fssEntities=fss_entities,
                QBlocking=iapQBlocking,
                protection_ent_type=ProtectionEntityType.FSS_BLOCKING)

    elif (fss_lowFreq >= 3700 and fss_highFreq <= 4200) and (fss_ttc_flag == False):
        print 'IAP for FSS not applied for FSS Pass band 3700 to 4200 and TT&C flag set to false'

    pool.close()
    pool.join()

    return

def calculateIAPQ(protection_thresholds, pre_iap_headRooms):
    """
   Routine to calculate interference margin for each 5MHz channel
   Inputs:
       protection_threhsold: protection threshold of the protected entity
       headrooms:            headroom for the protected entity 
       protection_ent_type:  protected entity type
   Returns:
       allowed_margin:       allowed interference margin of the protected entity 
   """

    for key, Q in protection_thresholds.iteritems():
        if key is 'QPpa':
           iap_allowed_margin['iapQPpa'] = Q + 10 * \
               np.log10(IAPBW/PPA_RBW) - pre_iap_headRooms.get('MgPpa')
        elif key is 'QGwpz':
             iap_allowed_margin['iapQGwpz'] = Q + 10 * \
                np.log10(IAPBW/GWPZ_RBW) - pre_iap_headRooms.get('MgGwpz')
        elif key is 'QCochannel':
             iap_allowed_margin['iapQCochannel'] = Q + 10 * \
               np.log10(IAPBW/ONE_MHZ) - pre_iap_headRooms.get('MgCochannel') 
        elif key is 'QBlocking':
            iap_allowed_margin['iapQBlocking'] = \
                       Q - pre_iap_headRooms.get('MgBlocking')
        elif key is 'QEsc':
             iap_allowed_margin['iapQEsc'] = Q + 10 * \
                np.log10(IAPBW/ONE_MHZ) - pre_iap_headRooms.get('MgEsc') 

       
def getGrantFromCBSDDump(cbsd_dump,is_managing_sas):
    """
    Routine to extract CBSDGrant tuple from CBSD dump from FAD object
    Inputs:
        cbsd_dump:         cbsd dump extracted from FAD record 
        is_managing_sas:   flag indicating cbsd dump is from managing SAS or peer SAS
                           True - Managing SAS, False - Peer SAS
    Returns:
        grant_objects:     List of CBSD grant objects 
    """
    
    cbsd_objects = len(cbsd_dump)

    grants_objects = []
    # Loop over each CBSD grant
    for i in range(cbsd_objects):
        cbsd_record = cbsd_dump[i].get('recordData')
        registration = cbsd_record[0].get('registration')
        grants = cbsd_record[0].get('grants')

        # Check CBSD location
        lon_cbsd = registration.get('installationParam', {}).get('longitude')
        height_cbsd = registration.get('installationParam', {}).get('height')
        height_type_cbsd = registration.get('installationParam', {}).get('heightType')
        if height_type_cbsd == 'AMSL':
            altitude_cbsd = terrainDriver.GetTerrainElevation(lat_cbsd, lon_cbsd)
            height_cbsd = height_cbsd - altitude_cbsd

        # Sanity check on CBSD antenna height
        if height_cbsd < 1 or height_cbsd > 1000:
            raise ValueError('CBSD height is less than 1 m or greater than 1000 m.')
        
        for grant in grants:
           # Return CBSD information
           cbsd_grant = CBSDGrant(
                # Get information from the registration
                latitude=registration.get('installationParam', {}).get('latitude'),
                longitude=registration.get('installationParam', {}).get('longitude'),
                height=height_cbsd,
                indoorDeployment=registration.get('installationParam',{}).get('indoorDeployment'),
                antennaAzimuth=registration.get('installationParam',{}).get('antennaAzimuth'),
                antennaGain=registration.get('installationParam',{}).get('antennaGain'),
                antennaBeamwidth=registration.get('installationParam',{}).get('antennaBeamwidth'),
                cbsdCategory=registration.get('cbsdCategory'),
                grantIndex=grant_index+1,
                # Get information from the grant
                maxEirp=grant.get('operationParam',{}).get('maxEirp'),
                lowFrequency=grant.get('operationParam', {}). \
                       get('operationFrequencyRange', {}).get('lowFrequency'),
                highFrequency=grant.get('operationParam', {}). \
                       get('operationFrequencyRange', {}).get('highFrequency'),
                isManagedGrant=is_managing_sas)
           grants_objects.append(cbsd_grant)

    return grants_objects


def calculate_AP_IAP_Ref():
    """
    Routine to calculate calculate interference from all the CBSDs managed 
    by the SAS at protected entity
    Inputs:
        post_iap_managed_grants: Global container to store EIRP and Interference 
                                 of a grant over all the protection point, channel
        common_leftover:         Global container too store common_leftover interference 
                                 margin for all the protection point, channel
    Returns:
        AP_IAP_Ref:              a dictionary containing AP_IAP_Ref for
                                 protection point, channel
    """
    
    AP_IAP_Ref = {}

    for p_ch_key, Q_p_ch in common_leftover.iteritems():
        A_SAS_P = 0
        # Calculate A_SAS_P - Aggregate interference calculated using the 
        # EIRP obtained by all CBSDs through application of IAP for protected
        # entity p. Only grants managed by SAS UUT are considered  
        for grant_id, grant_info in post_iap_managed_grants.iteritems():
            for grant_protection_constraint, grant_params in grant_info.iteritems():
                if p_ch_key == grant_protection_constraint:
                   #Aggregate interference if grant in inside protection constraint
                   A_SAS_P =  A_SAS_P +  grant_params.interference
        # Calculate AP_IAP_Ref for a particular protection point, channel
        if p_ch_key.entityType == ProtectionEntityType.ESC_CAT_A or \
           p_ch_key.entityType == ProtectionEntityType.ESC_CAT_B:
           low_freq = p_ch_key.lowFrequency
           high_freq = p_ch_key.highFrequency
           if low_freq >= 3650000000.0:
              channel = (high_freq - CBRS_LOW_FREQ )/ IAPBW
              iapQ = iap_allowed_margin['iapQEsc'+`channel`]
        elif p_ch_key.entityType == ProtectionEntityType.GWPZ_AREA: 
              iapQ = iap_allowed_margin['iapQGwpz']
        elif p_ch_key.entityType == ProtectionEntityType.PPA_AREA: 
              iapQ = iap_allowed_margin['iapQPpa']
        elif p_ch_key.entityType == ProtectionEntityType.FSS_CO_CHA: 
              iapQ = iap_allowed_margin['iapQCochannel']
        elif p_ch_key.entityType == ProtectionEntityType.FSS_BLOCKING: 
              iapQ = iap_allowed_margin['iapQBlocking']
        # iapQ -- pre IAP margin
        AP_IAP_Ref[p_ch_key] =  (iapQ/NUM_SAS) + (Q_p_ch/ NUM_SAS) + 10 * np.log10(10**(A_SAS_P/10))



def performIAP(protection_thresholds, pre_iap_headRooms, protection_entities,
                   sas_uut_fad_object, sas_th_fad_objects):
    """
    Main routine to apply IAP to all existing and pending grants.
    Inputs:
        protection_thresholds : a list of protection thresholds per IAPBW(dbm/IAPBW)
                               for protection entities
        pre_iap_headRooms :      a list of per IAP headroom for protection entities
        protection_entities:    a list of protection entities, a list of FSS and GWPZ records
        fadObjects:            a list of FAD objects from SAS UUT and SAS Test Harness
    Returns:
        result:                a list of post IAP margin for all the protected entities p
    """

    # Calculate protection threshold per IAPBW
    calculateIAPQ(protection_thresholds, pre_iap_headRooms)

    # List of CBSD grant tuples extract from FAD record 
    grant_objects = []
    tot_fad_th = len(sas_th_fad_objects)

    # Extract CBSD dump from SAS UUT FAD object
    #cbsd_dump = self.sas_uut_fad_object.get_cbsds() 
    cbsd_dump_uut = sas_uut_fad_object[0]   #testing purpose
    
    # Extract CBSD Grant objects from CBSD dump from Managing SAS  
    grant_objects = getGrantFromCBSDDump(cbsd_dump_uut,True)

    # Extract CBSD dump from SAS Test Harness FAD objects
    for i in range (0,tot_fad_th):
        sas_th_fad_object = sas_th_fad_objects[i]
        #cbsd_dump_sasTH = self.sas_th_fad_object.get_cbsds()
        cbsd_dump_sasTH = sas_th_fad_object[0]
        # Extract CBSD Grant objects from CBSD dump from Managing SAS  
        grant_objects_sasTH = getGrantFromCBSDDump(cbsd_dump_sasTH,False)
        grant_objects.append(grant_objects_sasTH)
    
    # Extract PPA protection entity information from SAS UUT FAD object
    #ppa_protection_entities = self.sas_uut_fad_object.get_ppas()
    ppa_protection_entities = sas_uut_fad_object[1]  #testing purpose
    
    # Extract PPA protection entity information from SAS TH FAD objects
    for i in range (0,tot_fad_th):
        sas_th_fad_object = sas_th_fad_objects[i]
        #ppa_entities_sasTH = self.sas_th_fad_objects.get_ppas()
        ppa_entities_sasTH = sas_th_fad_object[1]
        ppa_protection_entities.append(ppa_entities_sasTH)

    # Extract ESC protection entity information from SAS UUT FAD object
    #esc_protection_entities = self.sas_uut_fad_object.get_esc_sensors()
    esc_protection_entities = sas_uut_fad_object[2]  #testing purpose

    # Extract ESC protection entity information from SAS TH FAD objects
    for i in range (0,tot_fad_th):
        sas_th_fad_object = sas_th_fad_objects[i]
        #esc_entities_sasTH = self.sas_th_fad_objects.get_esc_sensors()
        esc_entities_sasTH = sas_th_fad_object[2]
        esc_protection_entities.append(esc_entities_sasTH)

    for protection_entity in protection_entities:
        if 'type' in protection_entity :
            if protection_entity['type'] == 'FSS':
               performIAPforFSS(protection_entity, grant_objects, \
	   			iap_allowed_margin['iapQCochannel'], \
				iap_allowed_margin['iapQBlocking'])
        elif protection_entity['record']['type'] == 'PART_90':
             performIAPforGWPZ(protection_entity, grant_objects, \
                             iap_allowed_margin['iapQGwpz'])

    for ppa_entity in ppa_protection_entities:
        performIAPforPPA(ppa_entity, grant_objects, \
                         iap_allowed_margin['iapQPpa'])
    for esc_entity in esc_protection_entities:
        performIAPforESC(esc_entity, grant_objects, \
                         iap_allowed_margin['iapQEsc'])
    
     # List of Aggregate interference from all the CBSDs managed by 
     # the SAS at the protected entity 
    AP_IAP_Ref = {}

    AP_IAP_Ref = calculate_AP_IAP_Ref()

    return AP_IAP_Ref
