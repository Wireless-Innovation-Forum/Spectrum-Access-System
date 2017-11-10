#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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
import sas
from  util import winnforum_testcase, makePpaAndPalRecordsConsistent
import sas_testcase
import hashlib
from datetime import datetime, timedelta

class FullActivityDumpMessageTestcase(sas_testcase.SasTestCase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()

    def tearDown(self):
        pass
    
    def assertCbsdRecord(self, registration_request, grant_request, grant_response, recordData):
        for index, device in enumerate(registration_request):
            record_id = 'cbsd/'+ device['fccId']+'/'+ hashlib.sha1(device['cbsdSerialNumber']).hexdigest()
            cbsd_record = [record['registration'] for record in recordData if record['id'] == record_id]
            self.assertEqual(1, len(cbsd_record))
            self.assertEqual(device['cbsdCategory'], cbsd_record[0]['cbsdCategory'])
            self.assertEqual(device['fccId'], cbsd_record[0]['fccId'])
            self.assertEqual(device['airInterface']['radioTechnology'],\
                             cbsd_record[0]['airInterface']['radioTechnology'])
            self.assertEqual(device['installationParam']['latitude'],\
                             cbsd_record[0]['installationParam']['latitude'])
            self.assertEqual(device['installationParam']['longitude'],\
                             cbsd_record[0]['installationParam']['longitude'])
            self.assertEqual(device['installationParam']['height'],\
                             cbsd_record[0]['installationParam']['height'])
            self.assertEqual(device['installationParam']['heightType'], \
                             cbsd_record[0]['installationParam']['heightType'])
            self.assertEqual(device['installationParam']['indoorDeployment'], \
                             cbsd_record[0]['installationParam']['indoorDeployment'])
            self.assertEqual(device['installationParam']['antennaGain'], \
                             cbsd_record[0]['installationParam']['antennaGain'])     
            self.assertEqual(device['installationParam']['antennaAzimuth'], \
                             cbsd_record[0]['installationParam']['antennaAzimuth'])        
            self.assertEqual(device['installationParam']['antennaDowntilt'], \
                             cbsd_record[0]['installationParam']['antennaDowntilt'])       
            self.assertEqual(device['installationParam']['antennaBeamwidth'], \
                             cbsd_record[0]['installationParam']['antennaBeamwidth'])    
                         
            # Get grants by cbsd_id
            grants_of_cbsd = [cbsd['grants'] for cbsd in recordData if cbsd['id'] == record_id]
            self.assertEqual(1, len(grants_of_cbsd))
            self.assertTrue('id' in grants_of_cbsd[0])
            # Verify the Grant Of the Cbsd
            if grants_of_cbsd[0]['requestedOperationParam'] is not None :
                self.assertEqual(grants_of_cbsd[0]['requestedOperationParam']['maxEirp'],\
                             grant_request[index]['operationParam']['maxEirp'])    
                self.assertEqual(grants_of_cbsd[0]['requestedOperationParam']['operationFrequencyRange']\
                                 ['lowFrequency'], grant_request[index]['operationParam']['operationFrequencyRange']['lowFrequency'])
                self.assertEqual( grants_of_cbsd[0]['requestedOperationParam']\
                                 ['operationFrequencyRange']['highFrequency'], grant_request[index]['operationParam']\
                                 ['operationFrequencyRange']['highFrequency']) 
                
            self.assertEqual( grants_of_cbsd[0]['operationParam']['maxEirp'],\
                             grant_request[index]['operationParam']['maxEirp'])    
            self.assertEqual( grants_of_cbsd[0]['operationParam']['operationFrequencyRange']['lowFrequency'],\
                             grant_request[index]['operationParam']['operationFrequencyRange']['lowFrequency'])
            self.assertEqual(grants_of_cbsd[0]['operationParam']['operationFrequencyRange']['highFrequency'],\
                             grant_request[index]['operationParam']['operationFrequencyRange']['highFrequency'])
            self.assertEqual(grants_of_cbsd[0]['channelType'], grant_response[index]['channelType'])
            self.assertEqual( grants_of_cbsd[0]['grantExpireTime'], grant_response[index]['grantExpireTime'])
            self.assertEqual(False, grants_of_cbsd[0]['terminated'])   
    @winnforum_testcase
    def test_WINNF_FT_S_FAD_1(self):
        """ This test verifies that a SAS UUT can successfully respond to a full
             activity dump request from a SAS Test Harness
			
		SAS UUT approves the request and responds,
		with correct content and format for both dump message and files 
          """
        # STEP 1
        # register devices
        device_a = json.load(
            open(os.path.join('testcases', 'testdata', 'device_a.json')))
        device_c = json.load(
            open(os.path.join('testcases', 'testdata', 'device_c.json')))
        cbsd_ids = self.assertRegistered([device_a, device_c])
        # Create grant requests
        grant_a = json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_c = json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_a['cbsdId'] = cbsd_ids[0]
        grant_c['cbsdId'] = cbsd_ids[1]
        # Set Grants 
        grant_a['operationParam']['operationFrequencyRange'] = {
            'lowFrequency': 3620000000.0,
            'highFrequency': 3630000000.0
        }
        grant_c['operationParam']['operationFrequencyRange'] = {
            'lowFrequency': 3640000000.0,
            'highFrequency': 3650000000.0
        }
        grant_request = [grant_a, grant_c]
        request = {'grantRequest': grant_request}     
        # Send grant requests
        grant_response = self._sas.Grant(request)['grantResponse']
        grant_ids = []
        for resp in grant_response:
            self.assertEqual(resp['response']['responseCode'], 0)
            grant_ids.append(resp['grantId'])
        # STEP 2
        # Inject PPA
        pal_low_frequency = 3550000000.0
        pal_high_frequency = 3560000000.0
        pal_record = json.load(
          open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
        ppa_record = json.load(
          open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
        ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,
                                                                [pal_record],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                device_a['userId'])
        self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
        self._sas_admin.InjectZoneData({'record': ppa_record})
        # Inject Esc Sensor
        esc_sensor_record = json.load(
          open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
        self._sas_admin.InjectEscSensorDataRecord({'record': esc_sensor_record})
        # STEP 3
        self._sas_admin.TriggerFullActivityDump()
        # STEP 4
        response = self._sas.GetFullActivityDump()
        # STEP 5
        self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
        # STEP 6 AND CHECK
        self.assertEqual()
        self.assertGreaterEqual(3, len(response['files']))
        self.assertLessEqual(2 + len(cbsd_ids), len(response['files']))
        cbsd_dump_files = [dump_file for dump_file in response['files'] if dump_file['recordType'] ==  'cbsd']
        esc_sensor_dump_file = [dump_file for dump_file in response['files'] if dump_file['recordType'] ==  'esc_sensor']
        zone_dump_file = [dump_file for dump_file in response['files'] if dump_file['recordType'] ==  'zone']        
        # Verify the record type
        # Verify the response files with ActivityDumpFile.schema.json Object schema
        for dump_file in [esc_sensor_dump_file, zone_dump_file]:
            self.assertContainsRequiredFields("ActivityDumpFile.schema.json",
                                               dump_file[0])
            self.assertEqual(1, len(dump_file))
        self.assertGreaterEqual(1, len(cbsd_dump_files))
        self.assertLessEqual(len(cbsd_ids), len(cbsd_dump_files))
        data = []
        for dump_file in cbsd_dump_files:
            self.assertContainsRequiredFields("ActivityDumpFile.schema.json",
                                               dump_file)
            data.append(self._sas.DownloadFile(dump_file['url']))
        # Get json data from url
        #for dump_file in cbsd_dump_files    
        # Verify that everything in the full dump matches a cbsd or grant created at the beginning
        cbsd_records = [cbsd_record['recordData'] for cbsd_record in data]
        for record in cbsd_records:
            # Verify the response files with CbsdData.schema.json Object schema
            self.assertContainsRequiredFields("CbsdData.schema.json", record)
            self.assertTrue(record['registration']['fccId'] in (device_a['fccId'], device_c['fccId']))
        # Verify all the previous activities on CBSDs and Grants exist in the dump files
        self.assertCbsdRecord([device_a, device_c], grant_request, grant_response, cbsd_records)
        del data
        data = self._sas.DownloadFile(esc_sensor_dump_file[0]['url'])
        # Verify that everything in the full dump matches a cbsd or grant created at the beginning
        for record in data['recordData']:
            self.assertEqual(1, len(data['recordData']))
            # Verify the response file of Esc Sensor
            self.assertContainsRequiredFields("EscSensorRecord.schema.json", data['recordData'][0])
            self.assertDictEqual(esc_sensor_record, data['recordData'][0])    
        del data  
        data = self._sas.DownloadFile(zone_dump_file[0]['url'])
        for record in data['recordData']:
            self.assertEqual(1, len(data['recordData']))
            # Verify the response file of PPA
            self.assertContainsRequiredFields("zoneData.schema.json", data['recordData'][0])
            self.assertDictEqual(ppa_record, data['recordData'][0])