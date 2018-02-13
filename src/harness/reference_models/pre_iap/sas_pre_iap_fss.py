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

"""
==================================================================================
    This is a subset of the Pre-IAP reference model which implements
    the FSS purge list algorithm described in R2-SGN-29
    The main route is fssPurgeModel(sas_uut_fad, sas_harness_fads, fss_record, margin_oobe)
==================================================================================
"""

import math
from reference_models.antenna import antenna
from reference_models.antenna import fss_pointing
from reference_models.examples import entities
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm


REF_BW = 5000000.0
ONE_MHZ = 1.0
# Find all the FSS protection points from a given FSS license info
def GetAllFssFromLicenseInfo(fss_license_info):
  """Get all Fss protection points from a FSS license record.

  Inputs:
    fss_license_info:  A |FssLicenseInfo| holding the license record.

  Returns:
    a list of |FssProtectionPoint| with same location and different pointings.
  """
  info = fss_license_info
  pointings = fss_pointing.GsoPossiblePointings(
      info.latitude, info.longitude,
      info.satellite_arc_west_limit, info.satellite_arc_east_limit,
      info.elevation_west_limit, info.elevation_east_limit,
      info.azimuth_west_limit, info.azimuth_east_limit)
  fss_entities = []
  for (azimuth, elevation) in pointings:
    fss = entities.FssProtection(latitude=info.latitude,
                                 longitude=info.longitude,
                                 height_agl=info.height_agl,
                                 max_gain_dbi=info.max_gain_dbi,
                                 pointing_azimuth=azimuth,
                                 pointing_elevation=elevation)
    fss_entities.append(fss)

  return fss_entities

def getNeighbouringCbsds(all_cbsds, base_fss):
    """
    Get the list of all cbsds that lie within 40 km of FSS
    
    Inputs:
    List of all CBSDs
    Fss entity

    Outputs:
    List of CBSDs lying within 40 km
    """
    
    neighbouring_cbsds = []
    for cbsd in all_cbsds:
        distance_km, _, _ = vincenty.GeodesicDistanceBearing(
            base_fss.latitude, base_fss.longitude,
            cbsd['registrationRequest']['installationParam']['latitude'],
            cbsd['registrationRequest']['installationParam']['longitude'])
        if distance_km <= 40:
            neighbouring_cbsds.append(cbsd)
    return neighbouring_cbsds


def performPurge(cbsds,base_fss,margin_oobe):
    """
    Purging the grants 
    """
  
    calculateOobeInterference(cbsds, base_fss)
    # Sorting CBSD based on its interference value
    sfss = sorted(cbsds, key=lambda cbsd: cbsd['interference_value'])
    # Reference interference value
    oobe_threshold_value =(-1 * 129) + 10 * (math.log10(REF_BW/ONE_MHZ) - margin_oobe)
    # Update sfss and pfss list
    total_cbsd_interference = 0
    for index, cbsd in enumerate(sfss):
        total_cbsd_interference = total_cbsd_interference + cbsd['interference_value']
        if total_cbsd_interference > oobe_threshold_value:
            nc = index
            break     
        else:
            nc = index + 1   
    pfss = sfss[nc:]
    sfss = sfss[:nc]
    if len(pfss) == 0:
       return
    else:
        # for each cbsd
        for index, cbsd in enumerate(pfss):
            grants = cbsd['grantRequests']
            # Get the grant that was used for the OOBE interference calculation, which is the grant with highest highFrequency.
            grant_with_max_high_freq = \
            max(cbsd['grantRequests'],
                key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])
            # Get all the grants that share the same emission mask as the one that was used for OOBE calculation
            if grant_with_max_high_freq['operationParam']['operationFrequencyRange']['highFrequency'] > 3690000000:
                grants_to_purge = [grant_request for grant_request in cbsd['grantRequests'] \
                 if grant_request['operationParam']['operationFrequencyRange']['highFrequency'] > 3690000000]
            else:
                # Adding the -25 emission mask grants to the purge list
                grants_to_purge = [grant_request for grant_request in cbsd['grantRequests'] \
                 if grant_request['operationParam']['operationFrequencyRange']['highFrequency'] <= 3690000000]
            for grant_items in grants_to_purge:
                cbsd['grantRequests'].remove(grant_items)
            # If no grants are remaining then remove the cbsd
            if len(cbsd['grantRequests']) == 0:
                pfss.remove(cbsd)
            else:
                sfss.append(cbsd)
        #performPurge(sfss, base_fss,margin_oobe)

       
