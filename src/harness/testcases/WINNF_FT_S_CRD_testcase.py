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
import hashlib
import urllib


class CbsdDataRecordExchangeTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_CRD_1(self):
    """This test verifies that a SAS can successfully responds to a SAS 
    Test Harness on a specific CBSD

    Response Code should be 200
    """

    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json'):
      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    self.assertEqualObject(request, request)
    del request, response

    # Request grant
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[1]
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_ids[1])
    self.assertTrue(response['grantId'])
    self.assertEqual(response['channelType'], 'GAA')
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    cbsd_sha1 = hashlib.sha1(b'%s' %
                             registration_request[0]['cbsdSerialNumber']).hexdigest()
    response = self._sas.GetCbsdDataMessage(urllib.quote(registration_request[0]['fccId'] +
                                                         '/' + cbsd_sha1, safe=''))

    # Verify the response schema and registration values for first device
    self.assertContainsRequiredFields('CbsdDataMessage.schema.json', response)
    self.assertDictEqual(response['registration'], registration_request[0])
    del request, response, cbsd_sha1

    cbsd_sha1 = hashlib.sha1(b'%s' %
                             registration_request[1]['cbsdSerialNumber']).hexdigest()
    response = self._sas.GetCbsdDataRecord(urllib.quote(registration_request[1]['fccId'] +
                                                        '/' + cbsd_sha1, safe=''))
    # Verify the response schema and registration and grant values for second device
    self.assertContainsRequiredFields('CbsdDataMessage.schema.json', response)
    self.assertDictEqual(response['registration'], registration_request[1])
    self.assertDictEqual(response['grants'][0]['operationParam'],
                         grant_0['operationParam'])


