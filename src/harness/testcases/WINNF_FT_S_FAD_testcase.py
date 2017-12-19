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
from datetime import datetime, timedelta
import hashlib

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
        client_cert = os.path.join('certs', 'admin_client.cert')
        client_key = os.path.join('certs', 'admin_client.key')
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
        response = self._sas.Grant(request)['grantResponse']
        # Check registration response
        grant_ids = []
        for resp in response:
            self.assertValidResponseFormatForApprovedGrant(resp)
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
        if generation_date_time >= (datetime.utcnow() - timedelta(minutes=1)):
            for activity_dump_file in response['files']:
                # Verify the record type 
                if activity_dump_file['recordType'] == 'cbsd':
                    # Verify the response files with ActivityDumpFile.schema.json Object schema
                    self.assertContainsRequiredFields("ActivityDumpFile.schema.json", activity_dump_file)
                    # Get json data from url
                    data = self._sas.DownloadFile(activity_dump_file['url'], client_cert, client_key)
                    # Verify that everything in the full dump matches a cbsd or grant created at the beginning
                    for record in data['recordData']:
                        # Verify the response files with CbsdData.schema.json Object schema
                        self.assertContainsRequiredFields("CbsdData.schema.json", record)
                        self.assertTrue(record['registration']['fccId'] in (device_a['fccId'], device_c['fccId']))
                        self.assertTrue(record['registration']['cbsdCategory'] in (device_a['cbsdCategory'], device_c['cbsdCategory']))
                        for grant in record['grants']:
                            self.assertTrue(grant['id'] in grant_ids)
                    
                    # Check that all cbsds and grants are present in the full dump
                    for device in [device_a, device_c]:
                        record_id = 'cbsd/'+ device['fccId']+'/'+ hashlib.sha1(device['cbsdSerialNumber']).hexdigest()
                        # Get grants by cbsd_id
                        grants_of_cbsd = [x['grants'] for x in data['recordData'] if x['id'] == record_id]
                        # Verify that grant_id in the full dump matches a grant created at the beginning
                        self.assertTrue(grants_of_cbsd[0][0]['id'] in (grant_ids))
                        # Get cbsd informations by cbsd_id
                        cbsd_informations = [x['registration'] for x in data['recordData'] if x['id'] == record_id]
                        self.assertEqual(cbsd_informations[0]['fccId'], device['fccId'])
                        self.assertEqual(cbsd_informations[0]['cbsdCategory'], device['cbsdCategory'])