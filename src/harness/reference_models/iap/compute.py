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
# Compute Interference for all the incumbent types
# ==================================================================================

import numpy as np
from reference_models.iap import util
from reference_models.antenna import antenna
from reference_models.propagation import wf_itm 
from reference_models.propagation import wf_hybrid

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

    results = wf_hybrid.CalcHybridPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                                  lat_c, lon_c, h_inc_ant,
                                                  indoor_cbsd,
                                                  reliability=-1,
                                                  freq_mhz=util.FREQ_PROP_MODEL,
                                                  region='SUBURBAN')
    path_loss = np.array(results.db_loss)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                           ant_az_cbsd, ant_beamwidth_cbsd,
                                           ant_gain_cbsd)

    eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain \
                + 10 * np.log10(util.IAPBW/util.ONE_MHZ)

    # Calculate the interference contributions
    interference = eirp_cbsd - path_loss

    return interference


def computeInterferenceESC(cbsd_grant, constraint, h_inc_ant, az_inc_ant, iap_eirp,ant_gain_esc):
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

    results = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=-1,
                                            freq_mhz=util.FREQ_PROP_MODEL)
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
            + 10 * np.log10(util.IAPBW/util.ONE_MHZ) - util.IN_BAND_INSERTION_LOSS

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

    db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(
                                            lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=-1,
                                            freq_mhz=util.FREQ_PROP_MODEL)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
                                               ant_az_cbsd, ant_beamwidth_cbsd,
                                               ant_gain_cbsd)

    # TODO Do we need to consider interference from all the FSS entities
    fss_total_interference = []
    for fss_entity in fss_entities:
        # Compute FSS antenna gain in the direction of CBSD
        fss_ant_gains = antenna.GetFssAntennaGains(
            incidence_angles.hor_rx, incidence_angles.ver_rx,
            fss_entity.pointing_azimuth,
            fss_entity.pointing_elevation,
            fss_entity.max_gain_dbi)

        # Compute EIRP of CBSD grant inside the frequency range of protection constraint
        eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain + fss_ant_gains \
                    + 10 * np.log10(util.IAPBW/util.ONE_MHZ) - util.IN_BAND_INSERTION_LOSS

        # Calculate the interference contributions
        interference = eirp_cbsd - db_loss
        fss_total_interference.append(interference)
   
    # Get the max interference
    fss_interference = int((max(fss_total_interference) * 100)/100)

    return fss_interference


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

    # a last value to reliabilities array
    db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=-1,
                                            freq_mhz=util.FREQ_PROP_MODEL)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
                                               ant_az_cbsd, ant_beamwidth_cbsd,
                                               ant_gain_cbsd)
    # TODO Do we need to consider interference from all the FSS entities
    fss_total_interference = []
    for fss_entity in fss_entities:
        # Compute FSS antenna gain in the direction of CBSD
        fss_ant_gains = antenna.GetFssAntennaGains(
            incidence_angles.hor_rx, incidence_angles.ver_rx,
            fss_entity.pointing_azimuth,
            fss_entity.pointing_elevation,
            fss_entity.max_gain_dbi)

        # Compute EIRP of CBSD grant inside the frequency range of protection constraint
        eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain + fss_ant_gains \
                    + 10 * np.log10((high_freq_cbsd - low_freq_cbsd) / util.ONE_MHZ)

        # Get 50MHz offset below the lower edge of the FSS earth station
        offset = low_freq_c - 50000000

        # Get CBSD grant frequency range
        cbsd_freq_range = high_freq_cbsd - low_freq_cbsd
        
        fss_mask = 0

        # if lower edge of the FSS passband is less than CBSD grant
        # lowFrequency and highFrequency
        if low_freq_c < low_freq_cbsd and low_freq_c < high_freq_cbsd:
            fss_mask = 0.5
        # if CBSD grant lowFrequency and highFrequency is less than
        # 50MHz offset from the FSS passband lower edge
        elif low_freq_cbsd < offset and high_freq_cbsd < offset:
            fss_mask = 10 * np.log10((cbsd_freq_range / util.ONE_MHZ) * 0.25)
        # if CBSD grant lowFrequency is less than 50MHz offset and
        # highFrequency is greater than 50MHz offset
        elif low_freq_cbsd < offset and high_freq_cbsd > offset:
            fss_mask = 10 * np.log10(((offset - low_freq_cbsd) / util.ONE_MHZ) * 0.25)
            fss_mask = fss_mask + 10 * np.log10(((high_freq_cbsd - offset) / util.ONE_MHZ) * 0.6)
        # if FSS Passband lower edge frequency is grater than CBSD grant
        # lowFrequency and highFrequency and
        # CBSD grand low and high frequencies are greater than 50MHz offset
        elif low_freq_c > low_freq_cbsd and low_freq_c > high_freq_cbsd and \
                low_freq_cbsd > offset and high_freq_cbsd > offset:
            fss_mask = 10 * np.log10((cbsd_freq_range / util.ONE_MHZ) * 0.6)

        # Calculate the interference contributions
        interference = eirp_cbsd - fss_mask - db_loss
        fss_total_interference.append(interference)

    # Get the max interference
    fss_interference = int((max(fss_total_interference) * 100)/100)

    return fss_interference



