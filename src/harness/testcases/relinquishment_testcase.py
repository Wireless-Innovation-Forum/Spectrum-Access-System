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
from util import winnforum_testcase


class RelinquishmentTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_1(self):
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

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_2(self):
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

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_4(self):
    """CBSD relinquishment request with CBSD ID that does not exist in SAS.

    CBSD Harness sends Relinquishment Request to SAS including CBSD ID and
    Grant ID in correct format but the CBSD ID does not exist in SAS.
    The response should be FAIL.
    """

    # Relinquish the grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': 'A nonexistent cbsd id',
            'grantId': 'A nonexistent grant id'
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertFalse('cbsdId' in response)
    self.assertTrue(response['response']['responseCode'] == 103 or
                    response['response']['responseCode'] == 105)

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_5(self):
    """CBSD relinquishment request of nonexistent grant

    CBSD Harness sends Relinquishment Request to SAS including grant
    with valid CBSD ID and nonexistent Grant ID. The response should
    be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Relinquish grant
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id, 'grantId': 'A nonexistent grant id'}]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_7(self):
    """CBSD relinquishment request of grant that does not belong to the CBSD

    CBSD Harness sends Relinquishment Request to SAS with valid CBSD ID and
    valid Grant ID, but the Grant doesn't belong to the CBSD. The response
    should be FAIL.
    """

    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Set up unique FCC IDs
    device_1['fccId'] = "test_fcc_id_1"
    device_2['fccId'] = "test_fcc_id_2"

    self._sas_admin.InjectFccId({'fccId': device_1['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})

    # Register the devices
    request = {'registrationRequest': [device_1, device_2]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_id = []
    for x in range (0, 2) :
      self.assertEqual(response[x]['response']['responseCode'], 0)
      cbsd_id.append(response[x]['cbsdId'])
    del request, response

    # Request grant
    grant = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant['cbsdId'] = cbsd_id[1]
    request = {'grantRequest': [grant]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id[1])
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response

    # Relinquish the grants
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id[0], 'grantId': grant_id}]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id[0])
    self.assertEqual(response['grantId'], grant_id)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_12(self):
    """CBSD relinquishment request with missing CBSD ID
    relinquished.

    CBSD Harness sends Relinquishment Request to SAS without CBSD ID.
    The response should be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response

    # Relinquish the grant
    request = {
        'relinquishmentRequest': [{
            'grantId': grant_id
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['grantId'], grant_id)
    self.assertIn(response['response']['responseCode'], [102, 105])

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_13(self):
    """CBSD relinquishment request with missing Grant ID
    relinquished.
 
    CBSD Harness sends Relinquishment Request to SAS with valid
    CBSD ID and without Grant ID. The response should be FAIL.
    """
 
    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response
 
    # Request grant
    grant = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response
 
    # Relinquish the grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_id
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINFF_FT_S_RLQ_14(self):
    """CBSD relinquishment request of multiple grants

    CBSD Harness sends Relinquishment Request to SAS including multiple
    grants with missing CBSD ID or missing Grant ID. The response should
    be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grants
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3600000000.0,
         'highFrequency': 3610000000.0
    }
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3610000000.0,
         'highFrequency': 3620000000.0
    }
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_id
    grant_2['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3620000000.0,
         'highFrequency': 3630000000.0
    }
    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Check grant response
    grant_id = []
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 3)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      self.assertEqual(resp['cbsdId'], cbsd_id)
      grant_id.append(resp['grantId'])
    del request, response

    # Relinquish the grants
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id},
        {'grantId': grant_id[1]},
        {'grantId': grant_id[2]}
    ]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse']
    # Check relinquishment response
    self.assertEqual(response[0]['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 102)
    self.assertFalse('cbsdId' in response[1])
    self.assertEqual(response[1]['grantId'], grant_id[1])
    self.assertIn(response[1]['response']['responseCode'], [102, 105])
    self.assertFalse('cbsdId' in response[2])
    self.assertEqual(response[2]['grantId'], grant_id[2])
    self.assertIn(response[2]['response']['responseCode'], [102, 105])
