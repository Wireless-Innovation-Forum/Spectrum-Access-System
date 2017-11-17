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

from datetime import datetime
import json
import os
import time
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
  def test_WINNF_FT_S_RLQ_1(self):
    """Multiple iterative Grant relinquishments.

    The response should be SUCCESS.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request two grants
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
    request = {'grantRequest': [grant_0, grant_1]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 2)
    grant_ids = []
    for resp in response:
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    # Relinquish the 1st grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_ids[0]
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_ids[0])
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Relinquish the 2nd grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_ids[1]
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_ids[1])
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Send a heartbeat request with relinquished grantIds.
    heartbeat_request = []
    for grant_id in grant_ids:
      heartbeat_request.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': 'GRANTED'
      })
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response
    self.assertEqual(len(response), 2)
    for resp in response:
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertTrue(resp['response']['responseCode'] == 103)
      # No need to check transmitExpireTime since this is the first heartbeat.

  @winnforum_testcase
  def test_WINNF_FT_S_RLQ_2(self):
    """Multiple Grant relinquishments: Successful simultaneous Relinquishment
    Request of multiple grants.

    Relinquishment Request array including valid CBSD ID and Grant ID.
    The response should be SUCCESS.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    self._sas_admin.InjectUserId({'userId': device['userId']})
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
    grant_ids = []
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 3)
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    # Relinquish the grants
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id, 'grantId': grant_ids[0]},
        {'cbsdId': cbsd_id, 'grantId': grant_ids[1]},
        {'cbsdId': cbsd_id, 'grantId': grant_ids[2]}]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse']
    # Check the relinquishment response
    self.assertEqual(len(response), 3)
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertEqual(resp['grantId'], grant_ids[resp_number])
      self.assertEqual(resp['response']['responseCode'], 0)
    del request, response

    # Send heartbeat request with relinquished grantIds.
    heartbeat_request = [{
        'cbsdId': cbsd_id,
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_id,
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_id,
        'grantId': grant_ids[2],
        'operationState': 'GRANTED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response
    self.assertEqual(len(response), 3)
    for resp in response:
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertTrue(resp['response']['responseCode'] == 103)
      # No need to check transmitExpireTime since this is the first heartbeat.

  @winnforum_testcase
  def test_WINNF_FT_S_RLQ_5(self):
    """Missing Parameter in Relinquishment Array request.

    Relinquishment Request including multiple grants with missing CBSD/Grant ID.
    The response should be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    self._sas_admin.InjectUserId({'userId': device['userId']})
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
        {},
        {'grantId': grant_id[2]}
    ]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse']
    # Check relinquishment response #1
    self.assertEqual(response[0]['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 102)
    # Check relinquishment response #2, 3
    for response_num in [1, 2]:
      self.assertFalse('cbsdId' in response[response_num])
      self.assertFalse('grantId' in response[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 102)

