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
import hashlib

class FullActivityDumpMessageTestcase(sas_testcase.SasTestCase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()

    def tearDown(self):
        pass
	
    def assertCbsdRecordEqual(self, first_cbsd, second_cbsd):
        self.assertEqual(first_cbsd['cbsdCategory'],second_cbsd['cbsdCategory'])
        self.assertEqual(first_cbsd['airInterface']['radioTechnology'],second_cbsd['airInterface']['radioTechnology'])
        self.assertEqual(first_cbsd['installationParam']['latitude'],second_cbsd['installationParam']['latitude'])
        self.assertEqual(first_cbsd['installationParam']['longitude'],second_cbsd['installationParam']['longitude'])
        self.assertEqual(first_cbsd['installationParam']['height'],second_cbsd['installationParam']['height'])
        self.assertEqual(first_cbsd['installationParam']['heightType'],second_cbsd['installationParam']['heightType'])
        self.assertEqual(first_cbsd['installationParam']['indoorDeployment'],second_cbsd['installationParam']['indoorDeployment'])
        self.assertEqual(first_cbsd['installationParam']['antennaGain'],second_cbsd['installationParam']['antennaGain'])
        

    def assertGrantRecord(self, grant_record, grant_request, grant_response):
        self.assertEqual(grant_record['id'],grant_response['grantId'])
        if grant_record['operationParam'] != null :
            self.assertEqual(grant_record['operationParam']['maxEirp'], grant_request['operationParam']['maxEirp'])    
            self.assertEqual(grant_record['operationParam']['operationFrequencyRange']['lowFrequency'], grant_request['operationParam']['operationFrequencyRange']['lowFrequency'])
            self.assertEqual(grant_record['operationParam']['operationFrequencyRange']['highFrequency'], grant_request['operationParam']['operationFrequencyRange']['highFrequency'])
        self.assertEqual(grant_record['requestedOperationParam']['maxEirp'], grant_request['requestedOperationParam']['maxEirp'])    
        self.assertEqual(grant_record['requestedOperationParam']['operationFrequencyRange']['lowFrequency'], grant_request['requestedOperationParam']['operationFrequencyRange']['lowFrequency'])
        self.assertEqual(grant_record['requestedOperationParam']['operationFrequencyRange']['highFrequency'], grant_request['requestedOperationParam']['operationFrequencyRange']['highFrequency'])
        self.assertEqual(grant_record['channelType'], grant_response['channelType'])
        self.assertEqual(grant_record['grantExpireTime'], grant_response['grantExpireTime'])
        self.assertEqual(false, grant_record['terminated']) 
		
    @winnforum_testcase
    def test_WINNF_FT_S_FAD_1(self):
        """
        Purpose : This test verifies that a SAS UUT can successfully respond to a full
                  activity dump request from a SAS Test Harness

        Result:S

          TS version : BASED_ON_V0.0.0-r5.0 (15 September 2017)

          Test version : 0.1
          """
        # STEP 1
        """
        CBSD Test Harness registers 2 CBSDs with the SAS UUT, and follows the CBSD Grant Request
        procedure to obtain grants for those CBSDs.
        """
        # register devices
        device_a = json.load(
            open(os.path.join('testcases', 'testdata', 'device_a.json')))
        device_c = json.load(
            open(os.path.join('testcases', 'testdata', 'device_c.json')))
        # Register the devices and assert the Response
        cbsd_ids = self.assertRegistered([device_a, device_c])
        # Create grant requests
        grant_0 = json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_1 = json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_0['cbsdId'] = cbsd_ids[0]
        grant_1['cbsdId'] = cbsd_ids[1]
        # Request for non-overlapping frequency spectrum
        grant_0['operationParam']['operationFrequencyRange'] = {
            'lowFrequency': 3620000000.0,
            'highFrequency': 3630000000.0
        }
        grant_1['operationParam']['operationFrequencyRange'] = {
            'lowFrequency': 3640000000.0,
            'highFrequency': 3650000000.0
        }
        request = {'grantRequest': [grant_0, grant_1]}
        # Send grant requests
        grant_response = self._sas.Grant(request)['grantResponse']
        # Check registration response
        grant_ids = []
        for resp in grant_response:
            grant_ids.append(resp['grantId'])
        del request
        
        # STEP 2
        """
        Use Test Harness to inject a PPA with ZONE_ID = X, and ESC Sensor data with ESC ID = Y, into SAS UUT
        """
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
        ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[1]]
        self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
        self._sas_admin.InjectZoneData({'record': ppa_record})
        # Inject Esc Sensor
        esc_sensor_record = json.load(
          open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
        self._sas_admin.InjectEscSensorDataRecord({'record': esc_sensor_record})
        # STEP 3
        """
        Trigger the SAS UUT to generate the activity dump.
        """
        self._sas_admin.TriggerFullActivityDump()
        # STEP 4
        """
        SAS Test Harness establishes a TLS session with SAS UUT.  SAS Test Harness sends a correctly-formatted
        full activity dump request to SAS UUT, of the form: GET $BASE_URL/dump.
        """
        response = self._sas.GetFullActivityDump()
        # STEP 5
        """
        SAS UUT approves the request and responds with a Full Activity Dump message.
        - The message includes all required fields, and all fields are syntactically correct.
        - HTTP status code shall be 200 (SUCCESS).
        """
        self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
        generation_date_time = datetime.strptime(response['generationDateTime'],
                                          '%Y-%m-%dT%H:%M:%SZ')
        # STEP 6
        """
        SAS test harness retrieves the individual files referenced in the FullActivityDump message.
        """
        # CHECK
        """
        The files obtained in Step 6 collectively reflect all of the activity in Step 1 and 2 and use
        the format defined in [n.11]
        """
        if generation_date_time >= (datetime.utcnow() - timedelta(minutes=1)):
            for activity_dump_file in response['files']:
                # Verify the record type
                # Verify the response files with ActivityDumpFile.schema.json Object schema
                self.assertContainsRequiredFields("ActivityDumpFile.schema.json", activity_dump_file)
                # Get json data from url
                data = self._sas.DownloadFile(activity_dump_file['url'])
                if activity_dump_file['recordType'] == 'cbsd':
                    self.assertEqual(2, len(data['recordData']))
                    # Verify that cbsds and grants in the full dump matches a cbsd or grant created acitivities
                    for record in data['recordData']:
                        # Verify the response files with CbsdData.schema.json Object schema
                        self.assertContainsRequiredFields("CbsdData.schema.json", record)
                        self.assertEqual(1, len(record['grants']))
                        if record['registration']['fccId'] == device_a['fccId']:
                            assertCbsdRecordEqual(record['registration'],device_a)
                            assertGrantRecord(record['grants'][0], grant_0, grant_response[0])                   
                        else:
                            self.assertEqual(record['registration']['fccId'], device_c['fccId'])
                            assertCbsdRecordEqual(record['registration'], device_c)
                            assertGrantRecord(record['grants'][0], grant_1, grant_response[1])
                if activity_dump_file['recordType'] == 'esc_sensor':
                    self.assertEqual(1, len(data['recordData']))
                    # Verify the response file of Esc Sensor
                    self.assertContainsRequiredFields("EscSensorRecord.schema.json", data['recordData'][0])
                    self.assertDictEqual(esc_sensor_record, data['recordData'][0])
                if activity_dump_file['recordType'] == 'zone':
                    self.assertEqual(1, len(data['recordData']))
                    # Verify the response file of PPA
                    self.assertContainsRequiredFields("zoneData.schema.json", data['recordData'][0])
                    self.assertEqual(ppa_record['id'], data['recordData'][0]['id'])
                    self.assertEqual(ppa_record['usage'], data['recordData'][0]['usage'])
                    self.assertEqual(ppa_record['terminated'], data['recordData'][0]['terminated'])
                    self.assertEqual(ppa_record['zone']['features'][0]['geometry']['coordinates'], data['recordData'][0]['zone']['features'][0]['geometry']['coordinates'])
                    self.assertEqual(set(ppa_record['ppaInfo']['palId']), set(data['recordData'][0]['ppaInfo']['palId']))
                    self.assertEqual(set(ppa_record['ppaInfo']['cbsdReferenceId']), set(data['recordData'][0]['ppaInfo']['cbsdReferenceId']))
                    self.assertEqual(ppa_record['ppaInfo']['ppaBeginDate'], data['recordData'][0]['ppaInfo']['ppaBeginDate'])
                    self.assertEqual(ppa_record['ppaInfo']['ppaExpirationDate'], data['recordData'][0]['ppaInfo']['ppaExpirationDate'])                                    