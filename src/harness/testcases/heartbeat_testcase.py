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
