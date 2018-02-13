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

from reference_models.examples import entities, example_fss_interference
from reference_models.iap import util
from reference_models.iap import compute


# Global aggrigate interference container
aggregate_interference = {}

# Calculate aggregate interference per area constraint


def aggrAreaConstraint(
    protectionPoints, channels, lowFreq, highFreq, cbsdGrantReqs,
        protection_ent_type):
    """
    Updates global container aggregate_interference with aggregate interference for protection point, channel
    Inputs:
     protectionPoints:   List of protection points inside protection area
     channels:           Channels over which reference incumbent needs protection
     lowFreq:            low frequency of protection constraint (Hz)
     highFreq:           high frequency of protection constraint (Hz)
     cbsdGrantReqs:      a list of grant requests, each one being a dictionary
                         containing grant information
     hIncAnt:            reference incumbent antenna height (m)
     protection_ent_type:  an enum member of class ProtectionEntityType
    Returns:             Updates global container aggregate_interference with aggregate interference for protection point, channel

    """
    aggregate_interference_point_channel = []
    # For each point p_i in protectionPoints
    for protectionPoint in protectionPoints:
        # Get protection constrain over 5MHz channel range
        constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                               longitude=protectionPoint[1],
                                               lowFrequency=lowFreq,
                                               highFrequency=highFreq,
                                               entityType=protection_ent_type)
        # Identify Na CBSD grants in the neighborhood of the protection point
        # and channel
        Na_grants = util.findGrantsInsideNeighborhood(
            cbsdGrantReqs, constraint)

        # For each channel in channels
        for channel in channels:
            # Get protection constrain over 5MHz channel range
            ch_constraint = util.ProtectionConstraint(
                latitude=protectionPoint[0],
                longitude=protectionPoint[1],
                lowFrequency=channel[0],
                highFrequency=channel[1],
                entityType=protection_ent_type)

            cbsd_interference_list = []
            for i, grant in enumerate(Na_grants):
                cbsd_interference = compute.computeInterference(
                    grant, ch_constraint, util.GWPZ_PPA_HEIGHT, grant.maxEirp)
                cbsd_interference_list.append(cbsd_interference)
            aggregate_interference[ch_constraint] = sum(cbsd_interference_list)


# Calculate aggregate interference per protection point
def aggrPointConstraint(
    protectionPoint, channels, lowFreq, highFreq, cbsdGrantReqs,
        hIncAnt, azIncAnt, fssEntities, protection_ent_type):
    """
     Updates global container aggregate_interference with aggregate interference for protection point, channel
    Inputs:
     protectionPoints:   List of protection points inside protection area
     channels:           Channels over which reference incumbent needs protection
     lowFreq:            low frequency of protection constraint (Hz)
     highFreq:           high frequency of protection constraint (Hz)
     cbsdGrantReqs:      a list of grant requests, each one being a dictionary
                         containing grant information
     hIncAnt:            reference incumbent antenna height (m)
     protection_ent_type:  an enum member of class ProtectionEntityType
    Returns:              Updates global container aggregate_interference with aggregate interference for protection point, channel

    """
    aggregate_interference_point_channel = []
    # For each channel in channels
    for channel in channels:

        # Get protection constrain over 5MHz channel range
        constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                               longitude=protectionPoint[1],
                                               lowFrequency=lowFreq,
                                               highFrequency=highFreq,
                                               entityType=protection_ent_type)

        # Identify Na CBSD grants in the neighborhood of the protection point
        # and channel
        Na_grants = util.findGrantsInsideNeighborhood(
            cbsdGrantReqs, constraint)
        cbsd_interference_list = []
        for i, grant in enumerate(Na_grants):
            # Compute interference grant causes to protection point over
            # channel
            if protection_ent_type is util.ProtectionEntityType.FSS_CO_CHA:
                cbsd_interference = compute.computeInterferenceFSS(grant,
                                                                   constraint, hIncAnt, fssEntities, grant.maxEirp)
            else:
                cbsd_interference = compute.computeInterferenceESC(
                    grant, constraint, hIncAnt, azIncAnt, grant.maxEirp, fssEntities)
            cbsd_interference_list.append(cbsd_interference)
        # Get protection constrain over 5MHz channel range
        ch_constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                                  longitude=protectionPoint[1],
                                                  lowFrequency=channel[0],
                                                  highFrequency=channel[1],
                                                  entityType=protection_ent_type)
        aggregate_interference[ch_constraint] = sum(cbsd_interference_list)


