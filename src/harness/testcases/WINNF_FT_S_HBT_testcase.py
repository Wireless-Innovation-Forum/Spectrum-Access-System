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
from datetime import timedelta
import json
import logging
import os
import time
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
  def test_WINNF_FT_S_HBT_1(self):
    """Heartbeat request array after moving to Granted / Heartbeating state.

    Returns response code 0 (NO_ERROR) for all requests.
    """
    # Register 3 devices.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_e['fccId']})
    # Inject User IDs
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    self._sas_admin.InjectUserId({'userId': device_c['userId']})
    self._sas_admin.InjectUserId({'userId': device_e['userId']})
    request = {'registrationRequest': [device_a, device_c, device_e]}
    # Check Reg response.
    response = self._sas.Registration(request)['registrationResponse']
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Create and send grant requests for all 3 devices.
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_2['cbsdId'] = cbsd_ids[2]
    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Check grant response.
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 3)
    grant_ids = []
    grant_expire_times = []
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
      grant_expire_times.append(
          datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # CBSDs send a Heartbeat request to Authorize the device.
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
        'grantId': grant_ids[2],
        'operationState': 'GRANTED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response.
    self.assertEqual(len(response), 3)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(resp['grantId'], grant_ids[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)
    del request, response

    # All 3 devices send a heartbeat request in AUTHORIZED state.
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'AUTHORIZED'
    }, {
        'cbsdId': cbsd_ids[1],
        'grantId': grant_ids[1],
        'operationState': 'AUTHORIZED'
    }, {
        'cbsdId': cbsd_ids[2],
        'grantId': grant_ids[2],
        'operationState': 'AUTHORIZED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response for all 3 devices.
    self.assertEqual(len(response), 3)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(resp['grantId'], grant_ids[response_num])
      transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
      self.assertLess(datetime.utcnow(), transmit_expire_time)
      self.assertLessEqual(
          (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
      self.assertLessEqual(transmit_expire_time,
                           grant_expire_times[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)

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
  def test_WINNF_FT_S_HBT_6(self):
    """Heartbeat Request from CBSD immediately after CBSD's grant is expired.

    Response Code should  be 103.
    """

    # Register the device.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    cbsd_ids = self.assertRegistered([device_a])

    # Request grant.
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    request = {'grantRequest': [grant_0]}
    # Check grant response.
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    grant_expire_time = datetime.strptime(response['grantExpireTime'],
                                          '%Y-%m-%dT%H:%M:%SZ')
    #  Test will automatically fail if the SAS UUT is not configured to use a
    #  short Grant duration to prevent this test from taking unnecessarily
    #  long to execute.
    self.assertTrue(grant_expire_time < datetime.utcnow()+timedelta(hours=24))
    del request, response

    # First Heartbeat to authorize the device.
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_ids[0],
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }

    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response.
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Calculate (wait time) difference between current time and GrantExpireTime.
    difference_time = (grant_expire_time - datetime.utcnow()).total_seconds()
    logging.debug(
        'Difference between grantExpireTime and CurrentTime (in seconds): %d',
        difference_time)
    time.sleep(difference_time + 1)

    # Send a Heartbeat request after grantExpireTime with expired grantId.
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_ids[0],
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response, must have Response Code 103
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertTrue(response['response']['responseCode'] in (103, 500))
    transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    self.assertLessEqual(transmit_expire_time, datetime.utcnow())

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

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_8(self):
    """Heartbeat Array Request: BLACKLISTED.

    Response Code should  be 101.
    """
    # Register the devices
    registration_request = []
    fcc_ids = []
    for device_filename in ('device_a.json', 'device_c.json', 'device_e.json'):
      device = json.load(
          open(os.path.join('testcases', 'testdata', device_filename)))
      fcc_ids.append(device['fccId'])
      registration_request.append(device)

    cbsd_ids = self.assertRegistered(registration_request)

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
    self.assertEqual(len(response), len(cbsd_ids))
    grant_ids = []
    grant_expire_time = []
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[resp_number])
      self.assertTrue(resp['grantId'])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
      grant_expire_time.append(
          datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Inject Third Device into Blacklist
    self._sas_admin.BlacklistByFccId({'fccId': fcc_ids[2]})

    # First Heartbeat Request
    heartbeat_request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_request.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': 'GRANTED'
      })

    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(len(response), len(grant_ids))

    # Check the heartbeat response
    # First two devices have Response Code 0.
    for index, resp in enumerate(response[:2]):
      self.assertEqual(resp['cbsdId'], cbsd_ids[index])
      self.assertEqual(resp['grantId'], grant_ids[index])
      self.assertEqual(resp['response']['responseCode'], 0)
      transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
      self.assertLess(datetime.utcnow(), transmit_expire_time)
      self.assertLessEqual(
          (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
      self.assertLessEqual(transmit_expire_time,
                           grant_expire_time[index])

    # Third device is in Blacklist, must have Response Code 101.
    self.assertEqual(response[2]['response']['responseCode'], 101)
    transmit_expire_time = datetime.strptime(response[2]['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    self.assertLessEqual(transmit_expire_time, datetime.utcnow())
    del request, response

    # Third device sends a second heartbeat request with its blacklisted cbsdId.
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_ids[2],
            'grantId': grant_ids[2],
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response has Response code 101 or 103
    self.assertTrue(response['response']['responseCode'] in (101, 103))

