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

from datetime import datetime
import json
import os
import sas
import sas_testcase
from util import winnforum_testcase, getRandomLatLongInPolygon, \
  makePpaAndPalRecordsConsistent


class GrantTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass
 
  def test_WINNF_FT_S_GRA_2(self):
    """Grant request array with various required parameters missing.

    1. Missing cbsdId
    2. Missing operationParam object
    3. Missing maxEirp
    4. Missing highFrequency
    5. Missing lowFrequency

    Returns 102 (MISSING_PARAM) for all requests.
    """
    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json', 'device_e.json',
                            'device_f.json', 'device_g.json'):
      device = json.load(
          open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Prepare grant requests.
    # 1. Missing cbsdId.
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # 2. Missing operationParam object.
    grant_1 = {'cbsdId': cbsd_ids[1]}
    # 3. Missing maxEirp.
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[2]
    del grant_2['operationParam']['maxEirp']
    # 4. Missing highFrequency.
    grant_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_3['cbsdId'] = cbsd_ids[3]
    del grant_3['operationParam']['operationFrequencyRange']['highFrequency']
    # 5. Missing lowFrequency.
    grant_4 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_4['cbsdId'] = cbsd_ids[4]
    del grant_4['operationParam']['operationFrequencyRange']['lowFrequency']

    request = {'grantRequest': [grant_0, grant_1, grant_2, grant_3, grant_4]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse']

    self.assertEqual(len(response), 5)
    # Check grant response # 1
    self.assertFalse('cbsdId' in response[0])
    self.assertFalse('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 102)
    # Check grant response # 2, 3, 4, 5
    for response_num in (1, 2, 3, 4):
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertFalse('grantId' in response[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_7(self):
    """Invalid operationFrequencyRange.

    The response should be:
    - 103 (INVALID_VALUE) for first request.
    - 103 or 300 (UNSUPPORTED_SPECTRUM) for second and third requests.
    """
    # Register three devices
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

    devices = [device_a, device_c, device_e]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)

    # Check registration response
    cbsd_ids = []
    for resp in response['registrationResponse']:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Prepare 3 grant requests.
    # 1. With lowFrequency > highFrequency.
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000.0,
        'highFrequency': 3550000000.0
    }

    # 2. With frequency range completely outside the CBRS band.
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3350000000.0
    grant_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3450000000.0

    # 3. With frequency range partially overlapping with the CBRS band.
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[2]
    grant_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3450000000.0
    grant_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3650000000.0

    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse']

    # Check grant response array
    self.assertEqual(len(response), 3)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertFalse('grantId' in resp)
    self.assertEqual(response[0]['response']['responseCode'], 103)
    self.assertTrue(response[1]['response']['responseCode'], 300)
    self.assertTrue(response[2]['response']['responseCode'], 300)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_8(self):
    """CBSD requests a frequency range which is a mix of PAL and GAA channel.

    The Response Code should be 103.
    """
    # Load a device.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Load data
    pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,
                                                            [pal_record],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            device_a['userId'])

    # Move the device into the PPA zone
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = getRandomLatLongInPolygon(ppa_record)
    # Register device
    cbsd_ids = self.assertRegistered([device_a])

    # Update PPA record with device_a's CBSD ID and Inject data
    ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[0]]
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record})
    self.assertTrue(zone_id)

    # Create grant request
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    # Set overlapping PAL frequency spectrum
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': pal_low_frequency,
        'highFrequency': pal_high_frequency + 10000000
    }

    request = {'grantRequest': [grant_0]}
    # Send grant request
    response = self._sas.Grant(request)['grantResponse'][0]

    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)
    
  @winnforum_testcase
  def test_WINNF_FT_S_GRA_9(self):
    """Frequency range requested by a CBSD overlaps with PAL channel and
    the CBSD is inside claimed PPA boundary.

    Response Code should be 400 for second device
    """

    # Load the devices, data
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    user_id = device_a['userId']
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(ppa_record,
                                                            [pal_record],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            user_id)

    # Move device_a and device_c into the PPA zone
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = getRandomLatLongInPolygon(ppa_record)
    device_c['installationParam']['latitude'], device_c['installationParam'][
        'longitude'] = getRandomLatLongInPolygon(ppa_record)

    # Register the two devices.
    cbsd_ids = self.assertRegistered([device_a, device_c])

    # Update PPA record with only device_a's CBSD ID and Inject data
    ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[0]]
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record})
    self.assertTrue(zone_id)

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Create grant request for second device
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c['cbsdId'] = cbsd_ids[1]
    # Set frequency range that overlaps with PAL frequency.
    grant_c['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': pal_low_frequency,
        'highFrequency': pal_high_frequency
    }

    request = {'grantRequest': [grant_c]}
    # Send grant request
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response for second device response code 400
    self.assertEqual(response['cbsdId'], cbsd_ids[1])
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 400)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_15(self):
    """Two grant requests: 1. Missing maxEirp and 2. Invalid frequency range.

    Returns 102 (MISSING_PARAM) for first request.
            103 (INVALID_VALUE) for second request.
    """
    # Register two devices
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
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Prepare grant requests.
    # 1. maxEirp is missing.
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    del grant_0['operationParam']['maxEirp']

    # 2. highFrequency is lower than the lowFrequency.
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

    self.assertEqual(len(response), 2)
    # Check grant response # 1
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertFalse('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 102)
    # Check grant response # 2
    self.assertEqual(response[1]['cbsdId'], cbsd_ids[1])
    self.assertFalse('grantId' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 103)

 @winnforum_testcase
  def test_WINNF_FT_S_GRA_16(self):
    """Two grant requests for overlapping frequency range.

    Returns 401 (GRANT_CONFLICT) for at least one request.
    """
    # Register a device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id = response['cbsdId']
    del request, response

    # Prepare grant requests with overlapping frequency range
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3560000000.0,
        'highFrequency': 3570000000.0
    }
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3560000000.0,
        'highFrequency': 3580000000.0
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
    for resp in response:
      if resp['response']['responseCode'] == 0:
        # Check grantExpireTime with a correct format is included.
        self.assertTrue('grantExpireTime' in resp)
        grant_expire_time = datetime.strptime(
            resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
        self.assertLess(datetime.utcnow(), grant_expire_time)
        # Check heartbeatInterval with a correct format is included.
        self.assertTrue('heartbeatInterval' in resp)
        self.assertIsInstance(resp['heartbeatInterval'], int)
        self.assertTrue(resp['heartbeatInterval'] > 0)
