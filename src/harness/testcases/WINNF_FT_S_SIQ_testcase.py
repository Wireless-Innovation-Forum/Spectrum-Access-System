#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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
  def test_WINNF_FT_S_SIQ_2(self):
    """Response has no available channel
    with responseCode = 0 successful 
    """
    # Load GWPZ Record
    gwpz = json.load(
        open(os.path.join('testcases', 'testdata', 'gwpz_record_0.json')))      
    # Load CBSD info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Change device location to be inside GWPZ
    device_a['installationParam']['latitude'], \
    device_a['installationParam']['longitude'] = getRandomLatLongInPolygon(gwpz)
    # Register device
    cbsd_ids = self.assertRegistered([device_a])  
    
    # Inject GWPZ in SAS 
    self._sas_admin.InjectWisp(gwpz)   
    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()  
     
    # Create spectrumInquiry with the frequency range full overlaps with GWPZ frequency
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_ids[0]
    spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency'] = gwpz['record']\
        ['deploymentParam'][0]['operationParam']['operationFrequencyRange']['lowFrequency']
    spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'] = gwpz['record']\
        ['deploymentParam'][0]['operationParam']['operationFrequencyRange']['highFrequency']

    # Check : Check spectrum inquiry response
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertFalse(response['availableChannel'])
    self.assertEqual(response['response']['responseCode'], 0)
    
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
    self.assertEqual(len(response['availableChannel']), 0)
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
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
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
    self._sas_admin.InjectUserId({'userId': device_c['userId']})
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
  def test_WINNF_FT_S_SIQ_9(self):
    """Multiple SIQ requests as claimed PPAs or as GAAs.

    Response Code must be 0 for all CBSDs.
    """

    # Load 4 devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))

    # First PPA with device_a and FR1 = 3550 - 3560
    pal_low_frequency1 = 3550000000
    pal_high_frequency1 = 3560000000
    pal_record1 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    ppa_record1 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record1, pal_record1 = makePpaAndPalRecordsConsistent(
        ppa_record1, [pal_record1], pal_low_frequency1, pal_high_frequency1,
        device_a['userId'])

    # Move device_a into the first PPA zone
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = getRandomLatLongInPolygon(ppa_record1)

    # Second PPA with device_c and FR2 = 3600 - 3610
    pal_low_frequency2 = 3600000000
    pal_high_frequency2 = 3610000000
    pal_record2 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    ppa_record2 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_1.json')))
    ppa_record2, pal_record2 = makePpaAndPalRecordsConsistent(
        ppa_record2, [pal_record2], pal_low_frequency2, pal_high_frequency2,
        device_c['userId'])

    # Move device_c into the second PPA zone
    device_c['installationParam']['latitude'], device_c['installationParam'][
        'longitude'] = getRandomLatLongInPolygon(ppa_record2)

    # Register 4 devices.
    cbsd_ids = self.assertRegistered([device_a, device_c, device_e, device_f])

    # Update PPA record with device_a's CBSD ID and Inject data
    ppa_record1['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[0]]
    self._sas_admin.InjectPalDatabaseRecord(pal_record1[0])
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record1})
    self.assertTrue(zone_id)

    # Update PPA record with device_c's CBSD ID and Inject data
    ppa_record2['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[1]]
    self._sas_admin.InjectPalDatabaseRecord(pal_record2[0])
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record2})
    self.assertTrue(zone_id)

    # Create Spectrum Inquiry requests
    spectrum_inquiry_0 = {
        'cbsdId': cbsd_ids[0],
        'inquiredSpectrum': [{
            'lowFrequency': 3550000000,
            'highFrequency': 3700000000
        }]
    }
    spectrum_inquiry_1 = {
        'cbsdId': cbsd_ids[1],
        'inquiredSpectrum': [{
            'lowFrequency': 3600000000,
            'highFrequency': 3700000000
        }]
    }
    spectrum_inquiry_2 = {
        'cbsdId': cbsd_ids[2],
        'inquiredSpectrum': [{
            'lowFrequency': 3550000000,
            'highFrequency': 3700000000
        }]
    }
    spectrum_inquiry_3 = {
        'cbsdId': cbsd_ids[3],
        'inquiredSpectrum': [{
            'lowFrequency': 3550000000,
            'highFrequency': 3700000000
        }]
    }
    request = {
        'spectrumInquiryRequest': [
            spectrum_inquiry_0, spectrum_inquiry_1, spectrum_inquiry_2,
            spectrum_inquiry_3
        ]
    }

    # Check Spectrum Inquiry response
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    # Response 0 and 1 contain at least 1 PAL channelType in availableChannel.
    for resp_num in [0, 1]:
      self.assertEqual(response[resp_num]['cbsdId'], cbsd_ids[resp_num])
      self.assertEqual(response[resp_num]['response']['responseCode'], 0)
      self.assertTrue(
          any(channel['channelType'] == 'PAL'
              for channel in response[resp_num]['availableChannel']))
      self.assertTrue(
          all(channel['ruleApplied'] == 'FCC_PART_96'
              for channel in response[resp_num]['availableChannel']))
    # Check response 0.
    for channel in response[0]['availableChannel']:
      if channel['channelType'] == 'PAL':
        self.assertTrue(
            channel['frequencyRange']['lowFrequency'] == pal_low_frequency1)
        self.assertTrue(
            channel['frequencyRange']['highFrequency'] == pal_high_frequency1)
      else:
        self.assertTrue(channel['channelType'] == 'GAA')
        # Verify the low & high frequency in GAA.
        self.assertTrue(
            channel['frequencyRange']['lowFrequency'] >= pal_high_frequency1)
        self.assertTrue(
            (channel['frequencyRange']['highFrequency'] <= 3700000000))

    # Check response 1.
    for channel in response[1]['availableChannel']:
      if channel['channelType'] == 'PAL':
        self.assertTrue(
            channel['frequencyRange']['lowFrequency'] == pal_low_frequency2)
        self.assertTrue(
            channel['frequencyRange']['highFrequency'] == pal_high_frequency2)
      else:
        self.assertTrue(channel['channelType'] == 'GAA')
        # Verify the low & high frequency in GAA.
        self.assertTrue(
            channel['frequencyRange']['lowFrequency'] >= pal_high_frequency2)
        self.assertTrue(
            (channel['frequencyRange']['highFrequency'] <= 3700000000))

    # Response 2 and 3
    # If availableChannel is not null then all availableChannels should be GAA
    for resp_num in [2, 3]:
      self.assertEqual(response[resp_num]['cbsdId'], cbsd_ids[resp_num])
      self.assertEqual(response[resp_num]['response']['responseCode'], 0)
      if response[resp_num]['availableChannel']:
        self.assertTrue(
            all(channel['channelType'] == 'GAA'
                for channel in response[resp_num]['availableChannel']))
        self.assertTrue(
            all(channel['ruleApplied'] == 'FCC_PART_96'
                for channel in response[resp_num]['availableChannel']))

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_10(self):
    """Send Spectrum Inquiry with Array request with successful and unsuccessful responses.
     The response codes will vary
    """

    # Register six devices
    device_1 = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_4 = json.load(open(os.path.join('testcases', 'testdata', 'device_f.json')))
    device_5 = json.load(open(os.path.join('testcases', 'testdata', 'device_g.json')))
    device_6 = json.load(open(os.path.join('testcases', 'testdata', 'device_i.json')))

    self._sas_admin.InjectFccId({'fccId': device_1['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_3['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_4['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_5['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_6['fccId']})

    self._sas_admin.InjectUserId({'userId': device_1['userId']})
    self._sas_admin.InjectUserId({'userId': device_2['userId']})
    self._sas_admin.InjectUserId({'userId': device_3['userId']})
    self._sas_admin.InjectUserId({'userId': device_4['userId']})
    self._sas_admin.InjectUserId({'userId': device_5['userId']})
    self._sas_admin.InjectUserId({'userId': device_6['userId']})

    # send registration requests
    devices = [device_1, device_2, device_3, device_4, device_5, device_6]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)

    # Check registration response
    cbsd_ids = []
    for resp in response['registrationResponse']:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Send Spectrum Inquiry request for six cbsds
    # create inquiry with 6 requests
    #
    # the 1st inquiry is valid
    spectrum_inquiry_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_1['cbsdId'] = cbsd_ids[0]

    # the 2nd inquiry has one one parameter invalid
    spectrum_inquiry_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    # cause invalid parameters by changing frequencies
    spectrum_inquiry_2['inquiredSpectrum'][0]['lowFrequency'] = 3650000000
    spectrum_inquiry_2['inquiredSpectrum'][0]['highFrequency'] = 3560000000
    spectrum_inquiry_2['cbsdId'] = cbsd_ids[1]

    # the 3rd inquiry has highFrequency parameter in inquiredSpectrum object is missing
    spectrum_inquiry_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    del spectrum_inquiry_3['inquiredSpectrum'][0]['highFrequency']
    spectrum_inquiry_3['cbsdId'] = cbsd_ids[2]

    # the 4th inquiry has lowFrequency parameter in inquiredSpectrum object is missing
    spectrum_inquiry_4 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    del spectrum_inquiry_4['inquiredSpectrum'][0]['lowFrequency']
    spectrum_inquiry_4['cbsdId'] = cbsd_ids[3]

    # the 5th inquiry has inquiredSpectrum object completely missing
    spectrum_inquiry_5 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    del spectrum_inquiry_5['inquiredSpectrum']
    spectrum_inquiry_5['cbsdId'] = cbsd_ids[4]

    # the 6th inquiry has the cbsdId missing
    spectrum_inquiry_6 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))

    request = {'spectrumInquiryRequest': [spectrum_inquiry_1, spectrum_inquiry_2,
        spectrum_inquiry_3, spectrum_inquiry_4, spectrum_inquiry_5, spectrum_inquiry_6]}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']

    # Check Spectrum Inquiry Response
    # response length check for 6 responses
    self.assertEqual(len(response), 6)

    # the 1st object will be response code 0
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertTrue('availableChannel' in response[0])
    for available_channel in response[0]['availableChannel']:
      self.assertEqual(available_channel['ruleApplied'], 'FCC_PART_96')
    self.assertEqual(response[0]['response']['responseCode'], 0)

    # the 2nd object will be response code 103
    self.assertEqual(response[1]['cbsdId'], cbsd_ids[1])
    self.assertFalse('availableChannel' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 103)

    # the 3rd object will be response code 102
    self.assertEqual(response[2]['cbsdId'], cbsd_ids[2])
    self.assertFalse('availableChannel' in response[2])
    self.assertEqual(response[2]['response']['responseCode'], 102)

    # the 4th object will be response code 102
    self.assertEqual(response[3]['cbsdId'], cbsd_ids[3])
    self.assertFalse('availableChannel' in response[3])
    self.assertEqual(response[3]['response']['responseCode'], 102)

    # the 5th object will be response code 102
    self.assertEqual(response[4]['cbsdId'], cbsd_ids[4])
    self.assertFalse('availableChannel' in response[4])
    self.assertEqual(response[4]['response']['responseCode'], 102)

    # the 6th object will have no cbsdId
    self.assertFalse('cbsdId' in response[5])
    self.assertFalse('availableChannel' in response[5])
    self.assertEqual(response[5]['response']['responseCode'], 102)

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

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_13(self):
    """Blacklisted CBSD in Array request.

    The response for Inquiry #3 (blacklisted) should be code 101.
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))

    devices = [device_a, device_c, device_e]
    cbsd_ids = self.assertRegistered(devices)

    # Blacklist third cbsd
    request = {'fccId': device_e['fccId']}
    self._sas_admin.BlacklistByFccId(request)
    del request

    # Spectrum Inquiries: All parameters valid.
    spectrum_inquiries = []
    for i in range(len(devices)):
      spectrum_inquiry = json.load(
          open(
              os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
      spectrum_inquiry['cbsdId'] = cbsd_ids[i]
      spectrum_inquiries.append(spectrum_inquiry)

    request = {'spectrumInquiryRequest': spectrum_inquiries}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']

    # Check Spectrum Inquiry Response
    self.assertEqual(len(response), 3)
    # First and second cbsd
    for resp_num in range(2):
      self.assertEqual(response[resp_num]['cbsdId'], cbsd_ids[resp_num])
      self.assertEqual(response[resp_num]['response']['responseCode'], 0)
    # Third cbsd (blacklisted)
    self.assertEqual(response[2]['response']['responseCode'], 101)
