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
import full_activity_dump
import json
import os
import fss_purge
from reference_models.inter_sas_duplicate_grant import inter_sas_duplicate_grant
import zone_purge
import pre_iap_util
from util import makePpaAndPalRecordsConsistent

FSS_GWBL_PROTECTION_DISTANCE = 150
cbsd_0 = json.load(
      open(os.path.join('testdata', 'cbsd_0.json')))
cbsd_1 = json.load(
    open(os.path.join('testdata', 'cbsd_1.json')))
cbsd_2 = json.load(
    open(os.path.join('testdata', 'cbsd_2.json')))
cbsd_3 = json.load(
    open(os.path.join('testdata', 'cbsd_3.json')))
cbsd_4 = json.load(
    open(os.path.join('testdata', 'cbsd_4.json')))
cbsd_5 = json.load(
    open(os.path.join('testdata', 'cbsd_5.json')))
fss_entity_0 = json.load(
    open(os.path.join('testdata', 'fss_0.json')))
fss_entity_1 = json.load(
    open(os.path.join('testdata', 'fss_1.json')))
gwpz_record = json.load(
  open(os.path.join('testdata', 'gwpz_0.json')))
ppa_record = json.load(
  open(os.path.join('testdata', 'ppa_0.json')))
pal_record = json.load(
  open(os.path.join('testdata', 'pal_0.json')))
gwbl_record = json.load(
  open(os.path.join('testdata', 'gwbl_0.json')))

fd1 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_0, cbsd_1]})
fd2 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_2, cbsd_3]})
fd3 = full_activity_dump.FullActivityDump({'cbsd':[cbsd_4,cbsd_5]})
headroom = {'MgPpa': 2, 'MgGwpz': 2, 'MgCochannel': 2,
                         'MgBlocking': 2, 'MgOobe': 2, 'MgEsc': 2}
pal_low_frequency = pal_record['channelAssignment']['primaryAssignment']['lowFrequency']
pal_high_frequency = pal_record['channelAssignment']['primaryAssignment']['highFrequency']
ppa_record, pal_records = makePpaAndPalRecordsConsistent(ppa_record,
                                                             [pal_record],
                                                             'test_user_1')
sas_uut_fad = fd1
sas_test_harness_fads = [fd2,fd3]
protected_entities = {'fssRecords':[fss_entity_0, fss_entity_1], 'gwpzRecords':[gwpz_record],
    'gwblRecords':[gwbl_record], 'ppaRecords':[ppa_record], 'palRecords':pal_records}
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

  print "================CBSD Grants passed as input======================"
  for records in sas_uut_fad.getCbsdRecords():
   for grants in records['grants']:
     print " ",json.dumps(grants['id'])
  for fad in sas_test_harness_fads:
    for rec in fad.getCbsdRecords():
      for grants in rec['grants']:
        print " ",json.dumps(grants['id'])
  print "===================================================================="
  # Invoke Inter SAS duplicate grant purge list reference model
  inter_sas_duplicate_grant.interSasDuplicateGrantPurgeReferenceModel\
                                               (sas_uut_fad, sas_test_harness_fads)

  # Invoke PPA, EXZ, GWPZ, and FSS+GWBL purge list reference models
  fss_neighboring_gwbl = pre_iap_util.getFssNeighboringGwbl(protected_entities['gwblRecords']
                              ,protected_entities['fssRecords'], FSS_GWBL_PROTECTION_DISTANCE)
  zone_purge.zonePurgeReferenceModel(sas_uut_fad,
      sas_test_harness_fads, protected_entities['ppaRecords'], 
      protected_entities['palRecords'], protected_entities['gwpzRecords'], 
      fss_neighboring_gwbl) 

  # Invoke FSS purge list reference model
  if 'fssRecords' in protected_entities:
    fss_purge.fssPurgeReferenceModel(sas_uut_fad, sas_test_harness_fads,
                                protected_entities['fssRecords'])

  print "================CBSD Grants came as   output====================="
  for records in sas_uut_fad.getCbsdRecords():
   for grants in records['grants']:
     print " ",json.dumps(grants['id'])
  for fad in sas_test_harness_fads:
    for rec in fad.getCbsdRecords():
      for grants in rec['grants']:
        print " ",json.dumps(grants['id'])
  print "===================================================================="
preIapReferenceModel(protected_entities,sas_uut_fad,sas_test_harness_fads)
