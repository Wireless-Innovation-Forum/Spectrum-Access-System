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
  def test_WINNF_FT_S_HBT_2(self):
    """Array Request: Heartbeat request from 3 CBSDs for GRANT renewal.

    Returns response code 0.
    """
    # Register three devices.
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json', 'device_e.json'):
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

    # Request grants.
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

    # Request grants.
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
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[resp_number])
      self.assertTrue(resp['grantId'])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    # Use higher than supported version.
    self._sas._sas_version = 'v2.0'

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

    except AssertionError as e:
      # Allow HTTP status 404.
      self.assertEqual(e.args[0], 404)
