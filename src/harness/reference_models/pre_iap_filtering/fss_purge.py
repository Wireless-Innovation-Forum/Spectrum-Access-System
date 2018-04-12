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
from reference_models.antenna import antenna
from reference_models.interference import interference
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.pre_iap_filtering import pre_iap_util

# Definition of constants and data types for FSS purge model.
# Reference Channel bandwidth for FSS OOBE calculation
REF_BW = 5.e6

# OOBE Margin
FSS_OOBE_MARGIN = 1

def getFssInfo(fss_record):
  """ Create a FssProtectionPoint tuple from the fss_record.

  Args:
    fss_record: A single FSS record dictionary.
  Returns:
    FssProtectionPoint: Tuple holding details about FSS needed for interference calculation.
  """

  # Extract fields from FSS record.
  fss_latitude = fss_record['record']['deploymentParam'][0]['installationParam']['latitude']
  fss_longitude = fss_record['record']['deploymentParam'][0]['installationParam']['longitude']
  fss_height = fss_record['record']['deploymentParam'][0]['installationParam']['height']
  fss_height_type = fss_record['record']['deploymentParam'][0]['installationParam']['heightType']
  fss_azimuth = fss_record['record']['deploymentParam'][0]['installationParam']['antennaAzimuth']
  fss_pointing_elevation = - fss_record['record']['deploymentParam'][0]['installationParam']['antennaDowntilt']
  fss_max_gain_dbi = fss_record['record']['deploymentParam'][0]['installationParam']['antennaGain']

  # Convert the height to AGL if it was AMSL type.
  if fss_height_type == 'AMSL':
    fss_height_agl = convertAmslToAgl(fss_latitude, fss_longitude, fss_height)
  elif fss_height_type == 'AGL':
    fss_height_agl = fss_height
  else:
    raise Exception('Invalid FSS height type.')

  # Populate FssProtectionPoint tuple.
  fss_entity = interference.FssProtectionPoint(latitude=fss_latitude,
                                               longitude=fss_longitude,
                                               height_agl=fss_height_agl,
                                               max_gain_dbi=fss_max_gain_dbi,
                                               pointing_azimuth=fss_azimuth,
                                               pointing_elevation=fss_pointing_elevation)
  return fss_entity

def performPurge(cbsds, fss_entity):
  """ Implementation of algorithm described in R2-SGN-29.

  The list of grants to be purged based on the interference caused by their
  out of band emission are identified and returned.
  Args:
    cbsds: List of CbsdData objects that are in the neighborhood to an FSS.
    fss_entity: The FssProtectionPoint tuple of the FSS for which the purge is to be performed.
  Returns:
    List of multiple key-value pairs with keys "grantData", "cbsd" and values as grants to be
      purged and corresponding cbsd data object respectively.
  """
  # List of grants to be purged for the fss_entity.
  final_purge_list = []

  # List of dictionaries containing the highest grant of the CBSD and a reference to the CBSD.
  grants_for_oobe_calculation = getHighestGrantOfCbsds(cbsds)

  # Calculate the threshold value in dBm for the OOBE interference
  oobe_threshold_value = -129 + 10 * (np.log10(REF_BW/interference.ONE_MHZ) - FSS_OOBE_MARGIN)

  while True:
    # Calculate the OOBE interference value for each grant.
    calculateOobeInterference(grants_for_oobe_calculation, fss_entity)

    # Sort the grants based on the calculated interference value.
    sorted_grants = sorted(grants_for_oobe_calculation, key=lambda grant: grant['oobe_interference'])

    # Find the largest index such that aggregation of the interferences do not cross
    # the OOBE threshold.
    oobe_interferences = [interference.dbToLinear(grant['oobe_interference']) for grant in sorted_grants]
    cumulated_interference = np.cumsum(oobe_interferences)
    index = np.searchsorted(cumulated_interference, interference.dbToLinear(oobe_threshold_value))
    grants_to_purge = sorted_grants[index:]
    grants_for_oobe_calculation = sorted_grants[:index]
    final_purge_list.extend(grants_to_purge)

    # Add the identified grants to be purged from this iteration to the final list of grants to be purged
    if grants_to_purge:
      for purged_grant in grants_to_purge:
        remaining_grants = []
        # Identify other grants of the CBSD that have the same emission mask as the purged
        # grant and add them to the final purge list. If the CBSD has any other grant with
        # lower emission mask then add it to the remaining_grants list.
        for grant in purged_grant['cbsd']['grants']:
          # Check that we are not comapring the same grant as the pruged grant
          if grant != purged_grant['grantData']:
            if (getMcbsdValue (purged_grant['grantData']) == getMcbsdValue (grant)):
              final_purge_list.append({'grantData': grant, 'cbsd': purged_grant['cbsd']})
            else:
              remaining_grants.append(grant)

        # Identify the grant with the highest highFrequncy value among the remaining grants for the
        # CBSD and add it to the grants_for_oobe_calculation list for next iteration.
        if len(remaining_grants) > 0:
          max_grant = max(remaining_grants,\
                           key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])
          grants_for_oobe_calculation.append({'grantData': max_grant, 'cbsd': purged_grant['cbsd']})

    # If no grants are identified for purging in this iteration then break the loop
    else:
      break

  return final_purge_list

