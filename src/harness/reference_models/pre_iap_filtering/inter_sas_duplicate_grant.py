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

"""Inter-SAS Duplicate Grants removal.

This is a subset of the pre-IAP reference model which implements inter-SAS
duplicate CBSD removal. If a CBSD has registered with multiple SASs then the
CBSD is removed from the FAD objects of the respective SASs.
"""

from collections import defaultdict


def interSasDuplicateGrantPurgeReferenceModel(sas_uut_fad, sas_test_harness_fads):
  """ Removes CBSDs with grants from more than one SAS from FAD objects.

  Checks if a CBSD is registered with more than one SAS and removes the CBSD from
  all the FAD objects of all SASs (SAS UUT and SAS Test Harnesses).

  Args:
    sas_uut_fad: A |FullActivityDump| object containing the FAD records of SAS UUT.
    sas_test_harness_fads: A list of |FullActivityDump| objects containing the FAD records
      from SAS test harnesses.
  """
  # Get all the CBSD Reference ID of all CBSDs from UUT and SAS test Harness FAD objects
  cbsd_id_counts = defaultdict(int)
  for cbsd in sas_uut_fad.getCbsdRecords():
    cbsd_id_counts[cbsd['id']] += 1
  for fad in sas_test_harness_fads:
    for cbsd in fad.getCbsdRecords():
      cbsd_id_counts[cbsd['id']] += 1

  # Iterate through the UUT CBSD list and keep only the non duplicate CBSDs
  cbsds_to_keep = []
  for cbsd in sas_uut_fad.getCbsdRecords():
    if cbsd_id_counts[cbsd['id']] == 1:
      cbsds_to_keep.append(cbsd)
  sas_uut_fad.setCbsdRecords(cbsds_to_keep)

  # Iterate through the test harness CBSD list and keep only the non duplicate CBSDs
  for fad in sas_test_harness_fads:
    cbsds_to_keep = []
    for cbsd in fad.getCbsdRecords():
      if cbsd_id_counts[cbsd['id']] == 1:
        cbsds_to_keep.append(cbsd)
    fad.setCbsdRecords(cbsds_to_keep)
