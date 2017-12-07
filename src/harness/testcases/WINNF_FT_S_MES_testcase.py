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
from datetime import datetime


class MeasurementTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_MES_2(self):
    """The sas under test to request measurement reporting
    Register cbsds 6 CBSDs with measCapability make sure the SAS request 
    The measurement report config after for heartbeat.
    """

    # Load the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    device_g = json.load(
        open(os.path.join('testcases', 'testdata', 'device_g.json')))
    device_i = json.load(
        open(os.path.join('testcases', 'testdata', 'device_i.json')))
    devices = [device_a, device_c, device_e, device_f, device_g, device_i]

    for device in devices:
        device['measCapability'] = ['RECEIVED_POWER_WITH_GRANT']
        # Inject FCC and user IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
        self._sas_admin.InjectUserId({'userId': device['userId']})

    device_f['measCapability'] = ['RECEIVED_POWER_WITHOUT_GRANT']
    cbsd_ids = []

    # Register devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertEqual(len(response), 6)
    for resp in response:
        self.assertTrue('cbsdId' in resp)
        self.assertEqual(resp['response']['responseCode'], 0)
        self.assertFalse('RECEIVED_POWER_WITH_GRANT' in resp['measReportConfig'])
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
    response = self._sas.Grant(request)['grantResponse']

    grant_ids = []
    # Check grant response
    for response_num, resp in enumerate(response):
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertTrue('grantId' in resp)
        self.assertEqual(resp['response']['responseCode'], 0)
        grant_ids.append(resp['grantId'])
    del request, response
    
    # Trigger to request measurement report for all subsequent heartbeat request
    self._sas_admin.TriggerMeasurementReportHeartbeat({'measReportConfig':[]})
    
    # First heartbeat without measReport
    heartbeat_request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        heartbeat_request.append({
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        })
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check first heartbeat response
    for response_num, resp in enumerate(response):
        self.assertEqual(resp['response']['responseCode'], 0)
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['grantId'], grant_ids[response_num])
        transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
        self.assertLess(datetime.utcnow(), transmit_expire_time)
        if response_num != len(response) - 1:
            self.assertEqual(resp['measReportConfig'], 'RECEIVED_POWER_WITH_GRANT')
        else:
            self.assertFalse('measReportConfig' in resp)
    # Second heartbeat request with measReport
    heartbeat_requests = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        meas_report = json.load(
            open(os.path.join('testcases', 'testdata', 'meas_report_0.json')))
        heartbeat_request = {}
        heartbeat_request['cbsdId'] = cbsd_id
        heartbeat_request['grantId'] = grant_id
        heartbeat_request['operationState'] = 'AUTHORIZED'
        heartbeat_request['measReport'] = meas_report
        # Delete measFrequency for second device
        if cbsd_id == cbsd_ids[1]:
            del heartbeat_request['measReport']['rcvdPowerMeasReports'][0]['measFrequency']
        # Set measFrequency to 3540 MHZ for 3th device
        elif cbsd_id == cbsd_ids[2]:
            heartbeat_request['measReport']['rcvdPowerMeasReports'][0]['measFrequency'] = 3540000000.0
        # Delete rcvdPowerMeasReports for 4th device
        elif cbsd_id == cbsd_ids[3]:
            del heartbeat_request['measReport']['rcvdPowerMeasReports']
        # Delete measReport for devices 5 and 6
        elif cbsd_id in (cbsd_ids[4], cbsd_ids[5]):
            del heartbeat_request['measReport']
        heartbeat_requests.append(heartbeat_request)

    request = {'heartbeatRequest': heartbeat_requests}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check second heartbeat response
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 102)
    self.assertEqual(response[2]['response']['responseCode'], 103)
    self.assertEqual(response[3]['response']['responseCode'], 102)
    self.assertEqual(response[4]['response']['responseCode'], 102)
    self.assertEqual(response[5]['response']['responseCode'], 0)