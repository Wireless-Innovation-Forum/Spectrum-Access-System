#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

import json
import os
import unittest
import full_activity_dump
from util import makePpaAndPalRecordsConsistent
from reference_models.pre_iap_filtering import zone_purge
from reference_models.pre_iap_filtering import pre_iap_util


class TestZonePurge(unittest.TestCase):

  def test_zone_PurgeModel_default(self):

   # TEST DATA
   cbsd_0 = json.load(
     open(os.path.join('testdata', 'testset1', 'cbsd_0.json')))
   cbsd_1 = json.load(
     open(os.path.join('testdata', 'testset1', 'cbsd_1.json')))
   cbsd_2 = json.load(
     open(os.path.join('testdata', 'testset1', 'cbsd_2.json')))
   cbsd_3 = json.load(
     open(os.path.join('testdata', 'testset1', 'cbsd_3.json')))
   cbsd_4 = json.load(
     open(os.path.join('testdata', 'testset1', 'cbsd_4.json')))
   cbsd_5 = json.load(
     open(os.path.join('testdata', 'testset1', 'cbsd_5.json')))
   # Load PPA record
   gwpz_record = json.load(
     open(os.path.join('testdata', 'testset1', 'gwpz_0.json')))
   ppa_record = json.load(
     open(os.path.join('testdata', 'testset1', 'ppa_0.json')))
   pal_record_0 = json.load(
     open(os.path.join('testdata', 'testset1', 'pal_0.json')))
   pal_record_1 = json.load(
     open(os.path.join('testdata', 'testset1', 'pal_1.json')))
   pal_record_2 = json.load(
     open(os.path.join('testdata', 'testset1', 'pal_2.json')))

   pal_record_list = [pal_record_0, pal_record_1, pal_record_2]
   fss_record = json.load(
     open(os.path.join('testdata', 'testset1', 'fss_0.json')))
   gwbl_record = json.load(
     open(os.path.join('testdata', 'testset1', 'gwbl_0.json')))
    
   ppa_record, pal_records = makePpaAndPalRecordsConsistent(ppa_record, pal_record_list,
                                                                  'test_user_1')
   ppa_record['ppaInfo']['cbsdReferenceId'] = ["cbsd_5", "cbsd_3"]
   fad_object_1 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_0, cbsd_1]})
   fad_object_2 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_2, cbsd_3]})
   fad_object_3 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_4, cbsd_5]})

   sas_uut_fad = fad_object_1
   sas_test_harness_fads = [fad_object_2, fad_object_3]

   protected_entities = {'gwpzRecords': [gwpz_record],'palRecords': pal_records,
                         'ppaRecords': [ppa_record], 'fssRecords':[fss_record],
                         'gwblRecords':[gwbl_record]}
   print "================CBSD Grants passed as input======================"
   initial_grants = 0
   for records in sas_uut_fad.getCbsdRecords():
    for grants in records['grants']:
      print " ",json.dumps(grants['id'])
      initial_grants = initial_grants + 1
   for fad in sas_test_harness_fads:
     for rec in fad.getCbsdRecords():
       for grants in rec['grants']:
         print " ",json.dumps(grants['id'])
         initial_grants = initial_grants + 1
   print "===================================================================="
   zone_purge.zonePurgeReferenceModel(sas_uut_fad, sas_test_harness_fads,\
             protected_entities['ppaRecords'], protected_entities['palRecords'],\
             protected_entities['gwpzRecords'], protected_entities['fssRecords'])
   print "================CBSD Grants received as output======================"
   final_grants = 0
   for records in sas_uut_fad.getCbsdRecords():
     for grants in records['grants']:
       print " ",json.dumps(grants['id'])
       final_grants = final_grants + 1
   for fad in sas_test_harness_fads:
     for rec in fad.getCbsdRecords():
       for grants in rec['grants']:
         print " ",json.dumps(grants['id'])
         final_grants = final_grants + 1
   print "===================================================================="
   self.assertLess(final_grants, initial_grants)

if __name__ == '__main__':
  unittest.main()
