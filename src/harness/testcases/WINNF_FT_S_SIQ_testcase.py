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
  def test_WINNF_FT_S_SIQ_5(self):
    """
    Purpose : Tests related to PAL Protection Area (PPA)

    Result:SAS approves the request by sending a Spectrum Inquiry Response as follows:
    - SAS response includes cbsdId = C.
    - availableChannel parameter does not include the frequency range FR1.
    - responseCode = 0, indicating a successful inquiry of the spectrum.

    TS verrsion : BASED_ON_V0.0.0-r5.0 (15 September 2017)

    Test version : 0.1
    """
    # STEP 1
    # Load the device : equivalent to cbsdId=C from the TS
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    # Load PAL Database Record
    pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    # Load PPA record
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))

    # Change device location to be inside PPA
    device_a['installationParam']['latitude'], \
    device_a['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record)

    pal_low_frequency = 3620000000.0
    pal_high_frequency = 3630000000.0

    # Make PPA and PAL records consitent
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,[pal_record],\
        pal_low_frequency,pal_high_frequency,device_a['userId'])

    # Register the devices and assert the Response
    cbsd_ids = self.assertRegistered([device_a])
    # Inject PAL record record
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    # Inject PPA record
    self._sas_admin.InjectZoneData({"record": ppa_record})

    # Trigger daily activities and wait for it to be completed
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Send spectrumInquiry in which the frequency range(3550-3650)overlaps with PPA frequency
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_ids[0]

    # Check : Check spectrum inquiry response
    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    for available_channel in response['availableChannel']:
        self.assertNotEqual(available_channel['frequencyRange'], pal_record[0]['channelAssignment']['primaryAssignment'])

  @winnforum_testcase
  def test_WINNF_FT_S_SIQ_7(self):
    """Send Spectrum Inquiry from cbsdId different from its assigned cbsdId,
        SAS should reject Spectrum inquiry.
    The responseCode should be (103, 105), with NO channels in result.

    TS verrsion : BASED_ON_V0.0.0-r5.0 (15 September 2017)
    Test version : 0.1
    """
    # STEP 1
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

    # STEP 2
    # Create Spectrum Inquiry and Send request for device_a using device_c_cert and device_c_key
    spectrum_inquiry_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'spectrum_inquiry_0.json')))
    spectrum_inquiry_0['cbsdId'] = cbsd_id_a

    request = {'spectrumInquiryRequest': [spectrum_inquiry_0]}
    response = self._sas.SpectrumInquiry(request, device_c_cert, device_c_key)['spectrumInquiryResponse'][0]
    # CHECK : Check Spectrum Inquiry Response
    self.assertFalse('cbsdId' in response)
    self.assertTrue(response['response']['responseCode'] == 103 or
                    response['response']['responseCode'] == 105)