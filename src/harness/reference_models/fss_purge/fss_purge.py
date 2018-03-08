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
    the FSS purge list algorithm described in R2-SGN-29.
    The main function is fssPurgeModel().
==================================================================================
"""
import numpy as np
import sys

sys.path.append('../..')
from collections import namedtuple
from reference_models.antenna import antenna
from reference_models.geo import terrain, vincenty
from reference_models.propagation import wf_itm

# Definition of constants and data types for FSS purge model.
# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0

# Reference Channel bandwidth for FSS OOBE calculation
REF_BW = 5000000.0

# One Mega Hertz
ONE_MHZ = 1000000.0

# Define FSS information tuple containing the parameters necessary for antenna
# and propagation calculation as listed in the test spec
FssProtectionPoint = namedtuple('FssEntity',
                           ['latitude',
                            'longitude',
                            'height_agl',
                            'max_gain_dbi',
                            'pointing_azimuth',
                            'pointing_elevation',
                            'weight_1',
                            'weight_2'])

def getFssInfo(fss_record):
  """ Create a FssProtectionPoint tuple from the fss_record.

  Args:
    fss_record: A single FSS record dictionary.
  Returns:
    FssProtectionPoint: Tuple holding details about FSS needed for interference calculation.
  """

  # Extract fields from FSS record. 
  fss_latitude = fss_record['deploymentParam'][0]['installationParam']['latitude']
  fss_longitude = fss_record['deploymentParam'][0]['installationParam']['longitude']
  fss_height = fss_record['deploymentParam'][0]['installationParam']['height']
  fss_height_type = fss_record['deploymentParam'][0]['installationParam']['heightType']
  fss_azimuth = fss_record['deploymentParam'][0]['installationParam']['antennaAzimuth']
  fss_pointing_elevation = fss_record['deploymentParam'][0]['installationParam']['elevation']
  fss_max_gain_dbi = fss_record['deploymentParam'][0]['installationParam']['antennaGain']
  fss_weight_1 = fss_record['deploymentParam'][0]['weight1']
  fss_weight_2 = fss_record['deploymentParam'][0]['weight2']
  # Convert the height to AGL if it was AMSL type.
  if fss_height_type == 'AMSL':
     fss_height_agl = convertAmslToAgl(fss_latitude, fss_longitude, fss_height)
  else:
     fss_height_agl = fss_height

  # Populate FssProtectionPoint tuple.
  fss_entity = FssProtectionPoint(latitude=fss_latitude,
                                  longitude=fss_longitude,
                                  height_agl=fss_height_agl,
                                  max_gain_dbi=fss_max_gain_dbi,
                                  pointing_azimuth=fss_azimuth,
                                  pointing_elevation=fss_pointing_elevation,
                                  weight_1=fss_weight_1,
                                  weight_2=fss_weight_2)
  return fss_entity

def getNeighbouringCbsdsToFss(cbsd_list, fss_record):
  """ Get the list of all CBSDs that lie within 40 KMs of FSS.

  Args:
    cbsd_list: List of CBSDs.
    fss_record: A FSS record dictionary.
  Returns:
    List of CBSDs lying within 40 KMs of FSS.
  """

  neighbouring_cbsds = []
  for cbsd in cbsd_list:
    distance_km, _, _ = vincenty.GeodesicDistanceBearing(
        fss_record['deploymentParam'][0]['installationParam']['latitude'],
        fss_record['deploymentParam'][0]['installationParam']['longitude'],
        cbsd['registrationRequest']['installationParam']['latitude'],
        cbsd['registrationRequest']['installationParam']['longitude'])

    if distance_km <= 40:
        neighbouring_cbsds.append(cbsd)
  return neighbouring_cbsds

def dbmAddition(value1, value2):
  """ Adds two values in dBm unit.

  Converts the input values from dBm to linear scale and adds the values together.
  The result is converted back to dBm unit.

  Args:
    value1: First operand to be added in dBm.
    value2: Second operand to be added in dBm.
  Returns:
    Sum of value1 and value2 in dBm.
  """
  sum_in_linear = (10**(value1/10.)) + (10**(value2/10.))
  sum_in_dbm = (10*np.log10(sum_in_linear))
  
  return sum_in_dbm

def performPurge(cbsds, fss_entity, fss_oobe_margin):
  """ Implementation of algorithm described in R2-SGN-29.

  The list of grants to be purged based out of band emission are identifies and the grants
  are removed from the CBSDs. If a CBSDs has no grants then the CBSD is removed from the list.

  Args:
    cbsds: List of CbsdData objects that are in the neighbourhood to an FSS.
    fss_entity: The FssProtectionPoint tuple of the FSS for which the purge is to be performed.
    fss_oobe_margin: OOBE Margin value to be considered for FSS purge list calculation.
  """

  # Calculate the OOBE interference value for each CBSD based on the grant with the highest frequency.
  calculateOobeInterference(cbsds, fss_entity)

  # Sort the CBSDs based on the calculated interference value.
  sfss = sorted(cbsds, key=lambda cbsd: cbsd['oobe_interference'])
  # Calcualte the threshold value in dBm for the OOBE interference
  oobe_threshold_value = (-1 * 129) + 10 * (np.log10(REF_BW/ONE_MHZ) - fss_oobe_margin)

  # Find the largest index (nc) such that aggregation of the interferences do not cross 
  # the OOBE threshold
  for index, cbsd in enumerate(sfss):
    if index == 0:
      aggregate_interference = cbsd['oobe_interference']
    else:
      aggregate_interference = dbmAddition(aggregate_interference, cbsd['oobe_interference'])
    if aggregate_interference > oobe_threshold_value:
      nc = index
      break
  else:
    nc = len(sfss) + 1

  # Update sfss and pfss list. pfss contains the list of CBSDs for which grants needs to be purged.
  if len(sfss) != 0:
    pfss = sfss[nc:]
    sfss = sfss[:nc]
    if len(pfss) == 0:
       return
    else:
      for index, cbsd in enumerate(pfss):
        # Get the grant that was used for the OOBE interference calculation, that
        # is the grant with highest highFrequency.
        grant_with_max_high_freq = max(cbsd['grantRequests'],\
              key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])

        # Get all the grants that share the same emission mask as the one that 
        # was used for OOBE calculation
        if (grant_with_max_high_freq['operationParam']['operationFrequencyRange']\
            ['highFrequency'] > 3690000000):

          # Adding the -13 emission mask grants to the purge list 
          
          grants_to_purge = [grant_request for grant_request in cbsd['grantRequests'] \
                              if grant_request['operationParam']['operationFrequencyRange']\
                              ['highFrequency'] > 3690000000]
        else:
          # Adding the -25 emission mask grants to the purge list
          grants_to_purge = [grant_request for grant_request in cbsd['grantRequests'] \
                              if grant_request['operationParam']['operationFrequencyRange']\
                              ['highFrequency'] <= 3690000000]

        # Removing grant requests that are in the purge list from the CBSDs.
        for grant_items in grants_to_purge:
           cbsd['grantRequests'].remove(grant_items)

        # If no grants are remaining then remove the CBSD.
        if len(cbsd['grantRequests']) == 0:
           pfss.remove(cbsd)
        else:
           sfss.append(cbsd)

      performPurge(sfss, fss_entity, fss_oobe_margin)

  return 

def calculateOobeInterference(cbsds, fss_entity):
  """Calculate the OOBE interference value (MCBSDi,ch + GCBSDi + PLinvi + GFSSi).
  
  The interference values are calculated based on the grant with the highest highFrequency value.
  The calculated value is added into the CBSD object.

  Args:
    cbsds: List of CbsdData objects that are in the neighbourhood to an FSS.
    fss_entity: The FssProtectionPoint tuple of the FSS for which the interference is calculated.
  """

  # Get values of MCBSD,GCBSD,GFSS and LCBSD for each CBSD.
  for cbsd in cbsds:
    grant_with_max_high_freq = max(cbsd['grantRequests'],\
            key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])

    lcbsd, incidence_angle = getMeanPathLossFromCbsdToFss(cbsd, fss_entity)
    mcbsd = getMcbsdValue(grant_with_max_high_freq)
    gcbsd = getAntennaGainTowardsFss(incidence_angle, cbsd)
    gfss = getAntennaGainFssReceiver(fss_entity, incidence_angle)

    oobe_interference = mcbsd + gcbsd - lcbsd + gfss
    cbsd['oobe_interference'] = oobe_interference

def getMcbsdValue(grant_request):
  """ Identifies the MCBSD value for a grant.

  MCBSD is the CBSD conducted power (in dBm) on the frequency segment, 
  using the Tx mask of CBSD according to R0-DEV-05(e).

  Args:
    grant_request: A GrantData object.
  Returns:
    MCBSD value
  """
  if grant_request['operationParam']['operationFrequencyRange']['highFrequency'] > 3690000000:
      mcbsd = -13
  else:
      mcbsd = -25

  return mcbsd

def getAntennaGainTowardsFss(incidence_angle, cbsd):
  """Get antenna gain of CBSD in direction of FSS protection point [R2-SGN-20]

  Args:
    incidence_angle: Incidence angle as identified by ITM model.
    cbsd: A CbsdData object
  Returns
    Antenna gain towards FSS in dBi.
  """

  cbsd_antenna_gain = antenna.GetStandardAntennaGains( incidence_angle.hor_cbsd,\
                       cbsd['registrationRequest']['installationParam']['antennaAzimuth'],
                       cbsd['registrationRequest']['installationParam']['antennaBeamwidth'],
                       cbsd['registrationRequest']['installationParam']['antennaGain'])

  return cbsd_antenna_gain

def getMeanPathLossFromCbsdToFss(cbsd, fss):
  """Get mean ITM path loss from CBSD to FSS protection point.

  Args:
    cbsd: A CbsdData object
    fss_entity: The FssProtectionPoint tuple of the FSS.
  Returns:
    Mean path loss from CBSD to FSS in dBi.
  """

  # Extract the CBSD parameters
  cbsd_latitude = cbsd['registrationRequest']['installationParam']['latitude']
  cbsd_longitude = cbsd['registrationRequest']['installationParam']['longitude']
  cbsd_height = cbsd['registrationRequest']['installationParam']['height']
  cbsd_height_type = cbsd['registrationRequest']['installationParam']['heightType']
  cbsd_indoor_dep = cbsd['registrationRequest']['installationParam']['indoorDeployment']
  if cbsd_height_type == 'AMSL':
      cbsd_height_agl = convertAmslToAgl(cbsd_latitude, cbsd_longitude, cbsd_height)
  else:
      cbsd_height_agl = cbsd_height

  # Invoking ITM propagation model
  db_loss, incidence_angle, _ = wf_itm.CalcItmPropagationLoss(
                                         cbsd_latitude,
                                         cbsd_longitude,
                                         cbsd_height_agl,
                                         fss.latitude,
                                         fss.longitude,
                                         fss.height_agl,
                                         cbsd_indoor_dep,
                                         reliability=-1,
                                         freq_mhz=FREQ_PROP_MODEL)

  return db_loss, incidence_angle

def convertAmslToAgl(latitude, longitude, height_amsl):
  """ Convert AMSL height to AGL height."""

  altitude_cbsd = terrain.GetTerrainElevation(latitude, longitude)
  return height_amsl - altitude_cbsd

def getAntennaGainFssReceiver(fss_entity, incidence_angle):
  """Get antenna gain of FSS receiver determined using FSS antenna reference model.

  Args:
    cbsd: A CbsdData object
    incidence_angle: Incidence angle as identified by ITM model.
  Returns:
    Antenna gain of FSS in dBi.
  """

  #Invoke FSS antenna reference model.
  fss_ant_gain = antenna.GetFssAntennaGains(
                              incidence_angle.hor_rx, incidence_angle.ver_rx,
                              fss_entity.pointing_azimuth,
                              fss_entity.pointing_elevation,
                              fss_entity.max_gain_dbi,
                              fss_entity.weight_1,
                              fss_entity.weight_2)


  return fss_ant_gain

def fssPurgeModel(sas_uut_fad, sas_harness_fads, fss_record, fss_oobe_margin):
  """Entry point function to execute FSS purge list model.

  Performs FSS purge model as described in R2-SGN-29 on the FAD CBSD records of SAS UUT
  and SAS test harnesses for a given FSS entity. The grants are removed from the CBSD
  records of the FAD objects.

  Args:
    sas_uut_fad: A FullActivityDump object containing the FAD records of SAS UUT.
    sas_harness_fads: A list of FullActivityDump objects containing the FAD records 
      from SAS test harnesses.
    fss_record: A single FSS record dictionary.
    fss_oobe_margin: OOBE Margin value to be considered for FSS purge list calculation.
  """

  # If the FSS is of TT&C type then perform the FSS purge model for the FSS.
  if fss_record['deploymentParam'][0]['ttc']:
    # Get the CBSD list from the FAD Object. 
    cbsds = []
    cbsds.extend(sas_uut_fad.getCbsdRecords())
    for fad in sas_harness_fads:
      cbsds.extend(fad.getCbsdRecords())

    neighbouring_cbsds = getNeighbouringCbsdsToFss(cbsds, fss_record)
    if neighbouring_cbsds:
      fss_entity = getFssInfo(fss_record)
      performPurge(neighbouring_cbsds, fss_entity, fss_oobe_margin)

      # Removing the oobe_interference parameter added to cbsd objects
      for cbsd in neighbouring_cbsds:
        cbsd.pop('oobe_interference', None)      
  return 