def calculateOobeInterference(cbsds, base_fss):
    """
    Calculate the required variables
    :param cbsds: List of neighbouring CBSDs
    :param base_fss: FSS entity
    """

    # Get values of MCBSD,GCBSD,GFSS and LCBSD for each CBSD within 40 km of fss
    for cbsd in cbsds:
        grant_with_max_high_freq = \
            max(cbsd['grantRequests'],
                key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])
        lcbsd, incidence_angle = getMeanPathLossFromCbsdToFss(cbsd, base_fss)
        antenna_gain = cbsd['registrationRequest']['installationParam']['antennaGain']
        mcbsd = getMcbsdValue(grant_with_max_high_freq, antenna_gain)
        max_eirp = grant_with_max_high_freq['operationParam']['maxEirp']
        gcbsd = getAntennaGainTowardsFss(incidence_angle, cbsd, max_eirp)
        gfss = getAntennaGainFssReceiver(base_fss, incidence_angle)
        agg_interference_value = mcbsd + gcbsd - lcbsd + gfss
        cbsd['interference_value'] = agg_interference_value
        


def getMcbsdValue(grant_request, antenna_gain):
    """
    Get max-eirp value from the grant_request
    """
    return grant_request['operationParam']['maxEirp'] + antenna_gain


def getAntennaGainTowardsFss(incidence_angle, cbsd, max_eirp):
    """
    Get antenna gain of CBSD in direction of FSS protection point
    """
    cbsd_antenna_gain = antenna.GetStandardAntennaGains(
        incidence_angle.hor_cbsd, cbsd['registrationRequest']['installationParam']['antennaAzimuth'],
        cbsd['registrationRequest']['installationParam']['antennaBeamwidth'],
        max_eirp)
    return cbsd_antenna_gain


def getMeanPathLossFromCbsdToFss(cbsd, fss):
    """
    Get mean path loss from CBSD to fss protection in linear scale
    """
    db_loss, incidence_angle, _ = wf_itm.CalcItmPropagationLoss(
        cbsd['registrationRequest']['installationParam']['latitude'],
        cbsd['registrationRequest']['installationParam']['longitude'],
        cbsd['registrationRequest']['installationParam']['height'],
        fss.latitude,
        fss.longitude,
        fss.height_agl)
    return db_loss, incidence_angle


def getAntennaGainFssReceiver(fss_entity, incidence_angle):
    """
    Get antenna gain of fss receiver
    """
    fss_ant_gain = antenna.GetFssAntennaGains(
         incidence_angle.hor_rx, incidence_angle.ver_rx,
         fss_entity.pointing_azimuth,
         fss_entity.pointing_elevation,
         fss_entity.max_gain_dbi)
    return fss_ant_gain



def fssPurgeModel(sas_uut_fad, sas_harness_fads, fss_record, margin_oobe):    
    """
    Entry point function to execute FSS purge list model
    perform  fss purge on the fad_record for fss entity
    :param sas_uut_fad : UUT FAD object
    :param sas_harness_fad: TH FAD object
    :param fss_record: One FSS entity
    """
    if fss_record['deploymentParam'][0]['ttc_flag']:
       cbsds = []
       cbsds.extend(sas_uut_fad.getCbsds())
       for fad in sas_harness_fads:
           cbsds.extend(fad.getCbsds())

       #Get fss info 
       fss_info = entities.FssLicenseInfo(latitude=fss_record['deploymentParam'][0]['installationParam']['latitude'],
                                   longitude=fss_record['deploymentParam'][0]['installationParam']['longitude'],
                                   height_agl=fss_record['deploymentParam'][0]['installationParam']['height'],
                                   max_gain_dbi=fss_record['deploymentParam'][0]['installationParam']['antennaGain'],
                                   satellite_arc_east_limit=-60,
                                   satellite_arc_west_limit=-143,
                                   elevation_east_limit=32.8,
                                   elevation_west_limit=22.9,
                                   azimuth_east_limit=132.6,
                                   azimuth_west_limit=241.2)
       fss_entities = GetAllFssFromLicenseInfo(fss_info)
       base_fss = fss_entities[0]
       cbsds = getNeighbouringCbsds(cbsds, base_fss)
       performPurge(cbsds, base_fss,margin_oobe)
