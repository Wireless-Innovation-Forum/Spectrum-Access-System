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

import json
import os
import unittest
from datetime import datetime

from six.moves import zip

import sas
from util import winnforum_testcase, json_load


class MeasurementTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_MES_1(self):
    """The sas under test to request measurement reporting
    Register cbsds 6 CBSDs with measCapability make sure the SAS request
    The measurement report config.
    """

    # Load the devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    device_f = json_load(
        os.path.join('testcases', 'testdata', 'device_f.json'))
    device_g = json_load(
        os.path.join('testcases', 'testdata', 'device_g.json'))
    device_i = json_load(
        os.path.join('testcases', 'testdata', 'device_i.json'))
    devices = [device_a, device_c, device_e, device_f, device_g, device_i]

    for device in devices:
        # set meascapability for all devices to 'RECEIVED_POWER_WITHOUT_GRANT'
        device['measCapability'] = ['RECEIVED_POWER_WITHOUT_GRANT']
        # Inject FCC and user IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
        self._sas_admin.InjectUserId({'userId': device['userId']})

    # Trigger to request measurement report for spectrum Inquery and grant request
    self._sas_admin.TriggerMeasurementReportRegistration()
    cbsd_ids = []
    # Register devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for resp in response:
        self.assertTrue('cbsdId' in resp)
        self.assertTrue('RECEIVED_POWER_WITHOUT_GRANT' in resp['measReportConfig'])
        self.assertEqual(resp['response']['responseCode'], 0)
        cbsd_ids.append(resp['cbsdId'])

    del request, response
    # Create Spectrum Inquiry request  for the six devices
    spectrum_inquiries = []
    for cbsd_id in cbsd_ids:
        spectrum_inquiry = {}
        spectrum_inquiry['cbsdId'] = cbsd_id
        meas_report = json_load(
            os.path.join('testcases', 'testdata', 'meas_report_1.json'))
        spectrum_inquiry['measReport'] =  {'rcvdPowerMeasReports': meas_report}
        # Delete measRcvdPower for second devide
        if cbsd_id == cbsd_ids[1]:
            for meas_num, meas in enumerate(meas_report):
                del meas_report[meas_num]['measRcvdPower']
        # For the third device build array of 10 element for measReport
        elif cbsd_id == cbsd_ids[2]:
            spectrum_inquiry['measReport'] =  {'rcvdPowerMeasReports': meas_report[:10]}
        # Delete rcvdPowerMeasReports for the 4th device
        elif cbsd_id == cbsd_ids[3]:
            del spectrum_inquiry['measReport']['rcvdPowerMeasReports']
        # Delete MeasReport for the 5th device
        elif cbsd_id == cbsd_ids[4]:
            del spectrum_inquiry['measReport']
        # For the 6th device set measBandwidth to 15000000 Hz
        elif cbsd_id == cbsd_ids[5]:
            for meas_num, meas in enumerate(meas_report):
                meas_report[meas_num]['measBandwidth'] = 15000000
        spectrum_inquiry['inquiredSpectrum'] = [{
            'lowFrequency': 3550000000,
            'highFrequency': 3560000000
        }]
        spectrum_inquiries.append(spectrum_inquiry)
    # Send Spectrum Inquiry request
    request = {'spectrumInquiryRequest': spectrum_inquiries}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    # Check Spectrum Inquiry response
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    for resp in response[1:5]:
        self.assertEqual(resp['response']['responseCode'], 102)
    self.assertEqual(response[5]['response']['responseCode'], 103)

    # Create Grant Request for the six devices
    grant_request = []
    for spectrum_num, spectrum_inquiry in enumerate(spectrum_inquiries):
        grant_0 = json_load(
            os.path.join('testcases', 'testdata', 'grant_0.json'))
        grant_0['operationParam']['operationFrequencyRange'][
            'lowFrequency'] = 3550000000
        grant_0['operationParam']['operationFrequencyRange'][
            'highFrequency'] = 3560000000
        grant_0['cbsdId'] = spectrum_inquiry['cbsdId']
        if 'measReport' in spectrum_inquiry:
            grant_0['measReport'] = spectrum_inquiry['measReport']
        grant_request.append(grant_0)
    # Send Grant Request
    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    # Check Spectrum Inquiry response
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertTrue('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    for resp in response[1:5]:
        self.assertEqual(resp['response']['responseCode'], 102)
    self.assertEqual(response[5]['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_MES_2(self):
    """The sas under test to request measurement reporting
    Register cbsds 5 CBSDs with measCapability make sure the SAS request 
    The measurement report config after for heartbeat.
    """

    # Load the devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    device_f = json_load(
        os.path.join('testcases', 'testdata', 'device_f.json'))
    device_i = json_load(
        os.path.join('testcases', 'testdata', 'device_i.json'))
    devices = [device_a, device_c, device_e, device_f, device_i]

    for device in devices:
        device['measCapability'] = ['RECEIVED_POWER_WITH_GRANT']
        # Inject FCC and user IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
        self._sas_admin.InjectUserId({'userId': device['userId']})

    device_i['measCapability'] = ['RECEIVED_POWER_WITHOUT_GRANT']
    cbsd_ids = []

    # Register devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertEqual(len(response), 5)
    for resp in response:
        self.assertTrue('cbsdId' in resp)
        self.assertEqual(resp['response']['responseCode'], 0)
        if 'measReportConfig' in resp:
            self.assertFalse('RECEIVED_POWER_WITH_GRANT' in resp['measReportConfig'])
        cbsd_ids.append(resp['cbsdId'])
    # Check if SAS ask meas_report for the fifth device
    ask_meas_report = False
    if 'measReportConfig' in response[4] and 'RECEIVED_POWER_WITHOUT_GRANT' in response[4]['measReportConfig']:
        ask_meas_report = True
    del request, response

    # Request grant
    grant_request = []
    for cbsd_id in cbsd_ids:
        grant = json_load(
            os.path.join('testcases', 'testdata', 'grant_0.json'))
        grant['cbsdId'] = cbsd_id
        # Add meas_report for the fifth device if needed
        if grant['cbsdId'] == cbsd_ids[4] and ask_meas_report:
            meas_report = json_load(
                os.path.join('testcases', 'testdata', 'meas_report_1.json'))
            grant['measReport'] =  {'rcvdPowerMeasReports': meas_report}
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
    self._sas_admin.TriggerMeasurementReportHeartbeat()

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
            self.assertTrue('RECEIVED_POWER_WITH_GRANT' in resp['measReportConfig'])
        else:
            self.assertFalse('measReportConfig' in resp)
    # Second heartbeat request with measReport
    heartbeat_requests = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        meas_report = json_load(
            os.path.join('testcases', 'testdata', 'meas_report_0.json'))
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
            heartbeat_request['measReport']['rcvdPowerMeasReports'][0]['measFrequency'] = 3540000000
        # Delete rcvdPowerMeasReports for 4th device
        elif cbsd_id == cbsd_ids[3]:
            del heartbeat_request['measReport']['rcvdPowerMeasReports']
        # Delete measReport for 5th device
        elif cbsd_id == cbsd_ids[4]:
            del heartbeat_request['measReport']
        heartbeat_requests.append(heartbeat_request)

    request = {'heartbeatRequest': heartbeat_requests}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check second heartbeat response
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 102)
    self.assertEqual(response[2]['response']['responseCode'], 103)
    self.assertEqual(response[3]['response']['responseCode'], 102)
    self.assertEqual(response[4]['response']['responseCode'], 0)