def calculateOobeInterference(grants, fss_entity):
  """Calculate the OOBE interference value (MCBSDi,ch + GCBSDi + PLinvi + GFSSi).

  The interference values are calculated based on the grant with the highest highFrequency value.
  The calculated value is added into the grant object.
  Args:
    grants: List of dictionaries contianing the highest grant of the CBSD and a reference to the CBSD.
    fss_entity: The FssProtectionPoint tuple of the FSS for which the interference is calculated.
  """
  # Get values of MCBSD,GCBSD,GFSS and LCBSD for each CBSD.
  for grant in grants:
    if grant['cbsd']['grants']:
      lcbsd, incidence_angle = getMeanPathLossFromCbsdToFss(grant['cbsd'], fss_entity)
      mcbsd = getMcbsdValue(grant['grantData'])
      gcbsd = getAntennaGainTowardsFss(incidence_angle, grant['cbsd'])
      gfss = getAntennaGainFssReceiver(fss_entity, incidence_angle)
      oobe_interference = mcbsd + gcbsd - lcbsd + gfss
      grant['oobe_interference'] = oobe_interference

def getMcbsdValue(grant):
  """ Identifies the MCBSD (OOBE emission mask) value for a grant.

  MCBSD is the CBSD conducted power (in dBm) on the frequency segment,
  using the Tx mask of CBSD according to R0-DEV-05(e).
  Args:
    grant: A GrantData dictionary as defined in SAS-SAS specification.
  Returns:
    MCBSD (OOBE emission mask) value. 
  """
  if grant['operationParam']['operationFrequencyRange']['highFrequency'] > 3690000000:
      mcbsd = -13
  else:
      mcbsd = -25

  return mcbsd

def getAntennaGainTowardsFss(incidence_angle, cbsd):
  """Get antenna gain of CBSD in direction of FSS protection point [R2-SGN-20]

  Args:
    incidence_angle: Incidence angle as identified by ITM model.
    cbsd: A CbsdData object.
  Returns:
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
                                         freq_mhz=interference.FREQ_PROP_MODEL_MHZ)

  return db_loss, incidence_angle

def convertAmslToAgl(latitude, longitude, height_amsl):
  """ Convert AMSL height to AGL height."""

  altitude_cbsd = wf_itm.terrainDriver.GetTerrainElevation(latitude, longitude)
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
                              fss_entity.max_gain_dbi)
  return fss_ant_gain

def getHighestGrantOfCbsds(cbsds):
  """Creates a new list of grants for oobe_calculation

  Args:
    cbsds: A CbsdData objects
  Returns:
    List of multiple key-value pairs with keys 'grantData', 'cbsd' and values as max_grant and
      corresponding cbsd data object respectively
  """
  grants_for_oobe_calculation = []
  for cbsd in cbsds:
    max_grant = max(cbsd['grants'],\
                    key=lambda x: x['operationParam']['operationFrequencyRange']['highFrequency'])
    grant_info = {
        'grantData': max_grant,
        'cbsd': cbsd
    }
    grants_for_oobe_calculation.append(grant_info)

  return grants_for_oobe_calculation

def fssPurgeReferenceModel(sas_uut_fad, sas_test_harness_fads, fss_records):
  """Entry point function to execute FSS purge list model.

  Performs FSS purge model as described in R2-SGN-29 on the FAD CBSD records of SAS UUT
  and SAS test harnesses for a list of FSS records. The grants are removed from the CBSD
  records of the FAD objects.
  Args:
    sas_uut_fad: A FullActivityDump object containing the FAD records of SAS UUT.
    sas_test_harness_fads: A list of FullActivityDump objects containing the FAD records
      from SAS test harnesses.
    fss_records: A list of FSS record dictionary.
  """
  # Get the CBSD list from the FAD Object.
  cbsds = []
  cbsds.extend(sas_uut_fad.getCbsdRecords())
  for fad in sas_test_harness_fads:
    cbsds.extend(fad.getCbsdRecords())

  grants_to_purged_for_all_fss = []
  for fss_record in fss_records:
    # If the FSS is of TT&C type then perform the FSS purge model for the FSS.
    if fss_record['ttc']:
      neighboring_cbsds_with_grants = pre_iap_util.getFssNeighboringCbsdsWithGrants(cbsds, fss_record, 40)
      if neighboring_cbsds_with_grants:
        fss_entity = getFssInfo(fss_record)
        grants_to_purge_for_fss = performPurge(neighboring_cbsds_with_grants, fss_entity)
        grants_to_purged_for_all_fss.extend(purge_data for purge_data in grants_to_purge_for_fss
                                                     if purge_data not in grants_to_purged_for_all_fss)

  # Removing grant requests that are in the grants to purge list from the CBSDs.
  for purge_data in grants_to_purged_for_all_fss:
    purge_data['cbsd']['grants'].remove(purge_data['grantData'])

