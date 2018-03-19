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
  This is the Pre-IAP reference model which implements calling of 4 sub reference
  modules in to ensure the checks to be done before sending to the IAP calculation.
==================================================================================
"""

from reference_models.fss_purge import fss_purge
from reference_models.inter_sas_duplicate_grant import inter_sas_duplicate_grant


def performPreIapFiltering(protected_entities, uut_fad_object, test_harness_fad_object):
  """ The main function that invokes all pre-IAP filtering models.

  The grants/CBSDs to be purged are removed from the input parameters.
  
  Args:
    protected_entities: : A dictionary containing the list of protected entities. The key
      is a protected enity type and the value is a list of corresponding protected
      entity records. The format is {'entity_name':[record1, record2]}.
    uut_fad_object: A FullActivityDump object containing the FAD records of SAS UUT.
    test_harness_fad_objects: A list of FullActivityDump objects containing the FAD records
      from SAS test harnesses.
  """    

  # Invoke Inter SAS duplicate grant purge list reference model
  inter_sas_duplicate_grant.interSasDuplicateGrantReferenceModel\
                                (uut_fad_object, test_harness_fad_object)

  # Invoke PPA, EXZ, GWPZ, and FSS+GWBL purge list reference models

  # Invoke FSS purge list reference model
  for entity in protected_entities:
    if 'fssRecords' in entity:
      for fss_record in entity['fssRecords']:
        fss_purge.fssPurgeModel(uut_fad_object, test_harness_fad_object, fss_record)

