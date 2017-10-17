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
import unittest
import sas
from util import winnforum_testcase


class HeartbeatTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_4(self):
    """CBSD heartbeat request array with various required parameters missing.

    Heartbeat request immediately after CBSD moves into Granted State.
    Requests: 1 is valid; 2, 3 and 4 are missing required parameters.
    Returns: response code 0 for request 1; 102 for requests 2, 3 and 4.
    """

    # Register 4 devices.
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json', 'device_e.json',
                            'device_f.json'):
      device = json.load(
          open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response.
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Request grant.
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
      grant['cbsdId'] = cbsd_id
      grant_request.append(grant)
    request = {'grantRequest': grant_request}
    # Check grant response.
    response = self._sas.Grant(request)['grantResponse']
    grant_ids = []
    grant_expire_times = []
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
      grant_expire_times.append(
          datetime.strptime(resp['grantExpireTime'],
                            '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Prepare 4 Heartbeat requests (these are first heartbeats)
    # 1. Valid, 2. No cbsd_id, 3. No grantId, 4. No operationState
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }, {
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_ids[2],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_ids[3],
        'grantId': grant_ids[3],
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']

    # Check the heartbeat response.
    self.assertEqual(len(response), 4)
    # Check the cbsdId and grantId match the request for 1st and 4th response.
    for response_num in (0, 3):
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(response[response_num]['grantId'],
                       grant_ids[response_num])
    # Validating the first request's successful response
    self.assertEqual(response[0]['response']['responseCode'], 0)
    transmit_expire_time = datetime.strptime(response[0]['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    self.assertLess(datetime.utcnow(), transmit_expire_time)
    self.assertLessEqual(
        (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
    self.assertLess(transmit_expire_time, grant_expire_times[0])
    # Validating response for requests: 2, 3 and 4.
    for response_num in (1, 2, 3):
      self.assertEqual(response[response_num]['response']['responseCode'], 102)
      transmit_expire_time = datetime.strptime(
          response[response_num]['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
      self.assertLess(transmit_expire_time, datetime.utcnow())

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_7(self):
    """CBSD heartbeat requests with invalid parameter.

    Heartbeat request immediately after CBSD moves into Granted State.
    Requests: 1 & 2 are valid; 3rd request has a parameter with invalid value.
    Returns: response code 0 for requests 1 & 2; 103 for request 3.
    """

    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json', 'device_e.json'):
      device = json.load(
          open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Request grant
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
      grant['cbsdId'] = cbsd_id
      grant_request.append(grant)
    request = {'grantRequest': grant_request}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse']
    grant_ids = []
    grant_expire_times = []
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
      grant_expire_times.append(
          datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Prepare Heartbeats
    # No. 1, 2 - Valid requests, No. 3 - Invalid grantId in request
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_ids[1],
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_ids[2],
        'grantId': grant_ids[2] + '-changed',
        'operationState': 'GRANTED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check heartbeat response
    self.assertEqual(len(response), 3)
    for response_num in (0, 1):
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(response[response_num]['grantId'],
                       grant_ids[response_num])
    self.assertEqual(response[2]['cbsdId'], cbsd_ids[2])
    self.assertFalse('grantId' in response[2])
    # Validating the first and second request's successful response.
    for response_num in (0, 1):
      self.assertEqual(response[response_num]['response']['responseCode'], 0)
      transmit_expire_time = datetime.strptime(
          response[response_num]['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
      self.assertLess(datetime.utcnow(), transmit_expire_time)
      self.assertLessEqual(
          (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
      self.assertLessEqual(transmit_expire_time,
                           grant_expire_times[response_num])
    # Validating response for 3rd request.
    self.assertEqual(response[2]['response']['responseCode'], 103)
    transmit_expire_time = datetime.strptime(response[2]['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    self.assertLess(transmit_expire_time, datetime.utcnow())
