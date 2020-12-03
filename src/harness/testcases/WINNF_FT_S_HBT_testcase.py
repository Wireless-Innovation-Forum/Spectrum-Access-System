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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
from datetime import timedelta
import json
import logging
import os
import time

from six.moves import zip

import common_strings
from request_handler import HTTPError
import sas
import sas_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, addCbsdIdsToRequests, addGrantIdsToRequests, json_load


class HeartbeatTestcase(sas_testcase.SasTestCase):

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
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
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
    grant_0 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_1 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_2 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
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
  def test_WINNF_FT_S_HBT_2(self):
    """Array Request: Heartbeat request from 3 CBSDs for GRANT renewal.

    Returns response code 0.
    """
    # Register three devices.
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json', 'device_e.json'):
      device = json_load(
          os.path.join('testcases', 'testdata', device_filename))
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

    # Request grants.
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
      grant['cbsdId'] = cbsd_id
      grant_request.append(grant)
    request = {'grantRequest': grant_request}
    # Check grant response.
    response = self._sas.Grant(request)['grantResponse']
    grant_ids = []
    grant_expire_times = []
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertGreater(len(resp['grantId']), 0)
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
      grant_expire_times.append(
          datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Heartbeat requests with 'grantRenew' set to True
    heartbeat_request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_request.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': 'GRANTED',
          'grantRenew': True
      })
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response.
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
      grant_expire_time = datetime.strptime(resp['grantExpireTime'],
                                            '%Y-%m-%dT%H:%M:%SZ')
      self.assertGreaterEqual(grant_expire_time,
                              grant_expire_times[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_3(self):
    """Initial Heartbeat Request (immediately after CBSD moves into Granted
    State) from three CBSDs with an unsupported protocol version by SAS.

    Returns response code 100.
    """

    # Register three devices.
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json', 'device_e.json'):
      device = json_load(
          os.path.join('testcases', 'testdata', device_filename))
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

    # Request grants.
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
      grant['cbsdId'] = cbsd_id
      grant_request.append(grant)
    request = {'grantRequest': grant_request}
    # Check grant response.
    response = self._sas.Grant(request)['grantResponse']
    grant_ids = []
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[resp_number])
      self.assertTrue(resp['grantId'])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    # Use higher than supported version.
    self._sas.cbsd_sas_version = 'v5.0'

    # First Heartbeat with unsupported SAS-CBSD protocol version.
    heartbeat_request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_request.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': 'GRANTED'
      })
    request = {'heartbeatRequest': heartbeat_request}
    try:
      response = self._sas.Heartbeat(request)['heartbeatResponse']
      for response_num, resp in enumerate(response):
        # Check the heartbeat response.
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['grantId'], grant_ids[response_num])
        self.assertEqual(resp['response']['responseCode'], 100)
        transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                                 '%Y-%m-%dT%H:%M:%SZ')
        self.assertLessEqual(transmit_expire_time, datetime.utcnow())
    except HTTPError as e:
      # Allow HTTP status 404.
      self.assertEqual(e.error_code, 404)

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
      device = json_load(
          os.path.join('testcases', 'testdata', device_filename))
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
      grant = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
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
  def test_WINNF_FT_S_HBT_5(self):
    """CBSD heartbeat request after grant is terminated.

    Heartbeat request immediately after CBSD moves out of Granted State. The
    grantId is invalid in heartbeat request. The response should be FAIL.
    """

    # Register the device
    device_a = json_load(os.path.join('testcases', 'testdata', 'device_a.json'))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]

    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_0['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant_0]}

    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    grant_expire_time = datetime.strptime(response['grantExpireTime'],
                                          '%Y-%m-%dT%H:%M:%SZ')
    del request, response

    # First successful Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id, 'grantId': grant_id, 'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]

    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertEqual(response['response']['responseCode'], 0)
    transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    del request, response

    # Relinquish the grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_id, 'grantId': grant_id
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]

    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertEqual(response['response']['responseCode'], 0)

    # use relinquished grantId in new heartbeat request after transmitExpireTime
    # is passed, but before the grant expires
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id, 'grantId': grant_id, 'operationState': 'GRANTED'
        }]
    }
    transmit_expire_wait_time = (transmit_expire_time - datetime.utcnow()).total_seconds()
    time.sleep(transmit_expire_wait_time + 1)
    self.assertGreater(datetime.utcnow(), transmit_expire_time)
    self.assertLess(datetime.utcnow(), grant_expire_time)
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]

    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue(response['response']['responseCode'] in (103, 500))
    transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    self.assertLess(transmit_expire_time, datetime.utcnow())

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_6(self):
    """Heartbeat Request from CBSD immediately after CBSD's grant is expired.

    Response Code should  be 103.
    """

    # Register the device.
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    cbsd_ids = self.assertRegistered([device_a])

    # Request grant.
    grant_0 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
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
      device = json_load(
          os.path.join('testcases', 'testdata', device_filename))
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
      grant = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
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
      device = json_load(
          os.path.join('testcases', 'testdata', device_filename))
      fcc_ids.append(device['fccId'])
      registration_request.append(device)

    cbsd_ids = self.assertRegistered(registration_request)

    # Request grant
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
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

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_9(self):
    """ Array request, of three cbsds,SAS terminates the Grant for the one
    that impacts incumbent activity.

    successful heartbeat for the grants of two cbsds that don't impact
     the incumbent and failed with responseCode 500 for the third one.
    """
    # STEP 1
    # register three devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    cbsd_ids = self.assertRegistered([device_a, device_c, device_e])
    # load and set Grants data
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_a['cbsdId'] = cbsd_ids[0]
    grant_c = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_c['cbsdId'] = cbsd_ids[1]
    grant_e = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_e['cbsdId'] = cbsd_ids[2]
    grant_e['operationParam']['operationFrequencyRange']\
                             ['lowFrequency'] = 3650000000
    grant_e['operationParam']['operationFrequencyRange']\
                             ['highFrequency'] = 3660000000
    request = {'grantRequest': [grant_a, grant_c, grant_e]}
    # send grant request
    response = self._sas.Grant(request)['grantResponse']
    grant_ids = []
    grant_expire_times = []
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
      grant_expire_times.append(
          datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response
    # First Heartbeat
    request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      request.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': 'GRANTED'
      })

    response = self._sas.Heartbeat({'heartbeatRequest': request})['heartbeatResponse']
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
    del request, response
    # STEP 2
    # load and inject FSS data with Overlapping Frequency of CBSD
    fss_e = json_load(
        os.path.join('testcases', 'testdata', 'fss_record_0.json'))
    self._sas_admin.InjectFss(fss_e)
    # load and inject GWBL data with Overlapping Frequency of CBSD
    gwbl_e = json_load(
        os.path.join('testcases', 'testdata', 'gwbl_record_0.json'))
    self._sas_admin.InjectWisp(gwbl_e)
    # STEP 3
    # Trigger daily activities and wait for it to get it complete
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    # Send Heartbeat after triggering the IAP
    request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      request.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': 'GRANTED'
      })
    response = self._sas.Heartbeat({'heartbeatRequest': request})['heartbeatResponse']
    del request
    # CHECK
    # Check first two CBSDs with a successful HB response
    for response_num, resp in enumerate(response[:2]):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(resp['grantId'], grant_ids[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)
      transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],\
                                               '%Y-%m-%dT%H:%M:%SZ')
      self.assertLessEqual((transmit_expire_time - \
                            datetime.utcnow()).total_seconds(), 240)
      self.assertLessEqual(datetime.utcnow(), transmit_expire_time)
      self.assertLessEqual(transmit_expire_time, grant_expire_times[response_num])
    # Check the third  CBSD with unsuccessful HB response of code 500
    self.assertEqual(response[2]['cbsdId'], cbsd_ids[2])
    self.assertEqual(response[2]['grantId'], grant_ids[2])
    self.assertEqual(response[2]['response']['responseCode'], 500)
    self.assertLessEqual(datetime.strptime(
        response[2]['transmitExpireTime'],'%Y-%m-%dT%H:%M:%SZ'), datetime.utcnow())

  def generate_HBT_10_default_config(self, filename):
    """Generates the WinnForum configuration for HBT.10."""

    # Load device info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # Load grant.json
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_c = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

    heartbeat_a = {'operationState': 'GRANTED'}
    heartbeat_c = {'grantId': 'REMOVE', 'operationState': 'GRANTED'}
    heartbeat_b = {'operationState': 'GRANTED', 'grantRenew': True}

    # Device a and device_c are Cat A.
    self.assertEqual(device_a['cbsdCategory'], 'A')
    self.assertEqual(device_c['cbsdCategory'], 'A')

    # Device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam']
    }
    conditionals = [conditionals_b]
    del device_b['installationParam']
    del device_b['cbsdCategory']
    del device_b['airInterface']

    # Create the actual config.
    devices = [device_a, device_c, device_b]
    blacklist_devices = [device_a]
    grant_requests = [grant_a, grant_c, grant_b]
    heartbeat_requests = [heartbeat_a, heartbeat_c, heartbeat_b]
    config = {
        'fccIdsBlacklist': [d['fccId'] for d in blacklist_devices],
        'conditionalRegistrationData': conditionals,
        'registrationRequests': devices,
        'grantRequests': grant_requests,
        'heartbeatRequests': heartbeat_requests,
        # First request has a blacklisted CBSD => BLACKLISTED
        # Second request is missing Grant ID => MISSING_PARAM
        # Third request has all valid params => SUCCESS
        'expectedResponseCodes': [(101,), (102,), (0,)]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_HBT_10_default_config)
  def test_WINNF_FT_S_HBT_10(self, config_filename):
    """[Configurable] Heartbeat with optional intervening grant termination
       or blacklist."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list,
            'fccIdsBlacklist': list,
            'grantRequests': list,
            'heartbeatRequests': list,
            'expectedResponseCodes': list
        })
    self.assertEqual(
        len(config['registrationRequests']), len(config['grantRequests']))
    self.assertEqual(
        len(config['grantRequests']), len(config['heartbeatRequests']))
    self.assertEqual(
        len(config['heartbeatRequests']),
        len(config['expectedResponseCodes']))

    # Register devices
    try:
      cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                       config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)
      raise

    # Request grant
    grant_request = config['grantRequests']
    addCbsdIdsToRequests(cbsd_ids, grant_request)
    request = {'grantRequest': grant_request}

    # Check grant response
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))
    grant_ids = []
    grant_expire_times = []
    for _, resp in enumerate(response):
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
      grant_expire_times.append(
          datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Blacklist N2 CBSDs
    for fcc_id in config['fccIdsBlacklist']:
      self._sas_admin.BlacklistByFccId({'fccId': fcc_id})
    blacklisted_cbsd_ids = []
    for cbsd_id, request in zip(cbsd_ids, config['registrationRequests']):
      if request['fccId'] in config['fccIdsBlacklist']:
        blacklisted_cbsd_ids.append(cbsd_id)

    # First Heartbeat Request
    heartbeat_request = config['heartbeatRequests']
    addCbsdIdsToRequests(cbsd_ids, heartbeat_request)
    addGrantIdsToRequests(grant_ids, heartbeat_request)
    request = {'heartbeatRequest': heartbeat_request}
    responses = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(len(responses), len(heartbeat_request))

    # Check heartbeat response
    self.assertEqual(len(responses), len(config['expectedResponseCodes']))
    for i, response in enumerate(responses):
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_response_codes)
      # Check if the request contains CBSD ID
      if 'cbsdId' in heartbeat_request[i]:
        # Check if CBSD ID is valid
        if (heartbeat_request[i]['cbsdId'] in cbsd_ids) and (
            heartbeat_request[i]['cbsdId'] not in blacklisted_cbsd_ids):
          self.assertEqual(response['cbsdId'], heartbeat_request[i]['cbsdId'])
          # Check if the request contains Grant ID
          if 'grantId' in heartbeat_request[i]:
            # Check if Grant ID is valid
            if heartbeat_request[i]['grantId'] in grant_ids:
              cbsd_index = cbsd_ids.index(heartbeat_request[i]['cbsdId'])
              grant_index = grant_ids.index(heartbeat_request[i]['grantId'])
              # Check if CBSD ID is paired with the corresponding Grant ID.
              if cbsd_index == grant_index:
                self.assertEqual(response['grantId'],
                                 heartbeat_request[i]['grantId'])

      if response['response']['responseCode'] == 0:
        transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                                 '%Y-%m-%dT%H:%M:%SZ')
        self.assertLess(datetime.utcnow(), transmit_expire_time)
        self.assertLessEqual(
            (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
        self.assertLessEqual(transmit_expire_time, grant_expire_times[i])
        if ('grantRenew' in heartbeat_request[i]) and (
            heartbeat_request[i]['grantRenew']):
          grant_expire_time = datetime.strptime(response['grantExpireTime'],
                                                '%Y-%m-%dT%H:%M:%SZ')
          self.assertLess(datetime.utcnow(), grant_expire_time)
      else:
        transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                                 '%Y-%m-%dT%H:%M:%SZ')
        self.assertLessEqual(transmit_expire_time, datetime.utcnow())

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_11(self):
    """Out of sync Grant state between the CBSD and the SAS.

    Returns response code 502 (UNSYNC_OP_PARAM).
    """
    # Load a device.
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))

    # Load grant.json
    grant_0 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

    # Register the device and get a grant
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_a], [grant_0])

    # Send a Heartbeat request.
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'AUTHORIZED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(len(response), 1)

    # Check the heartbeat response.
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[0]['grantId'], grant_ids[0])
    self.assertEqual(response[0]['response']['responseCode'], 502)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_12(self):
    """The grant is SUSPENDED or TERMINATED in the heartbeat response.

     Heartbeat Response Code for Step 7 and 8, should  be:
     - 500(TERMINATED_GRANT) or 501(SUSPENDED_GRANT)
    """
    # Load DPAs and ensure all DPAs are inactive
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Load a device.
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    # CBSD located in DPA 6 neighborhood
    device_a['installationParam']['latitude'] = 36.7115375795
    device_a['installationParam']['longitude'] = -76.0162751808

    # Register device
    cbsd_ids = self.assertRegistered([device_a])

    # Step 3: Send grant request and check grant response
    grant_0 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_0['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3550000000
    grant_0['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3560000000
    grant_0['operationParam']['maxEirp'] = 20
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertTrue('grantId' in response)
    grant_expire_time = datetime.strptime(response['grantExpireTime'],
                                          '%Y-%m-%dT%H:%M:%SZ')
    grant_id = response['grantId']
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_id,
        'operationState': 'GRANTED'
    }]
    del request, response

    # Step 4: Send heartbeat request and check heartbeat response
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['grantId'], grant_id)
    del request, response

    # Step 5: Activate DPA on channel 3550 - 3560 MHz
    self._sas_admin.TriggerDpaActivation({
        'frequencyRange': {
            'lowFrequency': 3550000000,
            'highFrequency': 3560000000
        },
        'dpaId': 'East1'
    })

    # Step 6: Sleep 240 seconds
    time.sleep(240)

    # Step 7
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_id,
        'operationState': 'GRANTED'
    }]
    # Send heartbeat request and Check heartbeat response
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(len(response), 1)
    self.assertTrue(response[0]['response']['responseCode'] in [500, 501])
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[0]['grantId'], grant_id)
    if response[0]['response']['responseCode'] == 500:
      return

    # Step 8
    time.sleep(300)
    self.assertLess(datetime.utcnow(), grant_expire_time)
    # Step 9 - Heartbeat request with operationState = GRANTED
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_id,
        'operationState': 'GRANTED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check heartbeat response
    self.assertEqual(len(response), 1)
    self.assertTrue(response[0]['response']['responseCode'] in [500, 501])
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[0]['grantId'], grant_id)
