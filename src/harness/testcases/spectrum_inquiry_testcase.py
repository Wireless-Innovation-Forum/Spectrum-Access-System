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

    # Send Spectrum Inquiry request.
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    self.assertFalse('cbsdId' in spectrum_inquiry_0)
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertFalse('cbsdId' in response)
    self.assertTrue(response['response']['responseCode'] == 102 or
                    response['response']['responseCode'] == 105)

  @winnforum_testcase
  def test_WINFF_FT_S_SIQ_9(self):
    """Send Spectrum Inquiry with missing frequencyRange object.

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
    self.assertTrue('cbsdId' in response)
    cbsd_id = response['cbsdId']
    del request, response

    # Send Spectrum Inquiry request
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id
    del spectrum_inquiry_0['inquiredSpectrum']
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertTrue('cbsdId' in response)
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
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertTrue('cbsdId' in response)
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINFF_FT_S_SIQ_11(self):
    """Send Spectrum Inquiry with missing lowFrequency parameter.

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
    del spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency']
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertTrue('cbsdId' in response)
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINFF_FT_S_SIQ_14(self):
    """Send Spectrum Inquiry with mutually invalid set of parameters.

    The response should be INVALID_PARAM, code 103
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

    # Create and send Spectrum Inquiry request
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id
    # Swap low and high frequencies to create an invalid range.
    (spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'],
     spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency']) = (
         spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency'],
         spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'])
    self.assertLess(
        spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'],
        spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency'])
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Send the request
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    # Check Spectrum Inquiry Response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINFF_FT_S_SIQ_15(self):
    """Send Spectrum Inquiry with unsupported spectrum.

    The response should be INVALID_PARAM, code 300
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
    spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency'] = 3780000000.0
    spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'] = 3790000000.0
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertEqual(response['response']['responseCode'], 300)
