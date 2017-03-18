import json
import os
import unittest

import sas
from util import winnforum_testcase


class SpectrumInquiryTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINFF_FT_S_SIQ_8(self):
    """Send Spectrum Inquiry with missing cbsdId field.

    The response should be MISSING_PARAM, code 102
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Send Spectrum Inquiry request
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    self.assertFalse('cbsdId' in spectrum_inquiry_0)
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINFF_FT_S_SIQ_10(self):
    """Send Spectrum Inquiry with missing highFrequency parameter.

    The response should be MISSING_PARAM, code 102
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

    # Send Spectrum Inquiry request
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id
    del spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency']
    self.assertFalse(
        'highFrequency' in spectrum_inquiry_0['inquiredSpectrum'][0])
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertEqual(response['response']['responseCode'], 102)
