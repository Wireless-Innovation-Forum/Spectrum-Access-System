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
from util import winnforum_testcase
import sas_testcase
from urllib import urlopen
import validators
from datetime import datetime, timedelta

class FullActivityDumpMessageTestcase(sas_testcase.SasTestCase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()

    def tearDown(self):
        pass

    @winnforum_testcase
    def test_WINNF_FT_S_FAD_1(self):
        """This test verifies that a SAS Under Test can successfully respond to a full activity dump request from a SAS Test Harness

        Response Code should be 200
        """
        # register devices
        device_a = json.load(
            open(os.path.join('testcases', 'testdata', 'device_a.json')))
        self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
        device_c = json.load(
            open(os.path.join('testcases', 'testdata', 'device_c.json')))
        self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
        request = {'registrationRequest': [device_a, device_c]}
        response = self._sas.Registration(request)['registrationResponse']
        # Check registration response
        cbsd_ids = []
        for resp in response:
            self.assertEqual(resp['response']['responseCode'], 0)
            cbsd_ids.append(resp['cbsdId'])
        del request, response

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
        response = self._sas.Grant(request)['grantResponse']
        # Check registration response
        grant_ids = []
        for resp in response:
            self.assertEqual(resp['response']['responseCode'], 0)
            grant_ids.append(resp['grantId'])
        del request, response

        # Trigger the SAS to generate the activity dump
        self._sas_admin.TriggerFullActivityDump()

        # Get dump 
        response = self._sas.GetFullActivityDump()
        # Verify the response with  FullActivityDump.schema.json Object schema
        self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
        generation_date_time = datetime.strptime(response['generationDateTime'],
                                          '%Y-%m-%dT%H:%M:%SZ')
        if generation_date_time >= (datetime.utcnow() - timedelta(days=7)):
            for file in response['files']:
                # Verify the response files with ActivityDumpFile.schema.json Object schema
                self.assertContainsRequiredFields("ActivityDumpFile.schema.json", file)
                # Verify the url format is valid (pip install validators)
                self.assertTrue(validators.url(file['url']))
                # Verify the link to download the file dump is valid
                self.assertEqual(urlopen(file['url']).getcode(), 200)
                # Verify the record type 
                self.assertTrue(file['recordType'] in ('cbsd','zone', 'coordination'))
                #get data in file
                data = urlopen(file['url']).read()
                #Decoding JSON message from file 
                data = json.loads(data)
                for record in data['recordData']:
                    # Verify the response files with CbsdData.schema.json Object schema
                    self.assertContainsRequiredFields("CbsdData.schema.json", record)
                    self.assertTrue(record['registration']['fccId'] in (device_a['fccId'], device_c['fccId']))
                    self.assertTrue(record['registration']['cbsdSerialNumber'] in (device_a['cbsdSerialNumber'], device_c['cbsdSerialNumber']))
                    self.assertTrue(record['registration']['userId'] in (device_a['userId'], device_c['userId']))
                    for grant in record['grants']:
                        self.assertTrue(grant['id'] in grant_ids)