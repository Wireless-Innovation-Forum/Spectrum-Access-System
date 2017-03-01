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
import unittest

import sas


class RelinquishmentTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def test_10_13_4_1_1(self):
    """Successful CBSD relinquishment request.

    CBSD Harness sends Relinquishment Request to SAS including CBSD ID and
    Grant ID in correct format. The response should be SUCCESS.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant_0]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue(response['grantId'])
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response

    # Relinquish the grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertEqual(response['response']['responseCode'], 0)

  def test_10_13_4_1_2(self):
    """Multiple iterative CBSD relinquishments.

    CBSD Harness sends multiple Relinquishment Requests to SAS including CBSD 
    ID and Grant ID in correct format. The response should be SUCCESS.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request three grants
    grant_id = []
    for i in range(0, 3):
      grant = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
      grant['cbsdId'] = cbsd_id
      grant['operationParam']['operationFrequencyRange']['lowFrequency'] = (
          3600000000.0 + i * 10000000.0)
      grant['operationParam']['operationFrequencyRange']['highFrequency'] = (
          3610000000.0 + i * 10000000.0)
      request = {'grantRequest': [grant]}
      # Check grant response
      response = self._sas.Grant(request)['grantResponse'][0]
      self.assertEqual(response['cbsdId'], cbsd_id)
      self.assertTrue(response['grantId'])
      self.assertEqual(response['response']['responseCode'], 0)
      grant_id.append(response['grantId'])
      del request, response

    # Relinquish second grant, then first grant, then third grant
    for i in [1, 0, 2]:
      request = {
          'relinquishmentRequest': [{
              'cbsdId': cbsd_id,
              'grantId': grant_id[i]
          }]
      }
      response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
      # Check the relinquishment response
      self.assertEqual(response['cbsdId'], cbsd_id)
      self.assertEqual(response['grantId'], grant_id[i])
      self.assertEqual(response['response']['responseCode'], 0)
      