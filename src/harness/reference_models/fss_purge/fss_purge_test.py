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
import sas_objects
from reference_models.fss_purge import fss_purge

class TestFssPurge(unittest.TestCase):

  def test_fss_purge_default(self):
    
   # TEST DATA
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
   fss_entity = json.load(
     open(os.path.join('testdata', 'fss_record_0.json')))
   
   fad_object_1 = sas_objects.FullActivityDump("","","","")
   fad_object_2 = sas_objects.FullActivityDump("","","","",)
   fad_object_3 = sas_objects.FullActivityDump("","","","",)
   fad_object_1.cbsd_records = [cbsd_0, cbsd_1]
   fad_object_2.cbsd_records = [cbsd_2, cbsd_3]
   fad_object_3.cbsd_records = [cbsd_4, cbsd_5]
   headroom = {'MgPpa': 2, 'MgGwpz': 2, 'MgCochannel': 2,
               'MgBlocking': 2, 'MgOobe': 2, 'MgEsc': 2}
   protected_entities = [{'fssRecords':[fss_entity]}]
   sas_uut_fad_object = fad_object_1
   sas_test_harness_fad_object = [fad_object_2, fad_object_3]
 
   print "================CBSD Grants passed as input======================"
   for records in sas_uut_fad_object.getCbsdRecords():
    for grants in records['grantRequests']:
       print " ",json.dumps(grants['id'])
   for fad in sas_test_harness_fad_object:
      for rec in fad.getCbsdRecords():
          for grants in rec['grantRequests']:
             print " ",json.dumps(grants['id'])
   print "===================================================================="

   for entity in protected_entities:
     if 'fssRecords' in entity:
       for fssRecord in entity['fssRecords']:
         fss_purge.fssPurgeModel(sas_uut_fad_object, sas_test_harness_fad_object, fssRecord, headroom['MgOobe'])

   print "================CBSD Grants received as output======================"
   for records in sas_uut_fad_object.getCbsdRecords():
    for grants in records['grantRequests']:
       print " ",json.dumps(grants['id'])
   for fad in sas_test_harness_fad_object:
      for rec in fad.getCbsdRecords():
          for grants in rec['grantRequests']:
             print " ",json.dumps(grants['id'])
   print "===================================================================="

if __name__ == '__main__':
  unittest.main()
