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
from datetime import datetime, timedelta

class FullActivityDumpMessageTestcase(sas_testcase.SasTestCase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()

    def tearDown(self):
        pass

    def assertGrantRecord(self, grant_record, grant_request, grant_response):
        self.assertEqual(grant_record['id'],grant_response['grantId'])
        if grant_record['operationParam'] != null :
            self.assertEqual(grant_record['operationParam']['maxEirp'],\
                             grant_request['operationParam']['maxEirp'])    
            self.assertEqual(grant_record['operationParam'], ['operationFrequencyRange']['lowFrequency'],\
                             grant_request['operationParam']['operationFrequencyRange']['lowFrequency'])
            self.assertEqual(grant_record['operationParam']['operationFrequencyRange']['highFrequency'],\
                             grant_request['operationParam']['operationFrequencyRange']['highFrequency'])
        self.assertEqual(grant_record['requestedOperationParam']['maxEirp'],\
                         grant_request['requestedOperationParam']['maxEirp'])    
        self.assertEqual(grant_record['requestedOperationParam']['operationFrequencyRange']\
                         ['lowFrequency'],grant_request['requestedOperationParam']['operationFrequencyRange']['lowFrequency'])
        self.assertEqual(grant_record['requestedOperationParam']\
                         ['operationFrequencyRange']['highFrequency'], grant_request['requestedOperationParam']\
                         ['operationFrequencyRange']['highFrequency'])
        self.assertEqual(grant_record['channelType'], grant_response['channelType'])
        self.assertEqual(grant_record['grantExpireTime'], grant_response['grantExpireTime'])
        self.assertEqual(false, grant_record['terminated']) 
		
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
        grants_to_request = [grant_a, grant_c]
        grant_request = {'grantRequest': grants_to_request}
        # Send grant requests
        grant_response = self._sas.Grant(request)['grantResponse']
        grant_ids = []
        for resp in grant_response:
            grant_ids.append(resp['grantId'])
        del request
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
        for activity_dump_file in response['files']:
            # Verify the record type
            # Verify the response files with ActivityDumpFile.schema.json Object schema
            self.assertContainsRequiredFields("ActivityDumpFile.schema.json", activity_dump_file)
            # Get json data from url
            data = self._sas.DownloadFile(activity_dump_file['url'])
            if activity_dump_file['recordType'] == 'cbsd':
                 # Verify that everything in the full dump matches a cbsd or grant created at the beginning
                for record in data['recordData']:
                # Verify the response files with CbsdData.schema.json Object schema
                    self.assertContainsRequiredFields("CbsdData.schema.json", record)
                    self.assertTrue(record['registration']['fccId'] in (device_a['fccId'], device_c['fccId']))
                # Verify all the previous activities on CBSDs and Grants exist in the dump files    
                for index, device in enumerate([device_a, device_c]):
                    record_id = 'cbsd/'+ device['fccId']+'/'+ hashlib.sha1(device['cbsdSerialNumber']).hexdigest()
                    cbsd_record = [record['registration'] for record in data['recordData'] if record['id'] == record_id]
                    self.assertEqual(first_cbsd['cbsdCategory'],second_cbsd['cbsdCategory'])
                    self.assertEqual(device['airInterface']['radioTechnology'],\
                                     cbsd_record['airInterface']['radioTechnology'])
                    self.assertEqual(device['installationParam']['latitude'],\
                                     cbsd_record['installationParam']['latitude'])
                    self.assertEqual(device['installationParam']['longitude'],\
                                     cbsd_record['installationParam']['longitude'])
                    self.assertEqual(device['installationParam']['height'],\
                                     cbsd_record['installationParam']['height'])
                    self.assertEqual(device['installationParam']['heightType'], \
                                     cbsd_record['installationParam']['heightType'])
                    self.assertEqual(device['installationParam']['indoorDeployment'], \
                                     cbsd_record['installationParam']['indoorDeployment'])
                    self.assertEqual(device['installationParam']['antennaGain'], \
                                     cbsd_record['installationParam']['antennaGain'])                           
                    # Get grants by cbsd_id
                    grants_of_cbsd = [cbsd['grants'] for cbsd in data['recordData'] if cbsd['id'] == record_id]
                    self.assertEqual(grants_of_cbsd[0][0]['id'], (grant_ids[index]))
                    self.assertGrantRecord(record['grants'][0], grants_to_request[index], grant_response[index])
            elif activity_dump_file['recordType'] == 'esc_sensor':
                self.assertEqual(1, len(data['recordData']))
                # Verify the response file of Esc Sensor
                self.assertContainsRequiredFields("EscSensorRecord.schema.json", data['recordData'][0])
                self.assertDictEqual(esc_sensor_record, data['recordData'][0])
            else:
                self.assertEqual(activity_dump_file['recordType'],'zone')
                self.assertEqual(1, len(data['recordData']))
                # Verify the response file of PPA
                self.assertContainsRequiredFields("zoneData.schema.json", data['recordData'][0])
                self.assertDictEqual(ppa_record, data['recordData'][0] )
                 
                                                  