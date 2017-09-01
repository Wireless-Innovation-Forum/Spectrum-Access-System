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
import sas_testcase
import sas
from util import winnforum_testcase, getRandomLatLongInPolygon, \
  makePpaAndPalRecordsConsistent


class SpectrumInquiryTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_4(self):
    """Send Spectrum Inquiry from inside coastal exclusion zone.
       With no ESC deployed, use a Category A device to request Spectrum
       Inquiry.

    The response should be Success, with NO channels in result.
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    # Locate this device close to coast (Half Moon Bay, Calif.)
    device_a['installationParam']['latitude'] = 37.444267
    device_a['installationParam']['longitude'] = -122.428628
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Query for the spectrum affected by the coastal exclusion zone, i.e.
    # 3550-3650 MHz.
    spectrum_inquiry_0 = {
        'cbsdId': cbsd_id,
        'inquiredSpectrum': [{
            'lowFrequency': 3550000000.0,
            'highFrequency': 3650000000.0
        }]
    }
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check spectrum inquiry response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(len(response['availableChannel']), 0)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_8(self):
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
  def test_WINNF_FT_S_SIQ_9(self):
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
  def test_WINNF_FT_S_SIQ_10(self):
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
  def test_WINNF_FT_S_SIQ_11(self):
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
  def test_WINNF_FT_S_SIQ_12(self):
    """Send Spectrum Inquiry with non-existent cbsdId parameter.

    The response should be INVALID_VALUE, code 103
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
    spectrum_inquiry_0['cbsdId'] = cbsd_id + '-changed'
    self.assertNotEqual(cbsd_id, spectrum_inquiry_0['cbsdId'])
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertFalse('cbsdId' in response)
    self.assertTrue(response['response']['responseCode'] in (103, 105))

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_13(self):
    """Send Spectrum Inquiry from cbsdId different from its assigned cbsdId,
        SAS should reject Spectrum inquiry.

    The responseCode should be (103, 105), with NO channels in result.
    """
    device_a_cert = os.path.join('certs', 'device_a.cert')
    device_a_key = os.path.join('certs', 'device_a.key')

    device_c_cert = os.path.join('certs', 'device_c.cert')
    device_c_key = os.path.join('certs', 'device_c.key')
    # Checks that devices certificate are valid (checking all chain).
    self.assertValidClientCertificate(device_a_cert, sas.CA_CERT)
    self.assertValidClientCertificate(device_c_cert, sas.CA_CERT)

    # Registers the device with valid certificates.
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

    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    request = {'registrationRequest': [device_c]}
    response = self._sas.Registration(request, device_c_cert,
                                      device_c_key)['registrationResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id_c = response['cbsdId']
    del request, response

    # Create Spectrum Inquiry request for device_a using device_c_cert and device_c_key
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id_a
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request, device_c_cert, device_c_key)['spectrumInquiryResponse'][0]
    self.assertFalse('cbsdId' in response)
    self.assertTrue(response['response']['responseCode'] == 103 or
                    response['response']['responseCode'] == 105)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_14(self):
    """Send Spectrum Inquiry with mutually invalid set of parameters.

    The response should be INVALID_VALUE, code 103
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
  def test_WINNF_FT_S_SIQ_15(self):
    """Send Spectrum Inquiry with unsupported spectrum.

    The response should be INVALID_VALUE, code 300
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

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_16(self):
    """Send Spectrum Inquiry dual requests (GAA- successful case).

    The response should be NO_ERROR, code 0
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    request = {'registrationRequest': [device_a, device_b]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertEqual(len(response), 2)
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Create Spectrum Inquiry requests, setting freq. ranges to 3550-3700 MHz
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_ids[0]
    spectrum_inquiry_0['inquiredSpectrum'] = [{
        'lowFrequency': 3550000000.0,
        'highFrequency': 3700000000.0
    }]
    spectrum_inquiry_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_1['cbsdId'] = cbsd_ids[1]
    spectrum_inquiry_1['inquiredSpectrum'] = [{
        'lowFrequency': 3550000000.0,
        'highFrequency': 3700000000.0
    }]
    request = {
        'spectrumInquiryRequest': [spectrum_inquiry_0, spectrum_inquiry_1]
    }
    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    self.assertEqual(len(response), 2)
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[resp_number])
      self.assertTrue('availableChannel' in resp)
      for available_channel in resp['availableChannel']:
        self.assertEqual(available_channel['channelType'], 'GAA')
        self.assertEqual(available_channel['ruleApplied'], 'FCC_PART_96')
      self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_17(self):
    """This test ensures that when a message with two requests, 
    both for PAL channels, is sent with valid parameters, 
    the SAS sends a successful response for both the requests.
    Response Code must be 0 for all CBSDs
    """

    # Load the Data
    pal_low_frequency = 3550000000.0
    pal_high_frequency = 3560000000.0
    registration_request = []
    ppa_records = []
    pal_records = []
    for device_filename, pal_filename, ppa_filename in zip(
      ('device_a.json', 'device_c.json'),
      ('pal_record_0.json', 'pal_record_1.json'),
      ('ppa_record_0.json', 'ppa_record_1.json')):

      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      pal_record = json.load(
        open(os.path.join('testcases', 'testdata', pal_filename)))
      ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', ppa_filename)))
      ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,
                                                              [pal_record],
                                                              pal_low_frequency,
                                                              pal_high_frequency,
                                                              device['userId'])

      # Move the Device to a random location in PPA
      device['installationParam']['latitude'], \
      device['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record)
      ppa_records.append(ppa_record)
      pal_records.append(pal_record[0])
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      registration_request.append(device)

    # Register the devices
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    for ppa_record, pal_record, cbsd_id in zip(ppa_records, pal_records, cbsd_ids):
      # Update PPA Record with CBSD ID and Inject Data
      ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_id]
      self._sas_admin.InjectPalDatabaseRecord(pal_record)
      self._sas_admin.InjectZoneData({"record": ppa_record})

    # Trigger daily activities and wait for it to get it complete
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Create Spectrum Inquiry requests, setting freq. ranges to 3550-3700 MHz
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_ids[0]
    spectrum_inquiry_0['inquiredSpectrum'] = [{
        'lowFrequency': 3550000000.0,
        'highFrequency': 3700000000.0
    }]
    spectrum_inquiry_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_1['cbsdId'] = cbsd_ids[1]
    spectrum_inquiry_1['inquiredSpectrum'] = [{
        'lowFrequency': 3550000000.0,
        'highFrequency': 3700000000.0
    }]
    request = {
        'spectrumInquiryRequest': [spectrum_inquiry_0, spectrum_inquiry_1]
    }

    # Check Spectrum Inquiry Response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    self.assertEqual(len(response), 2)
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[resp_number])
      self.assertTrue('availableChannel' in resp)
      self.assertTrue(any(channel['channelType'] == 'PAL'
                          for channel in resp['availableChannel']))
      self.assertTrue(all(channel['ruleApplied'] == 'FCC_PART_96'
                          for channel in resp['availableChannel']))
      self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_19(self):
    """Send Spectrum Inquiry with dual requests #1 successful #2 unsuccessful.

    The response should be NO_ERROR (code 0) and INVALID_VALUE, code 103
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    request = {'registrationRequest': [device_a, device_b]}
    response = self._sas.Registration(request)['registrationResponse']
    cbsd_ids = []
    # Check registration response
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Create Spectrum Inquiry requests
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_ids[0]
    # Use invalid range for the second spectrum inquiry request
    spectrum_inquiry_1 = {
        'cbsdId': cbsd_ids[1],
        'inquiredSpectrum': [{
            'lowFrequency': 3650000000.0,
            'highFrequency': 3550000000.0
        }]
    }
    request = {'spectrumInquiryRequest': [
        spectrum_inquiry_0, spectrum_inquiry_1]}
    # Send spectrumInquiryRequest and get response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    self.assertEqual(len(response), 2)
    # Check Spectrum Inquiry Response
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertTrue('availableChannel' in response[0])
    for available_channel in response[0]['availableChannel']:
      self.assertEqual(available_channel['ruleApplied'], 'FCC_PART_96')
    self.assertEqual(response[0]['response']['responseCode'], 0)

    self.assertEqual(response[1]['cbsdId'], cbsd_ids[1])
    self.assertFalse('availableChannel' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_20(self):
    """Send Spectrum Inquiry requesting for spectrum out of range.

    The response should be UNSUPPORTED_SPECTRUM, code 300
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    request = {'registrationRequest': [device_a, device_b]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Create two Spectrum Inquiry requests, second one with frequency range
    # outside 3550 - 3700 MHz
    spectrum_inquiry_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_1['cbsdId'] = cbsd_ids[0]

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

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_21(self):
    """Send Spectrum Inquiry (two requests, both unsuccessful).

    The response should be INVALID_VALUE, code 103 for both requests.
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    request = {'registrationRequest': [device_a, device_b]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 0)
    cbsd_ids = (response[0]['cbsdId'], response[1]['cbsdId'])
    del request, response

    # Create Invalid Spectrum Inquiry requests
    spectrum_inquiry_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_1['cbsdId'] = cbsd_ids[0]
    spectrum_inquiry_1['inquiredSpectrum'] = [{
        'lowFrequency': 3650000000.0,
        'highFrequency': 3550000000.0,
    }]

    spectrum_inquiry_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_2['cbsdId'] = cbsd_ids[1]
    spectrum_inquiry_2['inquiredSpectrum'] = [{
        'lowFrequency': 3750000000.0,
        'highFrequency': 3650000000.0,
    }]
    request = {
        'spectrumInquiryRequest': [spectrum_inquiry_1, spectrum_inquiry_2]
    }
    # Send Spectrum Inquiry requests and Check Responses
    responses = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    for response_num, response in enumerate(responses):
      self.assertEqual(response['cbsdId'], cbsd_ids[response_num])
      self.assertFalse('availableChannel' in response)
      self.assertEqual(response['response']['responseCode'], 103)
