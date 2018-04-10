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
===================================================================================
  The main function is zonePurgeReferenceModel(). The grants from FAD
  CBSD objects of SAS UUT and SAS test harnesses are purged if the CBSD lies within
  a list of PPA areas or GWPZ areas or within 150 KMs from a list of FSSs and the
  grant frequency range overlaps with the protected entity's frequency range.
===================================================================================
"""
from reference_models.geo import vincenty
from reference_models.pre_iap_filtering import pre_iap_util

FSS_GWBL_PROTECTION_FREQ_RANGE = {'lowFrequency': 3650000000,
                             'highFrequency': 3700000000}


def zonePurgeReferenceModel(sas_uut_fad, sas_test_harness_fads,
                   ppa_records, pal_records, gwpz_records, fss_records):
  """ Entry method for PPA, GWPZ and FSS+GWBL purge reference model.

  CBSDs from the FAD objects of SAS UUT and SAS test harnesses that lie within the
  PPA area or GWPZ area or within 150 KMs from the FSS site will have their grant
  purged if the grant overlaps with frequency range of the protected entities.
  A frequency range of 3650-3700 MHz is considered for all the FSSs. It is assumed
  that the FSS records passed as input have a GWBL station within 150 KMs and
  thus the FSS exclusion zone is activated. Grants are purged from the input FADs.
  Args:
    sas_uut_fad: A FullActivityDump object containing the FAD records of SAS UUT.
    sas_test_harness_fads: A list of FullActivityDump objects containing the FAD records
      from SAS test harnesses.
    ppa_records: List of PPA record dictionaries.
    pal_records: List of PAL record dictionaries.
    gwpz_records: List of GWPZ record dictionaries.
    fss_records: List of FSS record dictionaries. All the FSSs in this list should have
      atleast one GWBL within 150KMs.
  """
  # Get the list of all CBSDs from the FAD objects of UUT and test harness
  cbsds = []
  cbsds.extend(sas_uut_fad.getCbsdRecords())
  for fad in sas_test_harness_fads:
    cbsds.extend(fad.getCbsdRecords()) 

  # Perform purge for each PPA
  for ppa_record in ppa_records:
    # Get all the CBSDs within the PPA polygon
    cbsds_within_ppa = pre_iap_util.getCbsdsWithinPolygon(cbsds, ppa_record['zone'])
    if cbsds_within_ppa:
      # Get all the cbsds that are not part of the PPA cluster list
      cbsds_not_part_of_ppa_cluster = pre_iap_util.getCbsdsNotPartOfPpaCluster(
                                                   cbsds_within_ppa, ppa_record)
      if cbsds_not_part_of_ppa_cluster:
        # Get the frequency of the PPA
        ppa_frequency_range = pre_iap_util.getPpaFrequencyRange(ppa_record, pal_records)
        # Purge the grants of CBSDs that are overlapping PPA frequency
        pre_iap_util.purgeOverlappingGrants(cbsds_not_part_of_ppa_cluster, ppa_frequency_range)

  # Perform purge for each GWPZ 
  for gwpz_record in gwpz_records:
   # Get the CBSDs that are witin the GWPZ polygon
   cbsds_within_gwpz = pre_iap_util.getCbsdsWithinPolygon(cbsds, gwpz_record['zone'])
   if cbsds_within_gwpz:
     # Purge the overlapping grants 
     pre_iap_util.purgeOverlappingGrants(cbsds_within_gwpz, gwpz_record['deploymentParam']\
                  ['operationParam']['operationFrequencyRange'])

  # Perform GWBL+FSS purge for each FSS
  for fss_record in fss_records:
    # Get the CBSDs that are present within 150kms of FSS entity
    cbsds_neighboring_fss = pre_iap_util.getFssNeighboringCbsdsWithGrants(cbsds, fss_record, 150)
    if cbsds_neighboring_fss:
      # Purge the overlapping grants 
      pre_iap_util.purgeOverlappingGrants(cbsds_neighboring_fss, FSS_GWBL_PROTECTION_FREQ_RANGE)

