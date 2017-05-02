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
  def test_10_9_4_1_1_1(self):
    """Heartbeat request immediately after CBSD moves into Granted State.

    The response should be SUCCESS.
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

    # Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertLess(datetime.utcnow(),
                    datetime.strptime(response['transmitExpireTime'],
                                      '%Y-%m-%dT%H:%M:%SZ'))
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_2(self):
    """Multiple heartbeat requests after moving to Granted/Heartbeating state.

    Returns response code 0 (NO_ERROR) for all requests
    """
    # Register three devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    request = {'registrationRequest': [device_a, device_b, device_c]}
    response = self._sas.Registration(request)['registrationResponse']
    cbsd_ids = []
    for resp in response:
        self.assertEqual(resp['response']['responseCode'], 0)
        cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Create and send grant requests
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[2]
    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 3)
    grant_ids = []
    grant_expire_time = []
    for response_num, resp in enumerate(response):
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['response']['responseCode'], 0)
        grant_ids.append(resp['grantId'])
        grant_expire_time.append(
            datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Heartbeat the devices
    heartbeat_request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        heartbeat_request.append({
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        })
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response
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
                             grant_expire_time[response_num])
        self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_3(self):
    """Request grant renewal from heartbeat request.

    Returns response code 0 (NO_ERROR)
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
    grant_id = response['grantId']
    self.assertEqual(response['response']['responseCode'], 0)
    grant_expire_time = datetime.strptime(response['grantExpireTime'],
                                          '%Y-%m-%dT%H:%M:%SZ')
    del request, response

    # First successful Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED',
            'grantRenew': True
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    self.assertLess(datetime.utcnow(), transmit_expire_time)
    self.assertLessEqual(
        (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
    self.assertLessEqual(transmit_expire_time, grant_expire_time)
    self.assertLess(datetime.utcnow(), grant_expire_time)
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_4(self):
    """Request grant renewal from heartbeat request (3 devices).

    Returns response code 0 (NO_ERROR)
    """
    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_b.json', 'device_c.json'):
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
    del request, response

    # Request grant
    grant_request = []
    for grant_filename, cbsd_id in zip(
          ['grant_0.json', 'grant_0.json', 'grant_0.json'], cbsd_ids):
        grant = json.load(
            open(os.path.join('testcases', 'testdata', grant_filename)))
        grant['cbsdId'] = cbsd_id
        grant_request.append(grant)
    request = {'grantRequest': grant_request}
    # Check grant response
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

    # Heartbeat requests with grantRenew set to True
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
    # Check the heartbeat response
    for response_num, resp in enumerate(response):
        transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                                 '%Y-%m-%dT%H:%M:%SZ')
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['grantId'], grant_ids[response_num])
        self.assertLess(datetime.utcnow(), transmit_expire_time)
        self.assertLessEqual(
            (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
        self.assertLessEqual(transmit_expire_time,
                             grant_expire_times[response_num])
        self.assertLess(datetime.utcnow(), grant_expire_times[response_num])
        self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_9(self):
    """Initial Heartbeat Request (immediately after CBSD moves
    into Granted State) is from a CBSD with an unsupported protocol
    version by SAS.

    The response should be FAIL, code 100.
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

    # Save SAS version
    version = self._sas._sas_version
    # Use higher than supported version
    self._sas._sas_version = 'v2.0'

    # First Heartbeat with unsupported SAS-CBSD protocol version
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    try:
        response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
        # Check the heartbeat response
        self.assertEqual(response['response']['responseCode'], 100)
    except AssertionError as e:
        # Allow HTTP status 404
        self.assertEqual(e.args[0], 404)
    finally:
        # Put SAS version back
        self._sas._sas_version = version

  @winnforum_testcase
  def test_10_9_4_2_3_1_1(self):
    """CBSD heartbeat request with missing cbsdId parameter.

    Heartbeat request immediately after CBSD moves into Granted State. The
    cbsdId is missing in heartbeat request. The response should be FAIL.
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

    # First successful Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertLess(datetime.utcnow(),
                    datetime.strptime(response['transmitExpireTime'],
                                      '%Y-%m-%dT%H:%M:%SZ'))
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # cbsdId is missing
    request = {
        'heartbeatRequest': [{
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_10(self):
    """Initial Heartbeat Request (immediately after CBSD moves
    into Granted State) is from three CBSDs with an unsupported
    protocol version by SAS.

    The response should be FAIL, code 100.
    """

    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    request = {'registrationRequest': [device_a, device_b, device_c]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for resp in response:
        self.assertEqual(resp['response']['responseCode'], 0)
    cbsd_ids = [resp['cbsdId'] for resp in response]
    del request, response

    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[2]
    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(cbsd_ids))
    for resp_number, resp in enumerate(response):
        self.assertEqual(resp['cbsdId'], cbsd_ids[resp_number])
        self.assertTrue(resp['grantId'])
        self.assertEqual(resp['response']['responseCode'], 0)
    grant_ids = (response[0]['grantId'], response[1]['grantId'], response[2]['grantId'])
    del request, response

    # Save sas version
    version = self._sas._sas_version
    # Use higher than supported version
    self._sas._sas_version = 'v2.0'

    # First Heartbeat with unsupported SAS-CBSD protocol version
    heartbeat_0 = {
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }
    heartbeat_1 = {
        'cbsdId': cbsd_ids[1],
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }
    heartbeat_2 = {
        'cbsdId': cbsd_ids[2],
        'grantId': grant_ids[2],
        'operationState': 'GRANTED'
    }
    request = {'heartbeatRequest': [heartbeat_0, heartbeat_1, heartbeat_2]}
    try:
        response = self._sas.Heartbeat(request)['heartbeatResponse']
        self.assertEqual(len(response), len(grant_ids))
        for resp in response:
            try:
                # Check the heartbeat response
                self.assertEqual(resp['response']['responseCode'], 100)
            except AssertionError as e:
                # Allow HTTP status 404
                self.assertEqual(e.args[0], 404)
    finally:
        # Put sas version back
        self._sas._sas_version = version

  @winnforum_testcase
  def test_10_9_4_2_3_1_2(self):
    """CBSD heartbeat request with missing grantId parameter.

    Heartbeat request immediately after CBSD moves into Granted State. The
    grantId is missing in heartbeat request. The response should be FAIL.
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

    # First successful Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertLess(datetime.utcnow(),
                    datetime.strptime(response['transmitExpireTime'],
                                      '%Y-%m-%dT%H:%M:%SZ'))
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # grantId is missing
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_10_9_4_2_3_1_3(self):
    """CBSD heartbeat request with missing operationState parameter.

    Heartbeat request immediately after CBSD moves into Granted State. The
    operationState is missing in heartbeat request. The response should be FAIL.
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

    # First successful Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertLess(datetime.utcnow(),
                    datetime.strptime(response['transmitExpireTime'],
                                      '%Y-%m-%dT%H:%M:%SZ'))
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # operationState is missing
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_14(self):
    """CBSD heartbeat requests with various missing parameter.

    Heartbeat request immediately after CBSD moves into Granted State.
    Three requests out of the four have some needed parameter missing.
    The response should be FAIL.
    """

    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_b.json', 'device_c.json',
                            'device_d.json'):
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
          datetime.strptime(response[0]['grantExpireTime'],
                            '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Prepare Heartbeats (these are first heartbeats)
    # 1. valid, 2. no cbsd_id, 3. no grantId, 4. no operationState
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

    # Check the heartbeat response
    self.assertEqual(len(response), 4)
    # check the cbsdId and grantId where the request message had accurate values
    for response_num in (0, 3):
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(response[response_num]['grantId'],
                       grant_ids[response_num])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    transmit_expire_time = datetime.strptime(response[0]['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
    self.assertLess(datetime.utcnow(), transmit_expire_time)
    self.assertLessEqual(
        (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
    self.assertLess(transmit_expire_time, grant_expire_times[0])
    self.assertTrue(response[1]['response']['responseCode'] in (102, 105))
    for response_num in (2, 3):
      self.assertEqual(response[response_num]['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_15(self):
    """CBSD heartbeat request with invalid grantId parameter.

    Heartbeat request immediately after CBSD moves into Granted State. The
    grantId is invalid in heartbeat request. The response should be FAIL.
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
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response

    # First successful Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    transmit_expire_time_1 = datetime.strptime(response['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Send second heartbeat request with an invalid grantId
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id + '-changed',
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue(response['response']['responseCode'] in (103, 105))
    self.assertLessEqual(
        datetime.strptime(response['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ'),
        transmit_expire_time_1)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_18(self):
    """CBSD heartbeat requests with invalid parameter(s).

    Heartbeat request immediately after CBSD moves into Granted State.
    The requests have some parameter with invalid value
    The response should be FAIL.
    """

    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_b.json', 'device_c.json'):
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
    # No. 1,2 - valid requests, No. 3 - invalid grantId in request
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
    for response_num in (0, 1):
      self.assertEqual(response[response_num]['response']['responseCode'], 0)
      transmit_expire_time = datetime.strptime(
          response[response_num]['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
      self.assertLess(datetime.utcnow(), transmit_expire_time)
      self.assertLessEqual(
          (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
      self.assertLessEqual(transmit_expire_time,
                           grant_expire_times[response_num])
    self.assertEqual(response[2]['response']['responseCode'], 103)
    # No need to check transmitExpireTime because this is the first heartbeat

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_19(self):
    """Heartbeat Request from CBSD in Granted or Authorized state 
    (immediately after CBSD moves into Granted State or following
     a Heartbeat Response) requires CBSD to de-register. 

    The response should be FAIL, code 105."""

    # Register the device
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})

    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant_0]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue(response['grantId'])
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response

    # Inject Device into Blacklist
    self._sas_admin.BlacklistByFccId({'fccId': device_a['fccId']})

    # Request Heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the first heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertEqual(response['response']['responseCode'], 105)

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_20(self):
    """Heartbeat Request from CBSDs in Granted or Authorized state 
    (immediately after CBSDs moves into Granted State or following
     a Heartbeat Response) requires CBSDs to de-register. 

    The response should be FAIL, code 105.
    """
    # Register the devices
    registration_request = []
    fcc_ids = []
    for device_filename in ('device_a.json', 'device_b.json', 'device_c.json'):
      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      fcc_ids.append(device['fccId'])
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      registration_request.append(device)

    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
    cbsd_ids = [resp['cbsdId'] for resp in response]
    del request, response

    # Request grant
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
      grant['cbsdId'] = cbsd_id
      grant_request.append(grant)
    request = {'grantRequest': grant_request}

    # Check grant response
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(cbsd_ids))
    grant_expire_time = []
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[resp_number])
      self.assertTrue(resp['grantId'])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_expire_time.append(
        datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))

    grant_ids = [resp['grantId'] for resp in response]
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
    # First two devices are not in Blacklist must have Response Code 0
    for index, resp in enumerate(response[:2]):
      self.assertEqual(resp['cbsdId'], cbsd_ids[index])
      self.assertEqual(resp['grantId'], grant_ids[index])
      transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
      self.assertLess(datetime.utcnow(), transmit_expire_time)
      self.assertLessEqual(
        (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
      self.assertLessEqual(transmit_expire_time,
                           grant_expire_time[index])
      self.assertEqual(resp['response']['responseCode'], 0)

    # Last Device in Blacklist must have Response Code 105
    self.assertEqual(response[2]['cbsdId'], cbsd_ids[2])
    self.assertEqual(response[2]['grantId'], grant_ids[2])
    self.assertEqual(response[2]['response']['responseCode'], 105)

