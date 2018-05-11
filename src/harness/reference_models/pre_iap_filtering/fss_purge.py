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

"""FSS Purge List reference model.

This is a subset of the Pre-IAP reference model which implements the FSS purge list
algorithm described in R2-SGN-29.
"""
import numpy as np
from collections import namedtuple

from reference_models.common import data
from reference_models.antenna import antenna
from reference_models.interference import interference as interf
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.pre_iap_filtering import pre_iap_util

# Definition of constants and data types for FSS purge model.
# Reference Channel bandwidth for FSS OOBE calculation
REF_BW = 5.e6

# OOBE Margin
FSS_OOBE_MARGIN = 1

# Define named tuple
grants_cbsds_namedtuple = namedtuple('grants_cbsds_namedtuple', ['grant', 'cbsd'])


def generatePurgeListForFssPoint(cbsds, fss_point, fss_info):
  """Generates the FSS purge list.

  Implementation of algorithm described in R2-SGN-29.
  The list of grants to be purged based on the interference caused by their
  out of band emission are identified and returned.

  Args:
    cbsds: The list of |CbsdData| objects that are in the neighborhood to an FSS.
    fss_point: The FSS location as a (longitude, latitude) tuple.
    fss_info: The |data.FssInformation| of the FSS.

  Returns:
    A list of dictionaries, each holding keys:
      'grant': the grants to be purged
      'cbsd': the corresponding |CbsdData| object.

    A list of multiple key-value pairs with keys "grantData", "cbsd" and values as grants to be
    purged and corresponding cbsd data object respectively.
  """
  # List of grants to be purged for the fss entity.
  final_purge_list = []

  # List of dictionaries containing the grant_info based on the highest grant
  # from FSS OOBE calculation
  grants_cbsds_info_for_oobe_calculation = getGrantInfoListForFssOobeCalculation(cbsds)

  # Calculate the threshold value in dBm for the OOBE interference
  oobe_threshold_value = -129 + 10 * np.log10(REF_BW/interf.MHZ) - FSS_OOBE_MARGIN

  while True:

    # Calculate the OOBE interference value for each grant.
    calculateOobeInterference(grants_cbsds_info_for_oobe_calculation, fss_point, fss_info)

    # Sort the grants based on the calculated interference value.
    sorted_grants_cbsds_info = sorted(grants_cbsds_info_for_oobe_calculation,
                                      key=lambda grant: grant['oobe_interference'])
    # Find the largest index such that aggregation of the interferences are not equal
    # to or higher than the OOBE threshold.
    oobe_interferences = [interf.dbToLinear(grant['oobe_interference'])
                          for grant in sorted_grants_cbsds_info]
    cumulated_interference = np.cumsum(oobe_interferences)
    index = np.searchsorted(cumulated_interference, interf.dbToLinear(oobe_threshold_value))
    grants_to_purge = sorted_grants_cbsds_info[index:]
    grants_cbsds_info_for_oobe_calculation = sorted_grants_cbsds_info[:index]

    # If no grants are identified for purging in this iteration then break the loop
    if not grants_to_purge:
      break
    # Otherwise update purge list
    for purged_grant in grants_to_purge:
      remaining_grants = []
      for grant in purged_grant['cbsd']['grants']:
        # Find the grants matching mcbsd value and add it to the purge list
        if purged_grant['mcbsd'] == getMcbsdValue(grant):
          final_purge_list.append(grants_cbsds_namedtuple(grant,
                                                          purged_grant['cbsd']))
        elif purged_grant['mcbsd'] > getMcbsdValue(grant):
          # Find the grants with mcbsd value less than the max_grant mcbsd value
          # and add it to the remaining grants list
          remaining_grants.append(grant)

      # Identify the grant with the highest highFrequency value among the remaining
      # grants for the CBSD and add it to the grants_cbsds_info_for_oobe_calculation
      # list for next iteration.
      if remaining_grants:
        max_grant = max(remaining_grants,
                        key=lambda x:
                        x['operationParam']['operationFrequencyRange']['highFrequency'])
        grants_cbsds_info_for_oobe_calculation.append(
            {'mcbsd': getMcbsdValue(max_grant),
             'cbsd': purged_grant['cbsd']})

  return final_purge_list


