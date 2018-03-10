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
from reference_models.geo import terrain,vincenty
from reference_models.propagation import wf_itm

# One Mega Herts
ONE_MHZ = 1000000.0

# Reference Channel bandwidth for FSS OOBE calculation
REF_BW = 5000000.0

# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0
# Find all the FSS protection points from a given FSS license info
def GetAllFssFromLicenseInfo(fss_license_info):
  """Get all Fss protection points from a FSS license record.

  Args:
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

def getNeighbouringCbsds(all_cbsds, fss_record):
    """
    Get the list of all cbsds that lie within 40 km of FSS
    
    Args:
    List of all CBSDs
    Fss entity

    Returns:
    List of CBSDs lying within 40 km
    """
    
    neighbouring_cbsds = []
    for cbsd in all_cbsds:
        distance_km, _, _ = vincenty.GeodesicDistanceBearing(
            fss_record['deploymentParam'][0]['installationParam']['latitude'],
            fss_record['deploymentParam'][0]['installationParam']['longitude'],
            cbsd['registrationRequest']['installationParam']['latitude'],
            cbsd['registrationRequest']['installationParam']['longitude'])
        if distance_km <= 40:
            neighbouring_cbsds.append(cbsd)
    return neighbouring_cbsds

def performPurge(cbsds, fss_entities, margin_oobe):
    """
    Purging the grants

    Args:
     List of neighbouring CBSDs
     List of fss entities
     OOBE_margin 
    """
  
    calculateOobeInterference(cbsds, fss_entities)
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
            # Get the grant that was used for the OOBE interference calculation, which is the grant with highest highFrequency.
            grant_with_max_high_freq = \
            max(cbsd['grantRequests'],
                key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])
            # Get all the grants that share the same emission mask as the one that was used for OOBE calculation
            
            if grant_with_max_high_freq['operationParam']['operationFrequencyRange']['highFrequency'] > 3690000000:
                # Adding the -13 emission mask grants to the purge list
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
        performPurge(sfss, fss_entities, margin_oobe)
       
def calculateOobeInterference(cbsds, fss_entities):
    """
    Calculate the required interference values

    Args:
     cbsds: List of neighbouring CBSDs
     fss_entities: List of fss pointings

    Returns:
     value of interference in dBm
    """

    # Get values of MCBSD,GCBSD,GFSS and LCBSD for each CBSD within 40 km of fss
    base_fss = fss_entities[0]
    for cbsd in cbsds:
        grant_with_max_high_freq = \
            max(cbsd['grantRequests'],
                key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])
        lcbsd, incidence_angles = getMeanPathLossFromCbsdToFss(cbsd, base_fss)
        max_cbsd_antenna_gain = cbsd['registrationRequest']['installationParam']['antennaGain']
        mcbsd = getMcbsdValue(grant_with_max_high_freq, max_cbsd_antenna_gain)
        gcbsd = getAntennaGainTowardsFss(incidence_angles, cbsd)
        gfss = getAntennaGainFssReceiver(fss_entities, incidence_angles)
        agg_interference_value = mcbsd + gcbsd - lcbsd + gfss
        cbsd['interference_value'] = agg_interference_value
        
def getMcbsdValue(grant_request, max_cbsd_antenna_gain):
    """
    Get max-eirp value from the grant_request
    Args:
     Grant Request with maximum high frequency
     Maximum CBSD antenna gain
    """
    return grant_request['operationParam']['maxEirp'] - max_cbsd_antenna_gain

def getAntennaGainTowardsFss(incidence_angles, cbsd):
    """
    Get antenna gain of CBSD in direction of FSS protection point
    Args:
     Incidence Angles
     CBSD object
     Maximum EIRP
    """
    cbsd_antenna_gain = antenna.GetStandardAntennaGains(
        incidence_angles.hor_cbsd, cbsd['registrationRequest']['installationParam']['antennaAzimuth'],
        cbsd['registrationRequest']['installationParam']['antennaBeamwidth'],
        cbsd['registrationRequest']['installationParam']['antennaGain'])
    return cbsd_antenna_gain

def getMeanPathLossFromCbsdToFss(cbsd, fss):
    """
    Get mean path loss from CBSD to fss protection in linear scale
    Args:
     CBSD object
     FSS entity
    """
    cbsd_latitude = cbsd['registrationRequest']['installationParam']['latitude']
    cbsd_longitude = cbsd['registrationRequest']['installationParam']['longitude']
    cbsd_height = cbsd['registrationRequest']['installationParam']['height']
    cbsd_height_type = cbsd['registrationRequest']['installationParam']['heightType']
    cbsd_indoor_dep = cbsd['registrationRequest']['installationParam']['indoorDeployment']
    if cbsd_height_type == 'AMSL':
        cbsd_height_agl = convertAmslToAgl(cbsd_latitude, cbsd_longitude, cbsd_height)
    else:
        cbsd_height_agl = cbsd_height
    db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(
        cbsd_latitude,
        cbsd_longitude,
        cbsd_height_agl,
        fss.latitude,
        fss.longitude,
        fss.height_agl,
        cbsd_indoor_dep,
        reliability=-1,
        freq_mhz=FREQ_PROP_MODEL)

    return db_loss, incidence_angles

def convertAmslToAgl(latitude, longitude, height_amsl):
    """
    Convert AMSL height to AGL height
  
    Args:
     Latitude
     Longitude
     AMSL height

    Returns: AGL height

    """        
    altitude_cbsd = terrainDriver.GetTerrainElevation(latitude, longitude)
    return height_amsl - altitude_cbsd

def getAntennaGainFssReceiver(fss_entities, incidence_angles):
    """
    Get antenna gain of fss receiver
    Args:
     List of FSS entities
     Incidence Angles
    """
    fss_ant_gain = []
    for fss_pointing in fss_entities:
        fss_ant_gain.append(antenna.GetFssAntennaGains(
             incidence_angles.hor_rx, incidence_angles.ver_rx,
             fss_pointing.pointing_azimuth,
             fss_pointing.pointing_elevation,
             fss_pointing.max_gain_dbi))
    return max(fss_ant_gain)

def fssPurgeModel(sas_uut_fad, sas_harness_fads, fss_record, margin_oobe):    
    """
    Entry point function to execute FSS purge list model
    perform  fss purge on the fad_record for fss entity
    Args:
     sas_uut_fad : UUT FAD object
     sas_harness_fad: TH FAD object
     fss_record: One FSS entity
     margin_oobe: OOBE margin value
    """
    if fss_record['deploymentParam'][0]['ttc_flag']:
       cbsds = []
       cbsds.extend(sas_uut_fad.getCbsds())
       for fad in sas_harness_fads:
           cbsds.extend(fad.getCbsds())

       cbsds = getNeighbouringCbsds(cbsds, fss_record)
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
       performPurge(cbsds, fss_entities, margin_oobe)
       # Removing the interference_value parameter added to cbsd objects
       for cbsd in cbsds:
           cbsd.pop('interference_value',None)
