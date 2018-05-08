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
  This is the main Pre-IAP reference model which invokes the sub pre-IAP reference
  models to filter out grants and CBSDs before IAP model is invoked.
==================================================================================
"""
from reference_models.pre_iap_filtering import fss_purge
from reference_models.pre_iap_filtering import inter_sas_duplicate_grant
from reference_models.pre_iap_filtering import zone_purge
from reference_models.pre_iap_filtering import pre_iap_util


def preIapReferenceModel(protected_entities, sas_uut_fad, sas_test_harness_fads):
  """ The main function that invokes all pre-IAP filtering models.
  The grants/CBSDs to be purged are removed from the input parameters.

  Args:
    protected_entities: A dictionary containing the list of protected entities. The key
      is a protected enity type and the value is a list of corresponding protected
      entity records. The format is {'entityName':[record1, record2]}.
    sas_uut_fad: A FullActivityDump object containing the FAD records of SAS UUT.
    sas_test_harness_fads: A list of FullActivityDump objects containing the FAD records
      from SAS test harnesses.
  """

  # Invoke Inter SAS duplicate grant purge list reference model
  inter_sas_duplicate_grant.interSasDuplicateGrantPurgeReferenceModel(sas_uut_fad,
                                                                      sas_test_harness_fads)

  # Invoke PPA, EXZ, GWPZ, and FSS+GWBL purge list reference models
  if 'gwblRecords' in protected_entities and 'fssRecords' in protected_entities:
    list_of_fss_neighboring_gwbl = pre_iap_util.getFssNeighboringGwbl(
        protected_entities['gwblRecords'],
        protected_entities['fssRecords'])
    zone_purge.zonePurgeReferenceModel(sas_uut_fad,
                                       sas_test_harness_fads,
                                       protected_entities['ppaRecords'],
                                       protected_entities['palRecords'],
                                       protected_entities['gwpzRecords'],
                                       list_of_fss_neighboring_gwbl)

  # Invoke FSS purge list reference model
  if 'fssRecords' in protected_entities:
    fss_purge.fssPurgeReferenceModel(sas_uut_fad, sas_test_harness_fads,
                                     protected_entities['fssRecords'])