def calculateOobeInterference(grants_cbsds_oobe_info, fss_point, fss_info):
  """Calculates the OOBE interference value (MCBSDi,ch + GCBSDi + PLinvi + GFSSi).

  The interference values are calculated based on the grant with the highest
  highFrequency value, and added back into the grant object under key:
     'oobe_interference'.

  Args:
    grants_cbsds_oobe_info : List of dictionaries containing the highest grant
      of their CBSD and a reference to the CBSD.
    fss_point: The FSS location as a (longitude, latitude) tuple.
    fss_info: The |data.FssInformation| of the FSS.
  """
  # Get values of MCBSD,GCBSD,GFSS and LCBSD for each CBSD.
  for grant in grants_cbsds_oobe_info:
    if not grant['cbsd']['grants']:
      continue
    cbsd = data.constructCbsdGrantInfo(grant['cbsd']['registration'], None)
    # Get the MCBSD (ie the conducted OOBE power)
    mcbsd = grant['mcbsd']
    # Computes the path loss
    lcbsd, incidence_angle, _ = wf_itm.CalcItmPropagationLoss(
        cbsd.latitude,
        cbsd.longitude,
        cbsd.height_agl,
        fss_point[1],
        fss_point[0],
        fss_info.height_agl,
        cbsd.indoor_deployment,
        reliability=-1,
        freq_mhz=interf.FREQ_PROP_MODEL_MHZ)
    # The CBSD antenna gain towards FSS
    gcbsd = antenna.GetStandardAntennaGains(
        incidence_angle.hor_cbsd,
        cbsd.antenna_azimuth,
        cbsd.antenna_beamwidth,
        cbsd.antenna_gain)
    # The FSS antenna gain
    gfss = antenna.GetFssAntennaGains(
        incidence_angle.hor_rx,
        incidence_angle.ver_rx,
        fss_info.pointing_azimuth,
        fss_info.pointing_elevation,
        fss_info.max_gain_dbi)
    # The OOBE interference
    oobe_interference = mcbsd + gcbsd - lcbsd + gfss
    grant['oobe_interference'] = oobe_interference


def getMcbsdValue(grant):
  """Returns the MCBSD (OOBE emission mask) value in dB for a grant.

  MCBSD is the CBSD conducted power (in dBm) on the frequency segment,
  using the Tx mask of CBSD according to R0-DEV-05(e).

  Args:
    grant: A |GrantRecord| object as defined in SAS-SAS specification.
  """
  return (-13
          if grant['operationParam']['operationFrequencyRange']['highFrequency'] > 3690e6
          else -25)


def getGrantInfoListForFssOobeCalculation(cbsds):
  """Creates a list of grant infos based on the highest grant for FSS OOBE calculation.

  Args:
    cbsds: A list of |CbsdData| objects.
  Returns:
    A list of grant info dictionaries, each holding keys:
      'mcbsd': the MCBSD (CBSD conducted power) of the respective max frequency grant.
      'cbsd': the corresponding |CbsdData| object.
  """
  grants_cbsds_info_for_oobe_calculation = []
  for cbsd in cbsds:
    max_grant = max(cbsd['grants'],
                    key=lambda x:
                    x['operationParam']['operationFrequencyRange']['highFrequency'])
    grant_info = {
        'mcbsd': getMcbsdValue(max_grant),
        'cbsd': cbsd
    }
    grants_cbsds_info_for_oobe_calculation.append(grant_info)

  return grants_cbsds_info_for_oobe_calculation


def fssPurgeReferenceModel(sas_uut_fad, sas_test_harness_fads, fss_records):
  """Performs FSS purge model as described in R2-SGN-29.

  The FSS purge list model removes grants from the CBSD records of the FAD (Full Activity
  Dump) objects for both SAS UUT and SAS Test Harness.

  Args:
    sas_uut_fad: A |FullActivityDump| object containing the FAD records of SAS UUT.
    sas_test_harness_fads: A list of |FullActivityDump| objects containing the FAD records
      from SAS test harnesses.
    fss_records: A list of FSS record dictionary.
  """
  # Get the CBSD list from the FAD Object.
  cbsds = sas_uut_fad.getCbsdRecords()
  for fad in sas_test_harness_fads:
    cbsds.extend(fad.getCbsdRecords())

  grants_to_purged_for_all_fss = []
  ids_to_purge = set()

  for fss_record in fss_records:
    # If the FSS is of TT&C type then perform the FSS purge model for the FSS.
    if fss_record['ttc']:
      fss_point, fss_info, _ = data.getFssInfo(fss_record)
      neighboring_cbsds_with_grants = pre_iap_util.getFssNeighboringCbsdsWithGrants(
          cbsds, fss_point, 40)
      if neighboring_cbsds_with_grants:
        grants_to_purge_for_fss = generatePurgeListForFssPoint(
            neighboring_cbsds_with_grants, fss_point, fss_info)
        # Grants to be purged is updated checking against the cbsd id and grant id
        # to eliminate the duplicate entries
        grants_to_purged_for_all_fss.extend(
            purge_data for purge_data in grants_to_purge_for_fss
            if (purge_data.grant['id'], purge_data.cbsd['id']) not in ids_to_purge)
        ids_to_purge.update(
            [(purge_data.grant['id'], purge_data.cbsd['id'])
             for purge_data in grants_to_purge_for_fss])

  # Removing grant requests that are in the grants to purge list from the CBSDs.
  for purge_data in grants_to_purged_for_all_fss:
    purge_data.cbsd['grants'].remove(purge_data.grant)
