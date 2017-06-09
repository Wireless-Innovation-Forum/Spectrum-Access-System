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
  def test_WINNF_FT_S_MES_1(self):
    """The sas under test to request measurement reporting

    Register cbsds 6 CBSDs with measCapability make sure the SAS request 
    The measurement report config.
    """

    # Load the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    devices = [device_a, device_b, device_c, device_d, device_e, device_f]

    for device in devices:
        # set meascapability for all devices
        device['measCapability'] = ['RECEIVED_POWER_WITHOUT_GRANT']
        # Inject FCC IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})

    # Trigger to request measurement report for spectrum Inquery and grant request
    self._sas_admin.TriggerMeasurementReportRegistration({'measReportConfig':
                                                       ['RECEIVED_POWER_WITHOUT_GRANT']})
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

    # Create Spectrum Inquiry request  for the six devices
    spectrum_inquiries = []
    for cbsd_id in cbsd_ids:
        spectrum_inquiry = {}
        spectrum_inquiry['cbsdId'] = cbsd_id
        meas_report = json.load(
            open(os.path.join('testcases', 'testdata', 'meas_report_1.json')))
        # Delete measRcvdPower for second devide
        if cbsd_id == cbsd_ids[1]:
            for meas_num, meas in enumerate(meas_report):
                del meas_report[meas_num]['measRcvdPower']
        # For the third device build array of 10 element for measReport
        if cbsd_id == cbsd_ids[2]:
            meas_report = meas_report[:10]
        # For the 6th device set measBandwidth to 15000000 Hz
        if cbsd_id == cbsd_ids[5]:
            for meas_num, meas in enumerate(meas_report):
                meas_report[meas_num]['measBandwidth'] = 15000000
        spectrum_inquiry['measReport'] =  {'rcvdPowerMeasReport': meas_report}

        # Delete RcvdPowerMeasReport for the 4th device
        if cbsd_id == cbsd_ids[3]:
            del spectrum_inquiry['measReport']['rcvdPowerMeasReport']
        # Delete MeasReport for the 5th device
        if cbsd_id == cbsd_ids[4]:
            del spectrum_inquiry['measReport']

        spectrum_inquiry['inquiredSpectrum'] = [{
            'lowFrequency': 3550000000.0,
            'highFrequency': 3560000000.0
        }]
        spectrum_inquiries.append(spectrum_inquiry)
    del request, response
    request = {
        'spectrumInquiryRequest': spectrum_inquiries
    }
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    self.assertTrue('cbsdId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[5]['response']['responseCode'], 103)
    """ for resp in response[1:4]
    self.assertEqual(resp['response']['responseCode'], 102)"""
    del request, response
    # Create Grant Request for the six devices with frequency range 3550-3560 MHz
    grant_request = []

    # Get measReport of CBSDs from spectrum_inquiries
    for meas_num, meas_report in enumerate(spectrum_inquiries):
        grant_0 = json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_0['operationParam']['operationFrequencyRange'][
            'lowFrequency'] = 3550000000.0
        grant_0['operationParam']['operationFrequencyRange'][
            'highFrequency'] = 3560000000.0
        grant_0['cbsdId'] = meas_report['cbsdId']
    	if 'measReport' in meas_report:
        	grant_0['measReport'] = meas_report['measReport']
    	grant_request.append(grant_0);
    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertTrue('cbsdId' in response[0])
    self.assertTrue('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[5]['response']['responseCode'], 103)
    for resp in response[1:4]:
        self.assertEqual(resp['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_MES_2(self):
    """The sas under test to request measurement reporting

    Register CBSDs 5 devices with measCapability make sure the SAS request 
    The measurement report config.
    """
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    devices = [device_a, device_b, device_c, device_d, device_e]

    for device in devices:
        # set meascapability for all devices
        device['measCapability'] = ['RECEIVED_POWER_WITH_GRANT']
        # Inject FCC IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
    cbsd_ids = []
    # Register devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for resp in response:
        self.assertTrue('cbsdId' in resp)
        #self.assertEqual(resp['measReportConfig'], 'EUTRA_CARRIER_RSSI_ALWAYS')
        self.assertTrue('EUTRA_CARRIER_RSSI_ALWAYS' in resp['measReportConfig'])
        self.assertEqual(resp['response']['responseCode'], 0)
        cbsd_ids.append(resp['cbsdId'])

    # Request grant
    grant_request = []
    for cbsd_id in cbsd_ids:
        grant_0 = json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_0['operationParam']['operationFrequencyRange'][
            'lowFrequency'] = 3620000000.0
        grant_0['operationParam']['operationFrequencyRange'][
            'highFrequency'] = 3630000000.0  
        grant_0['cbsdId'] = cbsd_id
        grant_request.append(grant_0)
    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']

    grant_ids = []
    # Check grant response
    for response_num, resp in enumerate(response):
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertTrue('grantId' in resp)
        self.assertEqual(resp['response']['responseCode'], 0)
        grant_ids.append(resp['grantId'])

    # Trigger to request measurement report for all subsequent heartbeat request
    self._sas_admin.TriggerMeasurementReportRegistration({'measReportConfig':
                                                       ['RECEIVED_POWER_WITH_GRANT']})
    # Heartbeat the devices without measReport
    heartbeat_request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        heartbeat_request.append({
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        })
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    for response_num, resp in enumerate(response):
        self.assertEqual(resp['response']['responseCode'], 0)
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['grantId'], grant_ids[response_num])
        transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                             '%Y-%m-%dT%H:%M:%SZ')
        self.assertLess(datetime.utcnow(), transmit_expire_time)
        self.assertLessEqual(
            (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
        self.assertTrue('RECEIVED_POWER_WITH_GRANT' in resp['measReportConfig'])

    # Heartbeat the devices with measReport
    heartbeat_requests = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        meas_report = json.load(
            open(os.path.join('testcases', 'testdata', 'meas_report_0.json')))
        heartbeat_request = {}
        heartbeat_request['cbsdId'] = cbsd_id
        heartbeat_request['grantId'] = grant_id
        heartbeat_request['operationState'] = 'AUTHORIZED'
        heartbeat_request['measReport'] = meas_report
        if cbsd_id == cbsd_ids[1]:
            # Delete measFrequency for second devide
            del heartbeat_request['measReport']['rcvdPowerMeasReport'][0]['measFrequency']
        if cbsd_id == cbsd_ids[2]:
            # Set measFrequency to 3540 MHZ for 3th device
            heartbeat_request['measReport']['rcvdPowerMeasReport'][0]['measFrequency'] = 3540000000.0
        if cbsd_id == cbsd_ids[3]:
            # Delete rcvdPowerMeasReport for 4th device
            del heartbeat_request['measReport']['rcvdPowerMeasReport'][0]
        if cbsd_id == cbsd_ids[4]:
            # Delete measReport for 5th device
            del heartbeat_request['measReport']
        heartbeat_requests.append(heartbeat_request)
    request = {'heartbeatRequest': heartbeat_requests}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 102)
    self.assertEqual(response[2]['response']['responseCode'], 103)
    self.assertEqual(response[3]['response']['responseCode'], 102)
    self.assertEqual(response[4]['response']['responseCode'], 102)
