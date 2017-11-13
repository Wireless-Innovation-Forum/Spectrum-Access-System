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
import sas
import sas_testcase
from util import winnforum_testcase


class HeartbeatTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

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