def aggrFSSBlockingConstraint(
    protectionPoint, lowFreq, highFreq, cbsdGrantReqs, hIncAnt,
        fss_entities, protection_ent_type):
    """
     Updates global container aggregate_interference with aggregate interference for protection point, channel
    Inputs:
        protectionPoints:   List of protection points inside protection area
        channels:           Channels over which reference incumbent needs protection
        lowFreq:            low frequency of protection constraint (Hz)
        highFreq:           high frequency of protection constraint (Hz)
        cbsdGrantReqs:           a list of grant requests, each one being a dictionary
                            containing grant information
        hIncAnt:            reference incumbent antenna height (m)
                            given protection constraint
        protection_ent_type:  an enum member of class ProtectionEntityType
    Returns:              Updates global container aggregate_interference with aggregate interference for protection point, channel

    """

    # Find all the GAA grants inside 150kms
    # Assign values to the protection constraint
    constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                           longitude=protectionPoint[1],
                                           lowFrequency=lowFreq,
                                           highFrequency=highFreq,
                                           entityType=protection_ent_type)

    # Identify Na CBSD grants in the neighborhood of the protection constrain
    Na_grants = util.findGrantsInsideNeighborhood(cbsdGrantReqs, constraint)
    cbsd_interference_list = []
    for i, grant in enumerate(Na_grants):
        cbsd_interference = compute.computeInterferenceFSSBlocking(
            grant, constraint, hIncAnt, fssEntities, grant.maxEirp)
        cbsd_interference_list.append(cbsd_interference)
    aggregate_interference[constraint] = sum(cbsd_interference_list)


def calculateAggregateInterferenceForFSS(fss, cbsd_list):
    """
    Calculates aggregate interference to FSS.
    Inputs:
        fss : FSS protection entity
        cbsd_list: list of CBSD objects
    Returns:
        result: aggregate interference to FSS in the dictionary format {(latitude, longitude, lowFrequency,highFrequency,entityType): aggregateinterference, .......}

    """

    cbsd_grant_reqs = util.getGrantsFromCbsdObjects(cbsd_list)
    # Get FSS T&C Flag value
    fss_ttc_flag = fss['deploymentParam'][0]['ttc_flag']
    # Get the protection point of the FSS
    fss_point = fss['deploymentParam'][0]['installationParam']
    protection_point = [fss_point['latitude'], fss_point['longitude']]
    # Get FSS Antenna Height
    fss_height_agl = fss_point['height']

    # Get FSS Antenna Gain
    fss_max_antenna_gain = fss_point['antennaGain']

    # Get the frequency range of the FSS
    fss_freqRange = fss['deploymentParam'][0][
        'operationParam']['operationFrequencyRange']
    fss_lowFreq = fss_freqRange['lowFrequency']
    fss_highFreq = fss_freqRange['highFrequency']
    # TODO -- Details on elevation and arc parameters are to clarified
    fss_info = entities.FssLicenseInfo(latitude=protection_point[0],
                                       longitude=protection_point[1],
                                       height_agl=fss_height_agl,
                                       max_gain_dbi=fss_max_antenna_gain,
                                       satellite_arc_east_limit=-60,
                                       satellite_arc_west_limit=-143,
                                       elevation_east_limit=32.8,
                                       elevation_west_limit=22.9,
                                       azimuth_east_limit=132.6,
                                       azimuth_west_limit=241.2)

    # Get all the FSS "protection points".
    fss_entities = example_fss_interference.GetAllFssFromLicenseInfo(fss_info)

    # FSS Passband is between 3600 and 4200
    if (fss_lowFreq >= util.FSS_LOW_FREQ and fss_lowFreq < util.CBRS_HIGH_FREQ):
        # Get channels for co-channel CBSDs
        protection_channels = util.getChannels(
            fss_lowFreq, util.CBRS_HIGH_FREQ)
        aggrPointConstraint(
            protection_point, protection_channels, fss_lowFreq, util.CBRS_HIGH_FREQ,
            cbsd_grant_reqs, fss_height_agl, None, fss_entities, util.ProtectionEntityType.FSS_CO_CHA)
        # 5MHz channelization is not required for Blocking protection
        # FSS in-band blocking algorithm
        aggrFSSBlockingConstraint(
            protection_point, util.CBRS_LOW_FREQ, fss_lowFreq, cbsd_grant_reqs, fss_height_agl,
            fss_entities, util.ProtectionEntityType.FSS_BLOCKING)
    # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
    elif (fss_lowFreq >= 3700 and fss_highFreq <= 4200) and (fss_ttc_flag == True):
        # 5MHz channelization is not required for Blocking protection
        # FSS TT&C Blocking Algorithm
        aggrFSSBlockingConstraint(
            protection_point, util.CBRS_LOW_FREQ, fss_lowFreq, cbsd_grant_reqs, fss_height_agl,
            fss_entities, util.ProtectionEntityType.FSS_BLOCKING)
    elif (fss_lowFreq >= 3700 and fss_highFreq <= 4200) and (fss_ttc_flag == False):
        print 'Aggregate nterference not calculated for FSS Pass band 3700 to 4200 and TT&C flag set to false'
    return aggregate_interference


