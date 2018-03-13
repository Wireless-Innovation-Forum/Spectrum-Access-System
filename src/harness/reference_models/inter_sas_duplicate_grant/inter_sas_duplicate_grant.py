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
  This is a subset of the pre-IAP reference model which implements inter-SAS
  duplicate grant removal. If a CBSD has registered with multiple SASs then has
  overlapping grants then the overlapping grants will be removed from the FAD
  objects. The main function is interSasDuplicateGrantReferenceModel().
==================================================================================
"""


def interSasDuplicateGrantReferenceModel(sas_uut_fad, sas_test_harness_fads):
  """ Removes duplicate grants from FAD objects of SAS UUT and SAS test harnesses.

  Checks if a CBSD is registered with more than one SAS and removes the grants of the
  CBSD if the grant frequencies overlap either fully or partially. If all grants are
  removed from a CBSD then the CBSD is removed from the FAD Object.

  Args:
    sas_uut_fad: A FullActivityDump object containing the FAD records of SAS UUT.
    sas_test_harness_fads: A list of FullActivityDump objects containing the FAD records
      from SAS test harnesses.
  """

  # Creating list of cbsds from SAS UUT FAD object and SAS Test Harness FAD object
  cbsd_list = []
  for cbsds in sas_uut_fad.getCbsdRecords():
    cbsd_list.append(cbsds)
  for fad in sas_test_harness_fads:
    for cbsds in fad.getCbsdRecords():
      cbsd_list.append(cbsds)

  # Iterate through each CBSD and check if the FCC ID and SerialNumber matches another CBSD
  # If yes then check whether their grants overlap and mark the overlapping grants as duplicate.
  for index_a, cbsd_a in enumerate(cbsd_list):
    for index_b, cbsd_b in enumerate(cbsd_list):

        # Check that the objects we compare are different and not of the same index.
      if index_a != index_b:

           # Check if fccId and cbsdSerialNumber match
        if ((cbsd_a['registrationRequest']['fccId'] ==
             cbsd_b['registrationRequest']['fccId']) and
             (cbsd_a['registrationRequest']['cbsdSerialNumber'] ==
             cbsd_b['registrationRequest']['cbsdSerialNumber'])):

          # Check for overlapping grantrequests
          for grant_in_a in cbsd_a['grantRequests']:
            for grant_in_b in cbsd_b['grantRequests']:
              if checkForOverlappingGrants(grant_in_a,grant_in_b):
                grant_in_b["duplicate_flag"] = "TRUE"

  # Remove the grants marked as duplicate. If all grants of a CBSD are removed then remove the CBSD.
  cbsds_to_remove = []
  for cbsd in cbsd_list:
    grants_to_remove = []
    for grants in cbsd['grantRequests']:
      if "duplicate_flag" in grants:
        grants_to_remove.append(grants)
    for grant in grants_to_remove:
      cbsd['grantRequests'].remove(grant)
      if not cbsd['grantRequests']:
        cbsds_to_remove.append(cbsd)

  for cbsd in cbsds_to_remove:
    cbsd_list.remove(cbsd)

def checkForOverlappingGrants(grant_a, grant_b):
  """Checks if the frequency ranges of two grants are overlapping."""

  low_frequency_a = grant_a['operationParam']['operationFrequencyRange']['lowFrequency']
  high_frequency_a = grant_a['operationParam']['operationFrequencyRange']['highFrequency']
  low_frequency_b = grant_b['operationParam']['operationFrequencyRange']['lowFrequency']
  high_frequency_b = grant_b['operationParam']['operationFrequencyRange']['highFrequency']

  # If the low or high frequency of grant_a falls within the frequency range of grant_b
  # then the grants are overlapping.
  if (low_frequency_a <= low_frequency_b < high_frequency_a) or \
      (low_frequency_a < high_frequency_b <= high_frequency_a):
    return True
  return False

