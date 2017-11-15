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
  def test_WINNF_FT_S_SIQ_5(self):
    """Tests related to PAL Protection Area (PPA)

	SAS sending responseCode = 0 successful response
	without include the frequency range of PPA
    """
    # Load PAL Database Record
    pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    # Load PPA record
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))

    pal_low_frequency = 3620000000.0
    pal_high_frequency = 3630000000.0
    pal_user_id = "pal_user"

    # Make PPA and PAL records consistent
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,[pal_record],\
        pal_low_frequency,pal_high_frequency,pal_user_id)

    # Inject PAL record record
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    # Inject PPA record
    self._sas_admin.InjectZoneData({"record": ppa_record})

    # Trigger daily activities and wait for it to be completed
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Load CBSD info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Change device location to be inside PPA
    device_a['installationParam']['latitude'], \
    device_a['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record)

    # Register device
    cbsd_ids = self.assertRegistered([device_a])

    # Create spectrumInquiry with the frequency range full overlaps with PAL frequency
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_ids[0]
    spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency'] = \
                pal_record[0]['channelAssignment']['primaryAssignment']['lowFrequency']
    spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'] = \
                pal_record[0]['channelAssignment']['primaryAssignment']['highFrequency']

    # Check : Check spectrum inquiry response
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertFalse('availableChannel' in response)
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_6(self):
    """cbsdId sent in Spectrum Inquiry is non-existent and not the assigned one.

    The response should be INVALID_VALUE, code 103.
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]

    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Send Spectrum Inquiry request
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id + '-changed'
    self.assertNotEqual(cbsd_id, spectrum_inquiry_0['cbsdId'])
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}

    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertFalse('cbsdId' in response)
    self.assertTrue(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_7(self):
    """cbsdId different from its assigned cbsdId and the cbsdId exists in the SAS.

    SAS rejects the request by sending responseCode = 103 or 105 
    """
    # Load device_a [cert|key]
    device_a_cert = os.path.join('certs', 'device_a.cert')
    device_a_key = os.path.join('certs', 'device_a.key')

    # Register the first device with certificates
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request, device_a_cert,
                                      device_a_key)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id_a = response['cbsdId']
    del request, response

    # Load device_c [cert|key]
    device_c_cert = os.path.join('certs', 'device_c.cert')
    device_c_key = os.path.join('certs', 'device_c.key')

    # Register the second device with certificates
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    request = {'registrationRequest': [device_c]}
    response = self._sas.Registration(request, device_c_cert,
                                      device_c_key)['registrationResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id_c = response['cbsdId']
    del request, response

    # Create Spectrum Inquiry and Send request for device_a using device_c_cert and device_c_key
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id_a

    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    response = self._sas.SpectrumInquiry(request, device_c_cert, device_c_key)['spectrumInquiryResponse'][0]
    # Check Spectrum Inquiry Response
    self.assertFalse('cbsdId' in response)
    self.assertTrue(response['response']['responseCode'] == 103 or
                    response['response']['responseCode'] == 104)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_8(self):
    """Parameters in Inquired Spectrum mutually invalid.

    The response should be INVALID_VALUE, code 103.
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
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
  def test_WINNF_FT_S_SIQ_11(self):
    """Unsupported frequency range inquiry array.

    The response for Inquiry #2 and #3 should be UNSUPPORTED_SPECTRUM, code 300
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))

    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_e['fccId']})

    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    self._sas_admin.InjectUserId({'userId': device_c['userId']})
    self._sas_admin.InjectUserId({'userId': device_e['userId']})

    request = {'registrationRequest': [device_a, device_c, device_e]}
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

    # 2. Spectrum Inquiry: lowFrequency & highFrequency fully
    #    outside 3550 - 3700 MHz.
    spectrum_inquiry_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_2['cbsdId'] = cbsd_ids[1]
    spectrum_inquiry_2['inquiredSpectrum'] = [{
        'lowFrequency': 3300000000,
        'highFrequency': 3350000000
    }]

    # 3. Spectrum Inquiry: lowFrequency & highFrequency partially
    #    outside 3550 - 3700 MHz.
    spectrum_inquiry_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_3['cbsdId'] = cbsd_ids[2]
    spectrum_inquiry_3['inquiredSpectrum'] = [{
        'lowFrequency': 3600000000,
        'highFrequency': 3800000000
    }]

    request = {
        'spectrumInquiryRequest': [
            spectrum_inquiry_1, spectrum_inquiry_2, spectrum_inquiry_3
        ]
    }
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']

    self.assertEqual(len(response), 3)
    # Check Spectrum Inquiry Response #1
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertTrue('availableChannel' in response[0])
    for available_channel in response[0]['availableChannel']:
      self.assertEqual(available_channel['ruleApplied'], 'FCC_PART_96')
    self.assertEqual(response[0]['response']['responseCode'], 0)
    # Check Spectrum Inquiry Response #2 and #3
    for response_num in (1, 2):
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertFalse('availableChannel' in response[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 300)
