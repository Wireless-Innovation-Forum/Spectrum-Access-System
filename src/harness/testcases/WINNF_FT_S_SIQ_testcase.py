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
import logging
from util import winnforum_testcase, writeConfig,loadConfig, configurable_testcase ,getRandomLatLongInPolygon, \
  makePpaAndPalRecordsConsistent,filterChannelsByFrequencyRange, addCbsdIdsToRequests
import time

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
  def test_WINNF_FT_S_SIQ_3(self):
    """Multiple CBSDs inside and outside the Exclusion Zone.

    Response codes will vary depending on conditions.
    This test assumes some distance criteria between points and zones.
    If testdata records are changed, check again these criteria.
    """

    # Inject FSS station operating at range 3670 - 4200 MHz.
    fss_data = json.load(
        open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
    fss =  fss_data['record']
    fss['deploymentParam'][0]['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3670000000
    fss['deploymentParam'][0]['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 4200000000
    fss['deploymentParam'][0]['installationParam']['latitude'] = 38.4
    fss['deploymentParam'][0]['installationParam']['longitude'] = -98.9
    self._sas_admin.InjectFss(fss_data)

    # Inject GWBL station operating at range 3650 - 3700 MHz within 150 km of
    # FSS (approx. 100 km from FSS location set above).
    gwbl = json.load(
        open(os.path.join('testcases', 'testdata', 'gwbl_record_0.json')))
    self._sas_admin.InjectWisp(gwbl)

    # Load PAL/PPA data, operating channel 3620 - 3630 MHz.
    pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_low_frequency = 3620000000
    pal_high_frequency = 3630000000
    pal_user_id = 'pal_user'
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,
                                                            [pal_record],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            pal_user_id)

    # Load 5 CBSDs
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_4 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    device_5 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_g.json')))

    # Move device_1 inside PPA and outside 150kms range of FSS
    device_1['installationParam']['latitude'] = 38.854
    device_1['installationParam']['longitude'] = -97.195

    # Move device_2 outside PPA and outside 150kms range of FSS
    device_2['installationParam']['latitude'] = 40.0
    device_2['installationParam']['longitude'] = -97.87

    # Move device_3 inside PPA and inside 150kms range of FSS
    device_3['installationParam']['latitude'] = 38.775
    device_3['installationParam']['longitude'] = -97.291

    # Move device_4 outside PPA and inside 150kms range of FSS
    device_4['installationParam']['latitude'] = 39.0
    device_4['installationParam']['longitude'] = -98.6

    # Move device_5 outside PPA and inside 150kms range of FSS
    device_5['installationParam']['latitude'] = 38.2
    device_5['installationParam']['longitude'] = -99.5

    # Register devices - Use same userId as in PAL record for devices part of
    # the PPA cluster list.
    device_1['userId'] = pal_user_id
    device_3['userId'] = pal_user_id
    devices = [device_1, device_2, device_3, device_4, device_5]
    cbsd_ids = self.assertRegistered(devices)

    # Add devices 1 and 3 to the cluster list of the PPA
    ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[0], cbsd_ids[2]]

    # Inject PAL and PPA records
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record})
    self.assertTrue(zone_id)

    # Trigger daily activities and wait for it to be completed
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Spectrum Inquiries.
    spectrum_inquiries = []
    for i in xrange(4):
      spectrum_inquiries.append({
          'cbsdId': cbsd_ids[i],
          'inquiredSpectrum': [{
              'lowFrequency': 3550000000,
              'highFrequency': 3700000000
          }]
      })

    spectrum_inquiries.append({
        'cbsdId': cbsd_ids[4],
        'inquiredSpectrum': [{
            'lowFrequency': 3670000000,
            'highFrequency': 3700000000
        }]
    })

    request = {'spectrumInquiryRequest': spectrum_inquiries}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']

    # Check Spectrum Inquiry Response
    self.assertEqual(len(response), 5)

    # Checking response codes 0 for all inquiries. Checks for specific devices
    # will be treated in case by case sections below.
    for i in xrange(5):
      self.assertEqual(response[i]['response']['responseCode'], 0)

    # Filtering channels for devices 1 to 4 to simplify test checks.
    freq_range_pal = {
        'lowFrequency': pal_low_frequency,
        'highFrequency': pal_high_frequency,
    }
    freq_range_low = {
        'lowFrequency': 3550000000,
        'highFrequency': pal_low_frequency,
    }
    freq_range_high = {
        'lowFrequency': pal_high_frequency,
        'highFrequency': 3650000000,
    }
    freq_range_excluded = {
        'lowFrequency': 3650000000,
        'highFrequency': 3700000000,
    }
    all_channels = []
    channels_low = []
    channels_high = []
    channels_pal = []
    channels_excluded = []
    for i in xrange(4):
      channels = response[i]['availableChannel']
      all_channels.append(channels)
      channels_low.append(filterChannelsByFrequencyRange(channels,
                                                         freq_range_low))
      channels_high.append(filterChannelsByFrequencyRange(channels,
                                                          freq_range_high))
      channels_pal.append(filterChannelsByFrequencyRange(channels,
                                                         freq_range_pal))
      channels_excluded.append(filterChannelsByFrequencyRange(channels,
                                                              freq_range_excluded))

    # Checks for cbsd 1 (index 0)
    self.assertChannelsContainFrequencyRange(channels_low[0], freq_range_low)
    self.assertChannelsContainFrequencyRange(channels_high[0], freq_range_high)
    self.assertTrue(
        all(channel['channelType'] == 'GAA' and
            channel['ruleApplied'] == 'FCC_PART_96'
            for channel in channels_low[0] + channels_high[0]))
    self.assertChannelsContainFrequencyRange(channels_pal[0], freq_range_pal)
    self.assertTrue(
        all(channel['channelType'] == 'PAL' and
            channel['ruleApplied'] == 'FCC_PART_96'
            for channel in channels_pal[0]))

    # Checks for cbsd 2 (index 1)
    self.assertChannelsContainFrequencyRange(channels_low[1], freq_range_low)
    self.assertChannelsContainFrequencyRange(channels_high[1], freq_range_high)
    self.assertTrue(
        all(channel['channelType'] == 'GAA' and
            channel['ruleApplied'] == 'FCC_PART_96'
            for channel in channels_low[1] + channels_high[1]))
    self.assertFalse(
        any(channel['channelType'] == 'PAL' for channel in all_channels[1]))

    # Checks for cbsd 3 (index 2)
    self.assertChannelsContainFrequencyRange(channels_low[2], freq_range_low)
    self.assertChannelsContainFrequencyRange(channels_high[2], freq_range_high)
    self.assertTrue(
        all(channel['channelType'] == 'GAA' and
            channel['ruleApplied'] == 'FCC_PART_96'
            for channel in channels_low[2] + channels_high[2]))
    self.assertChannelsContainFrequencyRange(channels_pal[2], freq_range_pal)
    self.assertTrue(
        all(channel['channelType'] == 'PAL' and
            channel['ruleApplied'] == 'FCC_PART_96'
            for channel in channels_pal[2]))
    self.assertEqual(len(channels_excluded[2]), 0)

    # Checks for cbsd 4 (index 3)
    self.assertChannelsContainFrequencyRange(channels_low[3], freq_range_low)
    self.assertChannelsContainFrequencyRange(channels_high[3], freq_range_high)
    self.assertTrue(
        all(channel['channelType'] == 'GAA' and
            channel['ruleApplied'] == 'FCC_PART_96'
            for channel in channels_low[3] + channels_high[3]))
    self.assertFalse(
        any(channel['channelType'] == 'PAL' for channel in all_channels[3]))
    self.assertEqual(len(channels_excluded[3]), 0)

    # Check for cbsd 5 (index 4)
    self.assertEqual(len(response[4]['availableChannel']), 0)

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_4(self):
    """Tests related to DPA activated for some channels
    
    SAS sending responseCode = 0 successful response
    and including all channels within frequency range FR.
    """
    # Trigger SAS to load DPAs
    self._sas_admin.TriggerLoadDpas()
    # Trigger SAS to de-active all the DPAs
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})
    # Trigger SAS to active one DPA on channel c
    frequency_range = {
      'lowFrequency': 3620000000,
      'highFrequency': 3630000000
    }
    self._sas_admin.TriggerDpaActivation({'frequencyRange': frequency_range,
                                          'dpaId': 'east_dpa_4'})
    time.sleep(300)
    # Load and register CBSD
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Change device location to be inside DPA neighborhood
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350
    cbsd_ids = self.assertRegistered([device_a])
    # Create and send spectrumInquiry with the same frequency range as DPA Channel
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_ids[0]
    spectrum_inquiry_0['inquiredSpectrum'][0]['lowFrequency'] = \
                frequency_range['lowFrequency']
    spectrum_inquiry_0['inquiredSpectrum'][0]['highFrequency'] = \
                frequency_range['highFrequency']
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    # Check spectrum inquiry response
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertTrue('availableChannel' in response)
    self.assertEqual(response['response']['responseCode'], 0)
    # Verify available channels contains the requested range and don't have any missing or repeated channels
    self.assertChannelsContainFrequencyRange(response['availableChannel'], frequency_range)

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

    pal_low_frequency = 3620000000
    pal_high_frequency = 3630000000
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

  def generate_SIQ_12_default_config(self, filename):
    """Generates the WinnForum configuration for SIQ.12."""
    # Load GWBL information
    gwpz_e = json.load(
        open(os.path.join('testcases', 'testdata', 'gwpz_record_0.json')))
    # Load device info
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))

    # Load PAL records
    pal_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))

    # Load PPA records
    ppa_record1 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record2 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_1.json')))

    pal_low_frequency1 = 3570000000
    pal_high_frequency1 = 3580000000
    pal_user_id1 = "pal_user_1"
    pal_low_frequency2 = 3600000000
    pal_high_frequency2 = 3610000000
    pal_user_id2 = "pal_user_2"

    # Make PAL and PPA record consistent
    ppa_record1, pal_records1 = makePpaAndPalRecordsConsistent(
        ppa_record1, [pal_record_0], pal_low_frequency1, pal_high_frequency1,
        pal_user_id1)
    ppa_record2, pal_records2 = makePpaAndPalRecordsConsistent(
        ppa_record2, [pal_record_1], pal_low_frequency2, pal_high_frequency2,
        pal_user_id2)
    # Merge PAL records lists into one list (may contain duplicates)
    pal_records = pal_records1 + pal_records2

    ppa_cluster_list_1 = [0]
    ppa_cluster_list_2 = []
    # Move device_b inside the PPA1 zone
    device_b['installationParam']['latitude'] = 38.82767
    device_b['installationParam']['longitude'] = -97.20497

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionalParameters = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']

    # N2 spectrum inquiry requests
    # 1. Spectrum Inquiry: 3550-3580 .
    spectrum_inquiry_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_1['inquiredSpectrum'] = [{
        'lowFrequency': 3550000000,
        'highFrequency': 3580000000
    }]

    # 2. Spectrum Inquiry: Invalid Value of low and high frequency and invalid id for cbsdId.
    spectrum_inquiry_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_2['inquiredSpectrum'] = [{
        'lowFrequency': 3610000000,
        'highFrequency': 3590000000
    }]
    spectrum_inquiry_2['cbsdId'] = "INVALID_CBSD_ID_12345"

    # 3. Spectrum Inquiry: Missing parameter low frequency and missing cbsdId
    spectrum_inquiry_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_3['inquiredSpectrum'] = [{
        'highFrequency': 3700000000
    }]
    spectrum_inquiry_3['cbsdId'] = "REMOVE"

    # Create the actual config.
    devices = [device_b, device_c, device_e]
    conditionals = [conditionalParameters]

    config = {
      'registrationRequests': devices,
      'conditionalRegistrationData': conditionals,
      'expectedResponseCodes': [(0,), (103,), (102,)],
      'palRecords': pal_records,
      'ppaRecords': [
        {'ppaRecord': ppa_record1, 'ppaClusterList': ppa_cluster_list_1},
        {'ppaRecord': ppa_record2, 'ppaClusterList': ppa_cluster_list_2}
      ],
      'spectrumInquiryRequests': [
        spectrum_inquiry_1,
        spectrum_inquiry_2,
        spectrum_inquiry_3
      ],
      'gwpzRecords': [gwpz_e],
      'fr1Cbsd': [
        [{'lowFrequency': 3570000000, 'highFrequency': 3580000000}],
        [],
        []
      ],
      'fr2Cbsd': [
        [{'lowFrequency': 3570000000, 'highFrequency': 3580000000}],
        [],
        []
      ]

    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SIQ_12_default_config)
  def test_WINNF_FT_S_SIQ_12(self, config_filename):
    """[Configurable] Spectrum inquiry in the presence of protected entities."""

    config = loadConfig(config_filename)

    # Light checking of the config file
    self.assertEqual(len(config['spectrumInquiryRequests']),len(config['registrationRequests']))
    self.assertEqual(len(config['expectedResponseCodes']),len(config['spectrumInquiryRequests']))
    self.assertEqual(len(config['spectrumInquiryRequests']),len(config['fr1Cbsd']))
    self.assertEqual(len(config['spectrumInquiryRequests']),len(config['fr2Cbsd']))
    self.assertGreater(len(config['registrationRequests']),0)

    # 1. Load information about N1 GWBZs
    for gwpz_record in config['gwpzRecords']:
      self._sas_admin.InjectWisp(gwpz_record)

    # 2 & 3. Register N2 CBSDs
    # Check registration response
    # The assertRegistered function does the Inject FCC ID and user ID for the registration requests
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # 4. Load N3 PPAs
    # Inject PAL Records for all PPAs
    for pal_record in config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Update PPA records with devices' CBSD IDs and Inject zone data
    for ppa in config['ppaRecords']:
      ppa['ppaRecord']['ppaInfo']['cbsdReferenceId'] = []
      for device_index in ppa['ppaClusterList']:
        ppa['ppaRecord']['ppaInfo']['cbsdReferenceId'].append(cbsd_ids[device_index])
      # Inject PPA into SAS UUT
      zone_id = self._sas_admin.InjectZoneData({"record": ppa['ppaRecord']})

    # 5. Trigger CPAS activity if GWPZ > 0 or PPA > 0
    if (len(config['gwpzRecords']) > 0 or len(config['ppaRecords']) > 0):
      self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # 6. Send N2 spectrum inquiry requests (one per registered CBSD)
    spectrum_inquiry_list = config['spectrumInquiryRequests']
    addCbsdIdsToRequests(cbsd_ids, spectrum_inquiry_list)

    spectrum_inquiry_request = {'spectrumInquiryRequest': spectrum_inquiry_list}
    spectrum_inquiry_response = self._sas.SpectrumInquiry(spectrum_inquiry_request)['spectrumInquiryResponse']

    # Check the response contains N2 SpectrumInquiryResponse objects
    self.assertEqual(len(spectrum_inquiry_response),len(config['spectrumInquiryRequests']))

    for index,response in enumerate(spectrum_inquiry_response):
      # If the corresponding request contained a valid cbsdId, the
      # response shall contain the same cbsdId.
      if 'cbsdId' in spectrum_inquiry_list[index]:
        if spectrum_inquiry_list[index]['cbsdId'] in cbsd_ids:
          self.assertEqual(response['cbsdId'], spectrum_inquiry_list[index]['cbsdId'])
        else:
          self.assertFalse('cbsdId' in response)

      # Check response code matches the expected response code
      self.assertIn(response['response']['responseCode'],config['expectedResponseCodes'][index])

      if (response['response']['responseCode'] == 0) :
        # Check if the 'availableChannel' parameter is present
        self.assertTrue('availableChannel' in response)

        # Check if the ruleApplied field is set to FCC_PART_96
        for channel in response['availableChannel']:
          self.assertEqual(channel['ruleApplied'], 'FCC_PART_96')

        # Check that the GAA channel frequency ranges do not overlap with FR1cbsd ranges
        for channel in response['availableChannel']:
          if channel['channelType'] == 'GAA':
            for fr1_range in config['fr1Cbsd'][index]:
              # Check if the channel range is lower than the low freq of FR1cbsd range or if it is higher
              # than the high freq. If not then it is considered to be overlapping
              self.assertTrue(((channel['frequencyRange']['highFrequency'] <= fr1_range['lowFrequency']) or
                               (channel['frequencyRange']['lowFrequency'] >= fr1_range['highFrequency'])),
                                "GAA channel overlaps with FR1cbsd")

        # Check the PAL channels frequency ranges overlap with FR2cbsd
        for channel in response['availableChannel']:
          if channel['channelType'] == 'PAL':
            self.assertChannelIncludedInFrequencyRanges(channel, config['fr2Cbsd'][index])

            # Check the PAL channels frequency ranges does not include any frequency range from 3650-3700MHz.
            self.assertLess(channel['frequencyRange']['lowFrequency'], 3650000000)
            self.assertLessEqual(channel['frequencyRange']['highFrequency'], 3650000000)

        # Check the available channels are within the range requested by that CBSD
        for channel in response['availableChannel']:
          isFrequencyIncludedInRange = False
          for inquired_spectrum in spectrum_inquiry_request['spectrumInquiryRequest'][index]['inquiredSpectrum']:
            if ((channel['frequencyRange']['lowFrequency'] >= inquired_spectrum['lowFrequency']) and
                (channel['frequencyRange']['lowFrequency'] < inquired_spectrum['highFrequency']) and
                (channel['frequencyRange']['highFrequency'] > inquired_spectrum['lowFrequency']) and
                (channel['frequencyRange']['highFrequency'] <= inquired_spectrum['highFrequency'])):
              isFrequencyIncludedInRange = True
          self.assertTrue(isFrequencyIncludedInRange, "Available channel is not in requested frequency range")

      else:
        # Check 'availableChannel' is not present if the response code is not SUCCESS
        self.assertFalse('availableChannel' in response)

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