def calculateAggregateInterferenceForESC(esc, cbsd_list):
    """
    Calculates aggregate interference to ESC.
    Inputs:
        esc : esc protection entity
        cbsd_list: list of CBSD objects
    Returns:
        result: aggregate interference to ESC in the dictionary format {(latitude, longitude, lowFrequency,highFrequency,entityType): aggregateinterference, .......}

    """

    cbsd_grant_reqs = util.getGrantsFromCbsdObjects(cbsd_list)

    # Get the protection point of the ESC
    esc_point = esc['installationParam']
    protection_point = [esc_point['latitude'], esc_point['longitude']]

    # Get ESC Antenna Height
    antenna_height = esc_point['height']

    # Get ESC Antenna Azimuth
    antenna_azimuth = esc_point['antennaAzimuth']

    # ESC Category A CBSDs between 3550 - 3660 MHz within 40 km
    protection_channels = util.getChannels(
        util.ESC_CAT_A_LOW_FREQ, util.ESC_CAT_A_HIGH_FREQ)
    aggrPointConstraint(
        protection_point, protection_channels, util.ESC_CAT_A_LOW_FREQ, util.ESC_CAT_A_HIGH_FREQ,
        cbsd_grant_reqs, antenna_height, antenna_azimuth, None, util.ProtectionEntityType.ESC_CAT_A)
    # ESC Category B CBSDs between 3550 - 3680 MHz within 80 km
    protection_channels = util.getChannels(
        util.ESC_CAT_B_LOW_FREQ, util.ESC_CAT_B_HIGH_FREQ)
    aggrPointConstraint(
        protection_point, protection_channels, util.ESC_CAT_B_LOW_FREQ, util.ESC_CAT_B_HIGH_FREQ,
        cbsd_grant_reqs, antenna_height, antenna_azimuth, None, util.ProtectionEntityType.ESC_CAT_B)

    return aggregate_interference


def calculateAggregateInterferenceForGWPZ(gwpz, cbsd_list):
    """
    Calculates aggregate interference to GWPZ.
    Inputs:
        gwpz : gwpz protection entity
        cbsd_list: list of CBSD objects
    Returns:
        result: aggregate interference to GWPZ in the dictionary format {(latitude, longitude, lowFrequency,highFrequency,entityType): aggregateinterference, .......}

    """

    cbsd_grant_reqs = util.getGrantsFromCbsdObjects(cbsd_list)

    # Get Fine Grid Points for a GWPZ protoection area
    protection_points = util.getFUGPoints(gwpz)
    gwpz_freqRange = gwpz['record']['deploymentParam'][
        0]['operationParam']['operationFrequencyRange']
    gwpz_lowFreq = gwpz_freqRange['lowFrequency']
    gwpz_highFreq = gwpz_freqRange['highFrequency']
    # Get channels over which area incumbent needs partial/full protection
    protection_channels = util.getChannels(gwpz_lowFreq, gwpz_highFreq)
    aggrAreaConstraint(
        protection_points, protection_channels, gwpz_lowFreq, gwpz_highFreq, cbsd_grant_reqs,
        util.ProtectionEntityType.GWPZ_AREA)
    return aggregate_interference


def calculateAggregateInterferenceForPPA(ppa, cbsd_list):
    """
    Calculates aggregate interference to PPA.
    Inputs:
        ppa : ppa protection entity
        cbsd_list: list of CBSD objects
    Returns:
        result: aggregate interference to PPA in the dictionary format {(latitude, longitude, lowFrequency,highFrequency,entityType): aggregateinterference, .......}
    """
    cbsd_grant_reqs = util.getGrantsFromCbsdObjects(cbsd_list)

    # Get Fine Grid Points for a PPA protoection area
    protection_points = util.getFUGPoints(ppa)
    # TODO -- PAL -- freq range -
    # Get channels over which area incumbent needs partial/full protection
    protection_channels = util.getChannels(
        util.PPA_LOW_FREQ, util.PPA_HIGH_FREQ)
    aggrAreaConstraint(
        protection_points, protection_channels, util.PPA_LOW_FREQ, util.PPA_HIGH_FREQ, cbsd_grant_reqs,
        util.ProtectionEntityType.PPA_AREA)
    return aggregate_interference
