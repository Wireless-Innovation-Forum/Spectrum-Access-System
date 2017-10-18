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
import sas
import sas_testcase
from util import winnforum_testcase, getRandomLatLongInPolygon, \
  makePpaAndPalRecordsConsistent


class SpectrumInquiryTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_11(self):
    """Unsupported frequency range inquiry array.

    The response for Inquiry #2 should be UNSUPPORTED_SPECTRUM, code 300
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})

    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    self._sas_admin.InjectUserId({'userId': device_c['userId']})

    request = {'registrationRequest': [device_a, device_c]}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # 1. Spectrum Inquiry: All parameters valid.
    spectrum_inquiry_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_1['cbsdId'] = cbsd_ids[0]

    # 2. Spectrum Inquiry: lowFrequency & highFrequency outside 3550 - 3700 MHz.
    spectrum_inquiry_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_2['cbsdId'] = cbsd_ids[1]
    spectrum_inquiry_2['inquiredSpectrum'] = [{
        'lowFrequency': 3300000000.0,
        'highFrequency': 3350000000.0
    }]

    request = {
        'spectrumInquiryRequest': [spectrum_inquiry_1, spectrum_inquiry_2]
    }
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']

    self.assertEqual(len(response), 2)
    # Check Spectrum Inquiry Response #1
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertTrue('availableChannel' in response[0])
    for available_channel in response[0]['availableChannel']:
      self.assertEqual(available_channel['ruleApplied'], 'FCC_PART_96')
    self.assertEqual(response[0]['response']['responseCode'], 0)

    # Check Spectrum Inquiry Response #2
    self.assertEqual(response[1]['cbsdId'], cbsd_ids[1])
    self.assertFalse('availableChannel' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 300)
