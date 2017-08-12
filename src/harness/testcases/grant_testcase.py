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

# Some parts of this software was developed by employees of 
# the National Institute of Standards and Technology (NIST), 
# an agency of the Federal Government. 
# Pursuant to title 17 United States Code Section 105, works of NIST employees 
# are not subject to copyright protection in the United States and are 
# considered to be in the public domain. Permission to freely use, copy, 
# modify, and distribute this software and its documentation without fee 
# is hereby granted, provided that this notice and disclaimer of warranty 
# appears in all copies.

# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER 
# EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY
# THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM 
# INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE 
# SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT
# SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, 
# INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, 
# OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON 
# WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED
# BY PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED
# FROM, OR AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES 
# PROVIDED HEREUNDER.

# Distributions of NIST software should also include copyright and licensing 
# statements of any third-party software that are legally bundled with the 
# code in compliance with the conditions of those licenses.

import json
import os
import sas_testcase
import sas
from util import winnforum_testcase, getRandomLatLongInPolygon, \
  makePpaAndPalRecordsConsistent


class GrantTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_1(self):
    """Successful CBSD grant request.
    CBSD sends a single grant request when no incumbent is present in the GAA
    frequency range requested by the CBSD. Response should be SUCCESS.
    """

    # Category A and Category B Device
    for device_filename in ('device_a.json', 'device_b.json'):
      # Register the device
      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      request = {'registrationRequest': [device]}
      response = self._sas.Registration(request)['registrationResponse'][0]
      # Check registration response
      self.assertEqual(response['response']['responseCode'], 0)
      cbsd_id = response['cbsdId']
      del request, response

      # Request grant
      grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
      grant_0['cbsdId'] = cbsd_id
      request = {'grantRequest': [grant_0]}
      response = self._sas.Grant(request)['grantResponse'][0]
      # Check grant response
      self.assertEqual(response['cbsdId'], cbsd_id)
      self.assertTrue(response['grantId'])
      self.assertEqual(response['channelType'], 'GAA')
      self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_7(self):
    """CBSD sends grant with missing cbsdId. The response should be
      responseCode = 102 or 105.
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

    # Request grant
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertFalse('cbsdId' in response)
    self.assertFalse('grantId' in response)
    self.assertTrue((response['response']['responseCode'] == 102) or \
                    (response['response']['responseCode'] == 105))

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_8(self):
    """CBSD grant request with missing operationParams.

    The operationParams object is missing in the grant request. The response
    should be FAIL.
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

    # operationParams object is NOT present in the grant request.
    grant_0 = {'cbsdId': cbsd_id}
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_9(self):
    """Missing maxEirp in operationParam object.
    The maxEirp parameter is missing in the grant request. The response
    should be FAIL.
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

    # Request grant
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    del grant_0['operationParam']['maxEirp']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_10(self):
    """Missing lowFrequency in operationParam object.
    The lowFrequency parameter is missing in the grant request. The response
    should be FAIL.
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

    # Request grant
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    del grant_0['operationParam']['operationFrequencyRange']['lowFrequency']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_11(self):
    """Missing highFrequency in operationParam object.
    The highFrequency parameter is missing in the grant request. The response
    should be FAIL.
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

    # Request grant
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    del grant_0['operationParam']['operationFrequencyRange']['highFrequency']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_12(self):
    """CBSD grant request when CBSD ID does not exist in SAS.
    CBSD sends grant request when its CBSD Id is not in SAS. The response
    should be FAIL.
    """

    # Request grant before registration, thus the CBSD ID does not exist in SAS
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = 'A non-exist cbsd id'
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertFalse('cbsdId' in response)
    self.assertFalse('grantId' in response)
    self.assertTrue(response['response']['responseCode'] in (103, 105))

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_14(self):
    """lowFrequency and highFrequency value in operationParam mutually invalid.
    The response should be 103 (INVALID_PARAM)
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

    # Create Grant Request with mutually invalid frequency range
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'][
      'lowFrequency'] = 3630000000.0
    grant_0['operationParam']['operationFrequencyRange'][
      'highFrequency'] = 3620000000.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_15(self):
    """CBSD requests a frequency range which is a mix of PAL and GAA channel.
    
    The Response Code should be 103(INVALID_PARAM)
    """

    # Load the Data
    pal_low_frequency = 3550000000.0
    pal_high_frequency = 3560000000.0
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    ppa_record = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,
                                                            [pal_record],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            device_a['userId'])

    # Move the Device to a random location in PPA
    device_a['installationParam']['latitude'], \
    device_a['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record)

    # Register the device
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Inject PAL and PPA Database Record
    ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_id]
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    self._sas_admin.InjectZoneData({'record': ppa_record})

    # Trigger daily activities and wait for it to get it complete
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Create Grant Request containing PAL and GAA frequency
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'][
      'lowFrequency'] = pal_low_frequency
    grant_0['operationParam']['operationFrequencyRange'][
      'highFrequency'] = pal_high_frequency + 10000000.0
    request = {'grantRequest': [grant_0]}
    # Send grant request
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_16(self):
    """Frequency range is completely outside 3550-3700 MHz.
    The response should be 103 (INVALID_PARAM) or 300 (UNSUPPORTED_SPECTRUM)
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

    # Create Grant Request with frequency range outside 3550-3700 MHz
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'][
      'lowFrequency'] = 3350000000.0
    grant_0['operationParam']['operationFrequencyRange'][
      'highFrequency'] = 3450000000.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertTrue(response['response']['responseCode'] in (103, 300))

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_17(self):
    """Frequency range value in operationParam partially outside 3550-3700 MHz.
    The response should be 103 (INVALID_PARAM) or 300 (UNSUPPORTED_SPECTRUM)
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

    # Create Grant Request with frequency range partially outside 3550-3700 Mhz
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'][
      'lowFrequency'] = 3450000000.0
    grant_0['operationParam']['operationFrequencyRange'][
      'highFrequency'] = 3650000000.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertTrue(response['response']['responseCode'] in (103, 300))

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_20(self):
    """First request granted as PAL or GAA channel, send next request 
    for PAL or GAA channel for the same frequency range

    Response Code should be 401
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

    # Send grant request
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]

    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue('grantId' in response)
    self.assertValidResponseFormatForApprovedGrant(response)
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    request = {'grantRequest': [grant_0]}
    # Send grant request with the same frequency
    response = self._sas.Grant(request)['grantResponse'][0]

    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 401)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_21(self):
    """maxEirp in Grant Request for Category A is unsupported.

    The response should be 103 (INVALID_VALUE)
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

    # Create Grant Request with maxEirp exceeding maximum allowable (which is
    # 30 dBm/10 MHz)
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['maxEirp'] = 31.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_22(self):
    """maxEirp in Grant Request for Category B is unsupported.

    The response should be 103 (INVALID_VALUE)
    """
    # Register the device
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Create Grant Request with maxEirp exceeding maximum allowable EIRP (which
    # is 47 dBm/10 MHz)
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['maxEirp'] = 48.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_23(self):
    """Dual grant requests for two devices. Successful case.

    The response should be 0 (NO_ERROR)
    """
    # Register the devices
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_c = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    request = {'registrationRequest': [device_a, device_c]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Create grant requests
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_1['cbsdId'] = cbsd_ids[1]
    # Request for non-overlapping frequency spectrum
    grant_0['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': 3620000000.0,
      'highFrequency': 3630000000.0
    }
    grant_1['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': 3640000000.0,
      'highFrequency': 3650000000.0
    }
    request = {'grantRequest': [grant_0, grant_1]}
    # Send grant requests
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(response), 2)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertTrue('grantId' in resp)
      self.assertValidResponseFormatForApprovedGrant(resp)
      self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_25(self):
    """One request is for a PAL channel and the other for a GAA channel, 
    no incumbent present in the PAL and GAA frequency ranges used in the two requests.

    The response should be 0 (NO_ERROR)"""

    # Load the Data
    pal_low_frequency = 3550000000.0
    pal_high_frequency = 3560000000.0
    user_id = 'pal_device'
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))

    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    ppa_record = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,
                                                            [pal_record],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            user_id)

    # Move the Device to a random location in PPA
    device_a['installationParam']['latitude'], \
    device_a['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record)
    device_a['userId'] = user_id

    # Register the devices and assert the Response
    cbsd_ids = self.assertRegistered([device_a, device_c])

    # Update PPA Record with CBSD ID and Inject Data
    ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[0]]
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    self._sas_admin.InjectZoneData({"record": ppa_record})

    # Trigger daily activities and wait for it to get it complete
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    
    # Create grant requests
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_1['cbsdId'] = cbsd_ids[1]
    # Request for non-overlapping frequency spectrum
    grant_0['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': pal_low_frequency,
      'highFrequency': pal_high_frequency
    }
    grant_1['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': 3570000000.0,
      'highFrequency': 3580000000.0
    }
    request = {'grantRequest': [grant_0, grant_1]}
    # Send grant requests
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(response), 2)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertTrue('grantId' in resp)
      self.assertValidResponseFormatForApprovedGrant(resp)
      self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_26(self):
    """Two grant requests. #1 Successful, #2 Unsuccessful.

    Returns 0 (NO_ERROR) for successful and 103 (INVALID_VALUE) for unsuccessful
    """
    # Register two devices
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_c = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    request = {'registrationRequest': [device_a, device_c]}
    response = self._sas.Registration(request)['registrationResponse']
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Prepare grant requests.
    # 1. valid
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    # 2. with lowFrequency > highFrequency
    grant_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_1['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': 3650000000.0,
      'highFrequency': 3550000000.0
    }
    request = {'grantRequest': [grant_0, grant_1]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertGreater(len(response[0]['grantId']), 0)
    self.assertValidResponseFormatForApprovedGrant(response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)

    self.assertEqual(response[1]['cbsdId'], cbsd_ids[1])
    self.assertFalse('grantId' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_27(self):
    """Two grant requests. Both Unsuccessful.

    Returns 102 (MISSING_PARAM) for unsuccessful for first request
            103 (INVALID_VALUE) for second request
    """
    # Register two devices
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_c = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    request = {'registrationRequest': [device_a, device_c]}
    response = self._sas.Registration(request)['registrationResponse']
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Prepare grant requests.
    # 1. maxEirp is missing
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    del grant_0['operationParam']['maxEirp']
    # 2 lowFrequency is greater than the highFrequency
    grant_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_1['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': 3650000000.0,
      'highFrequency': 3550000000.0
    }
    request = {'grantRequest': [grant_0, grant_1]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertFalse('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 102)

    self.assertEqual(response[1]['cbsdId'], cbsd_ids[1])
    self.assertFalse('grantId' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_28(self):
    """Two grant requests for overlapping frequency range.

    Returns 401 (GRANT_CONFLICT) for at least one request
    """
    # Register a device
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id = response['cbsdId']
    del request, response

    # Prepare grant requests with overlapping frequency range
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': 3565000000.0,
      'highFrequency': 3567000000.0
    }
    grant_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
      'lowFrequency': 3566000000.0,
      'highFrequency': 3568000000.0
    }
    request = {'grantRequest': [grant_0, grant_1]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0]['cbsdId'], cbsd_id)
    self.assertEqual(response[1]['cbsdId'], cbsd_id)
    self.assertTrue(response[0]['response']['responseCode'] == 401
                    or response[1]['response']['responseCode'] == 401)
