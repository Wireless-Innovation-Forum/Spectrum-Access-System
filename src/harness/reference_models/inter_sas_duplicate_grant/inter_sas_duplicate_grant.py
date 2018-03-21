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
  duplicate CBSD removal. If a CBSD has registered with multiple SASs then the
  CBSD is removed from the FAD objects of the respective SASs. The main function
  is interSasDuplicateGrantReferenceModel().
==================================================================================
"""
import copy
from collections import Counter
def interSasDuplicateGrantReferenceModel(input_sas_uut_fad, input_sas_test_harness_fads):
  """ Removes duplicate grants from FAD objects of SAS UUT and SAS test harnesses.

  Checks if a CBSD is registered with more than one SAS and removes the grants of the
  CBSD if the grant frequencies overlap either fully or partially. If all grants are
  removed from a CBSD then the CBSD is removed from the FAD Object.

  Args:
    input_sas_uut_fad: A FullActivityDump object containing the FAD records of SAS UUT.
    input_sas_test_harness_fads: A list of FullActivityDump objects containing the FAD records
      from SAS test harnesses.
  Returns:
    sas_uut_fad: A FullActivityDump object containing the FAD record of SAS UUT after purged grants removed.    
    sas_test_harness_fads: A list of FullActivityDump object containing the FAD record of 
      SAS test harness after purged grants removed.    
  """
  sas_uut_fad = copy.deepcopy(input_sas_uut_fad)
  sas_test_harness_fads = copy.deepcopy(input_sas_test_harness_fads)

  all_cbsd_ids= []
  # Get all the CBSD Reference ID of all CBSDs from UUT and SAS test Harness FAD objects
  for cbsd in sas_uut_fad.getCbsdRecords():
    all_cbsd_ids.append(cbsd['id'])
  for fad in sas_test_harness_fads:
    for cbsd in fad.getCbsdRecords():
      all_cbsd_ids.append(cbsd['id'])
  cbsds_ids_to_remove = [str(k) for k, v in Counter(all_cbsd_ids).iteritems() if v > 1]

  indices_in_sas_uut_to_remove = []
  # Iterate through the UUT CBSD list and find the indices of the duplicate CBSDs
  sas_uut_cbsd = sas_uut_fad.getCbsdRecords()
  for index,cbsd in enumerate(sas_uut_cbsd):
    if cbsd['id'] in cbsds_ids_to_remove:
      indices_in_sas_uut_to_remove.append(index)
  indices_in_sas_uut_to_remove.sort(reverse=True)

  # Remove the CBSD at the index position
  for index in indices_in_sas_uut_to_remove:
    sas_uut_cbsd.pop(index)

  sas_test_harness_cbsds = []

  # Iterate through the SAS Test Harness CBSD list and find the indices of the duplicate CBSDs
  indices_in_sas_test_harness_to_remove = []
  for fad in sas_test_harness_fads:
    indices_in_sas_test_harness_to_remove = []
    sas_test_harness_cbsds = fad.getCbsdRecords()
    for index,cbsd in enumerate(sas_test_harness_cbsds):
      if cbsd['id'] in cbsds_ids_to_remove:
        indices_in_sas_test_harness_to_remove.append(index)
    indices_in_sas_test_harness_to_remove.sort(reverse=True)

    # Remove the CBSD at the index position.
    for index in indices_in_sas_test_harness_to_remove:
      sas_test_harness_cbsds.pop(index)
  return sas_uut_fad,sas_test_harness_fads

