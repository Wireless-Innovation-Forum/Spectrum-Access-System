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
import fss_purge
from reference_models.inter_sas_duplicate_grant import inter_sas_duplicate_grant
class TestFssPurge(unittest.TestCase):

  def test_fss_purge_default(self):
    
   # TEST DATA
   cbsd_0 = json.load(
     open(os.path.join('testdata', 'testset2', 'cbsd_0.json')))
   cbsd_1 = json.load(
     open(os.path.join('testdata', 'testset2', 'cbsd_1.json')))
   cbsd_2 = json.load(
     open(os.path.join('testdata', 'testset2', 'cbsd_2.json')))
   cbsd_3 = json.load(
     open(os.path.join('testdata', 'testset2', 'cbsd_3.json')))
   cbsd_4 = json.load(
     open(os.path.join('testdata', 'testset2', 'cbsd_4.json')))
   cbsd_5 = json.load(
     open(os.path.join('testdata', 'testset2', 'cbsd_5.json')))
   fss_entity = json.load(
     open(os.path.join('testdata', 'testset2', 'fss_record_0.json')))
   
   fad_object_1 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_0, cbsd_1]})
   fad_object_2 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_2, cbsd_3]})
   fad_object_3 = full_activity_dump.FullActivityDump({'cbsd': [cbsd_4, cbsd_5]})
   protected_entities = [{'fssRecords':[fss_entity]}]
   sas_uut_fad_object = fad_object_1
   sas_test_harness_fad_object = [fad_object_2, fad_object_3]
 
   print "================CBSD Grants passed as input======================"
   for records in sas_uut_fad_object.getCbsdRecords():
    for grants in records['grants']:
      print " ",json.dumps(grants['id'])
   for fad in sas_test_harness_fad_object:
     for rec in fad.getCbsdRecords():
       for grants in rec['grants']:
         print " ",json.dumps(grants['id'])
   print "===================================================================="

   for entity in protected_entities:
     if 'fssRecords' in entity:
       fss_purge.fssPurgeReferenceModel(sas_uut_fad_object, sas_test_harness_fad_object, entity['fssRecords'])

   print "================CBSD Grants received as output======================"
   for records in sas_uut_fad_object.getCbsdRecords():
     for grants in records['grants']:
       print " ",json.dumps(grants['id'])
   for fad in sas_test_harness_fad_object:
      for rec in fad.getCbsdRecords():
        for grants in rec['grants']:
          print " ",json.dumps(grants['id'])
   print "===================================================================="

if __name__ == '__main__':
  unittest.main()
