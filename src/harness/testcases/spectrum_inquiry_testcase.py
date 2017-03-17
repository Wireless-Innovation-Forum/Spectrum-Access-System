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


class SpectrumInquiryTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def test_10_5_4_1_1_3(self):
    """Include the entire CBRS band in the spectrumInquiryRequest

    This test ensures that SAS is able to handle spectrum inquiry of
    the entire CBRS band.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request spectrum inquiry
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id
    spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency']  = 3550000000.0
    spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'] = 3700000000.0
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    # Check spectrum inquiry response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
