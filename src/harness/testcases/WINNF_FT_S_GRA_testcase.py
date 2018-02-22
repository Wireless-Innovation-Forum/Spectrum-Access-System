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
import logging
import os
import sas
import sas_testcase
import time
from util import winnforum_testcase, getRandomLatLongInPolygon, \
  makePpaAndPalRecordsConsistent, configurable_testcase, writeConfig, \
  loadConfig, addCbsdIdsToRequests


class GrantTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_1(self):
    """Federal Incumbent present in the PAL frequency range requested by the CBSD
     who is inside the DPA Neighborhood.

     grant responseCode = 0 and in heartbeat responseCode = 501(SUSPENDED_GRANT)
     or  grant responseCode = 400
    """
    # Trigger SAS to load DPAs
    self._sas_admin.TriggerLoadDpas()
    # Trigger SAS to de-active all the DPAs
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})
    #Fix PAl frequency
    pal_low_frequency = 3600000000
    pal_high_frequency = 3610000000
    # Load the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Load PAL and PPA
    pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_2.json')))
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_2.json')))
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
    # Trigger SAS to active one DPA on channel c
    self._sas_admin.TriggerDpaActivation(\
        {'frequencyRange': {'lowFrequency': pal_low_frequency ,\
                           'highFrequency': pal_high_frequency },'dpaId': 'east_dpa4'})
    # UNAPPROVED Not in WINNF-TS-0016 Release 1 Spec, but necessary Step for DPA
    time.sleep(240)
    # Send grant request
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_0['operationParam']['operationFrequencyRange']['lowFrequency'] \
        = pal_low_frequency
    grant_0['operationParam']['operationFrequencyRange']['highFrequency'] \
        = pal_high_frequency
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    if response['response']['responseCode'] == 400 :
      return
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertTrue('grantId' in response)
    grant_id = response['grantId']
    self.assertEqual(response['channelType'], 'PAL')
    heartbeat_request = {
    'cbsdId': cbsd_ids[0],
    'grantId': grant_id,
    'operationState': 'GRANTED'
    }
    del request, response
    # Send heartbeat request
    request = {'heartbeatRequest': [heartbeat_request]}
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check heartbeat response
    self.assertEqual(response['response']['responseCode'], 501)
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['grantId'], grant_id)
    transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
    self.assertLessEqual(transmit_expire_time, datetime.utcnow())

  @winnforum_testcase
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
  def test_WINNF_FT_S_GRA_3(self):
    """CBSD grant request when CBSD ID does not exist in SAS.
    CBSD sends grant request when its CBSD Id is not in SAS. The response
    should be FAIL.
    """

    # Send grant request with CBSD ID not exists in SAS
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = 'A non-exist cbsd id'
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertFalse('cbsdId' in response)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_4(self):
    """cbsdId send by the CBSD is not its cbsdId but some other.

     SAS rejects the request by sending responseCode 103
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

    # Send grant request for device_a using device_c_cert and device_c_key
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id_a

    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request, device_c_cert, device_c_key)['grantResponse'][0]
    # Check grant Response
    self.assertFalse('cbsdId' in response)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

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
        'lowFrequency': 3650000000,
        'highFrequency': 3550000000
    }

    # 2. With frequency range completely outside the CBRS band.
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3350000000
    grant_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3450000000

    # 3. With frequency range partially overlapping with the CBRS band.
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[2]
    grant_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3450000000
    grant_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3650000000

    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse']

    # Check grant response array
    self.assertEqual(len(response), 3)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertFalse('grantId' in resp)
    self.assertEqual(response[0]['response']['responseCode'], 103)
    self.assertEqual(response[1]['response']['responseCode'], 300)
    self.assertEqual(response[2]['response']['responseCode'], 300)

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
  def test_WINNF_FT_S_GRA_10(self):
    """First request for 2 devices granted as PAL and GAA channel,
    send next request for PAL and GAA channel for the same frequency range.

    Response Code '0' for first request and '401' for next request.
    """
    # Load two devices.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

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

    # Insert device_a into the PPA zone.
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = getRandomLatLongInPolygon(ppa_record)
    # Register 2 devices
    cbsd_ids = self.assertRegistered([device_a, device_c])

    # Update PPA Record with CBSD ID and Inject data.
    ppa_record['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[0]]
    self._sas_admin.InjectPalDatabaseRecord(pal_record[0])
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record})
    self.assertTrue(zone_id)

    # Create grant request
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': pal_low_frequency,
        'highFrequency': pal_high_frequency
    }
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3560000000,
        'highFrequency': 3570000000
    }
    request = {'grantRequest': [grant_0, grant_1]}

    # Send grant request first time
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response, must be response code 0.
    self.assertEqual(len(response), 2)
    for response_num in [0, 1]:
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertTrue('grantId' in response[response_num])
      self.assertTrue('grantExpireTime' in response[response_num])
      datetime.strptime(response[response_num]['grantExpireTime'],
                        '%Y-%m-%dT%H:%M:%SZ')
      self.assertTrue('heartbeatInterval' in response[response_num])
      self.assertIsInstance(response[response_num]['heartbeatInterval'], int)
      self.assertTrue(response[response_num]['heartbeatInterval'] > 0)
      self.assertFalse('operationParam' in response[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 0)
    self.assertEqual(response[0]['channelType'], 'PAL')
    self.assertEqual(response[1]['channelType'], 'GAA')
    del request, response

    request = {'grantRequest': [grant_0, grant_1]}
    # Send the same grant request again.
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response, must be response code 401.
    for response_num in [0, 1]:
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertFalse('grantId' in response[response_num])
      self.assertFalse('grantExpireTime' in response[response_num])
      self.assertFalse('heartbeatInterval' in response[response_num])
      self.assertFalse('operationParam' in response[response_num])
      self.assertFalse('channelType' in response[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 401)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_13(self):
    """Requests for multiple PAL channels and for multiple GAA channels.

    No incumbent present in the PAL and GAA frequency ranges used in the
    requests.

    The response should be 0.
    """

    # Load 3 devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))

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

    # Inject two PAL database records
    self._sas_admin.InjectPalDatabaseRecord(pal_record1[0])
    self._sas_admin.InjectPalDatabaseRecord(pal_record2[0])

    # Register 3 devices.
    cbsd_ids = self.assertRegistered([device_a, device_c, device_e])

    # Update PPA record with device_a's CBSD ID and Inject zone data
    ppa_record1['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[0]]
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record1})
    self.assertTrue(zone_id)

    # Update PPA record with device_c's CBSD ID and Inject data
    ppa_record2['ppaInfo']['cbsdReferenceId'] = [cbsd_ids[1]]
    zone_id = self._sas_admin.InjectZoneData({'record': ppa_record2})
    self.assertTrue(zone_id)

    # Create grant requests
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_1['cbsdId'] = cbsd_ids[1]
    grant_2['cbsdId'] = cbsd_ids[2]
    # Grant 1 & 2: Request for PAL frequency
    # Grant 3: Frequency does not overlap with FR1 and FR2
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': pal_low_frequency1,
        'highFrequency': pal_high_frequency1
    }
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': pal_low_frequency2,
        'highFrequency': pal_high_frequency2
    }
    grant_2['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3630000000,
        'highFrequency': 3640000000
    }
    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Send grant requests
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response 1 and 2
    self.assertEqual(len(response), 3)
    for response_num, resp in enumerate(response[:2]):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertTrue('grantId' in resp)
      self.assertEqual(resp['channelType'], 'PAL')
      self.assertEqual(resp['response']['responseCode'], 0)
    # Check grantExpireTime is less than corresponding PAL licenseExpiration
    self.assertLess(
        datetime.strptime(response[0]['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'),
        datetime.strptime(
            pal_record1[0]['license']['licenseExpiration'],
            '%Y-%m-%dT%H:%M:%SZ'))
    self.assertLess(
        datetime.strptime(response[1]['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'),
        datetime.strptime(
            pal_record2[0]['license']['licenseExpiration'],
            '%Y-%m-%dT%H:%M:%SZ'))
    # Check grant response 3
    self.assertEqual(response[2]['cbsdId'], cbsd_ids[2])
    self.assertTrue('grantId' in response[2])
    self.assertEqual(response[2]['channelType'], 'GAA')
    self.assertEqual(response[2]['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_11(self):
    """Un-Supported CBSD maximum EIRP

    The response should be:
    - 103 (INVALID_VALUE) for all initial grant requests
    - 0 for all 2nd grant requests
    """

    # Register five devices
    # devices 1,2 category A
    # devices 3-5 category B
    device_1 = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_4 = json.load(open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_5 = json.load(open(os.path.join('testcases', 'testdata', 'device_h.json')))

    # Pre-load conditionals for cbsdIDs 3,4,5 (cbsdCategory B)
    conditionals_3 = {
        'cbsdCategory': device_3['cbsdCategory'],
        'fccId': device_3['fccId'],
        'cbsdSerialNumber': device_3['cbsdSerialNumber'],
        'airInterface': device_3['airInterface'],
        'installationParam': device_3['installationParam'],
        'measCapability': device_3['measCapability']
    }

    # add eirpCapability=40 to only conditional forcbsdId 4
    device_4['installationParam']['eirpCapability'] = 40
    conditionals_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }


    conditionals_5 = {
        'cbsdCategory': device_5['cbsdCategory'],
        'fccId': device_5['fccId'],
        'cbsdSerialNumber': device_5['cbsdSerialNumber'],
        'airInterface': device_5['airInterface'],
        'installationParam': device_5['installationParam'],
        'measCapability': device_5['measCapability']
    }

    conditionals = {
        'registrationData': [conditionals_3, conditionals_4, conditionals_5]
    }

    # setup fccMaxEirp for all cbsdIds
    self._sas_admin.InjectFccId({'fccId': device_1['fccId'], 'fccMaxEirp': 30})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId'], 'fccMaxEirp': 20})
    self._sas_admin.InjectFccId({'fccId': device_3['fccId'], 'fccMaxEirp': 40})
    self._sas_admin.InjectFccId({'fccId': device_4['fccId'], 'fccMaxEirp': 47})
    self._sas_admin.InjectFccId({'fccId': device_5['fccId'], 'fccMaxEirp': 30})

    self._sas_admin.InjectUserId({'userId': device_1['userId']})
    self._sas_admin.InjectUserId({'userId': device_2['userId']})
    self._sas_admin.InjectUserId({'userId': device_3['userId']})
    self._sas_admin.InjectUserId({'userId': device_4['userId']})
    self._sas_admin.InjectUserId({'userId': device_5['userId']})

    self._sas_admin.PreloadRegistrationData(conditionals)

    # Remove conditionals from registration for cbsdId 3,5
    del device_3['cbsdCategory']
    del device_3['airInterface']
    del device_3['installationParam']
    del device_3['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']
    del device_5['cbsdCategory']
    del device_5['airInterface']
    del device_5['installationParam']
    del device_5['measCapability']

    # set eirpCapability = 20 for cbsdId 1
    device_1['installationParam']['eirpCapability'] = 20

    # send registration requests
    devices = [device_1, device_2, device_3, device_4, device_5]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    cbsd_ids = []
    self.assertEqual(len(response), 5)
    for x in range(0, 5):
      cbsd_ids.append(response[x]['cbsdId'])
      self.assertEqual(response[x]['response']['responseCode'], 0)
    del request, response

    # Prepare 5 grant requests with various un-supported maxEirp values
    grant_1 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[0]
    grant_1['operationParam']['maxEirp'] = 11
    grant_2 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[1]
    grant_2['operationParam']['maxEirp'] = 11
    grant_3 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_3['cbsdId'] = cbsd_ids[2]
    grant_3['operationParam']['maxEirp'] = 31
    grant_4 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_4['cbsdId'] = cbsd_ids[3]
    grant_4['operationParam']['maxEirp'] = 31
    grant_5 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_5['cbsdId'] = cbsd_ids[4]
    grant_5['operationParam']['maxEirp'] = 21

    # Send the grant requests
    request = {'grantRequest': [grant_1, grant_2, grant_3, grant_4, grant_5]}
    response = self._sas.Grant(request)['grantResponse']

    # Check the grant responses
    # No grantIds, responseCode should be 103
    self.assertEqual(len(response), 5)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertFalse('grantId' in resp)
      self.assertEqual(resp['response']['responseCode'], 103)
    del request, response

    # Prepare 5 grant requests with various supported maxEirp values
    grant_1['operationParam']['maxEirp'] = 10
    grant_2['operationParam']['maxEirp'] = 10
    grant_3['operationParam']['maxEirp'] = 20
    grant_4['operationParam']['maxEirp'] = 30
    grant_5['operationParam']['maxEirp'] = 20

    # Send the grant requests
    request = {'grantRequest': [grant_1, grant_2, grant_3, grant_4, grant_5]}
    response = self._sas.Grant(request)['grantResponse']

    # Check the grant responses
    # response should have valid cbsdIds, grantIds, responseCode 0
    self.assertEqual(len(response), 5)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertTrue('grantId' in resp)
      self.assertEqual(resp['response']['responseCode'], 0)
    del request, response

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_12(self):
    """Blacklisted CBSD in Array Request (responseCode 101)

    The response should be:
    - responseCode 0 for the first and second cbsdIds
    - responseCode 101 for the third cbsdId
    """

    # Register three devices
    device_1 = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(open(os.path.join('testcases', 'testdata', 'device_e.json')))

    self._sas_admin.InjectFccId({'fccId': device_1['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_3['fccId']})

    self._sas_admin.InjectUserId({'userId': device_1['userId']})
    self._sas_admin.InjectUserId({'userId': device_2['userId']})
    self._sas_admin.InjectUserId({'userId': device_3['userId']})

    # send registration requests
    devices = [device_1, device_2, device_3]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    cbsd_ids = []
    self.assertEqual(len(response), 3)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Blacklist the third cbsdId
    self._sas_admin.BlacklistByFccId({'fccId': device_3['fccId']})

    # Prepare the grant requests
    grant_1 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[0]
    grant_2 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[1]
    grant_3 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_3['cbsdId'] = cbsd_ids[2]

    # Send the grant requests
    request = {'grantRequest': [grant_1, grant_2, grant_3]}
    response = self._sas.Grant(request)['grantResponse']

    # Check the grant responses
    #
    # Each cbsdId should be valid
    self.assertEqual(len(response), 3)
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[1]['cbsdId'], cbsd_ids[1])


    # 1st and 2nd cbsdId responseCode should be 0
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 0)

    # 1st and 2nd cbsdId should have channelType set to GAA
    self.assertEqual(response[0]['channelType'], 'GAA')
    self.assertEqual(response[1]['channelType'], 'GAA')

    # 3rd cbsdId responseCode should be 101
    self.assertEqual(response[2]['response']['responseCode'], 101)
    del request, response

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
        'lowFrequency': 3650000000,
        'highFrequency': 3550000000
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
        'lowFrequency': 3560000000,
        'highFrequency': 3570000000
    }
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3560000000,
        'highFrequency': 3580000000
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

  def generate_GRA_17_default_config(self, filename):
    """Generates the WinnForum configuration for GRA.17."""
    # Load device info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # device_a, device_c, device_e and device_f are Category A.
    self.assertEqual(device_a['cbsdCategory'], 'A')
    self.assertEqual(device_c['cbsdCategory'], 'A')
    self.assertEqual(device_e['cbsdCategory'], 'A')
    self.assertEqual(device_f['cbsdCategory'], 'A')

    # Device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam']
    }
    conditionals = {'registrationData': [conditionals_b]}
    del device_b['installationParam']
    del device_b['cbsdCategory']
    del device_b['airInterface']

    # Prepare grant requests.
    # All valid parameters, will have device_a CBSD ID
    grant_0 = {
        'cbsdId': 0,
        'operationParam': {
            'maxEirp': 10,
            'operationFrequencyRange': {
                'lowFrequency': 3550000000,
                'highFrequency': 3560000000
            }
        }
    }
    # CBSD ID will be removed (device_b)
    grant_1 = {
        'cbsdId': 'REMOVE',
        'operationParam': {
            'maxEirp': 10,
            'operationFrequencyRange': {
                'lowFrequency': 3620000000,
                'highFrequency': 3630000000
            }
        }
    }
    # LowFrequency > HighFrequency, will have device_c CBSD ID
    grant_2 = {
        'cbsdId': 2,
        'operationParam': {
            'maxEirp': 10,
            'operationFrequencyRange': {
                'lowFrequency': 3640000000,
                'highFrequency': 3630000000
            }
        }
    }
    # Partially outside CBRS band, will have device_e CBSD ID
    grant_3 = {
        'cbsdId': 3,
        'operationParam': {
            'maxEirp': 10,
            'operationFrequencyRange': {
                'lowFrequency': 3450000000,
                'highFrequency': 3600000000
            }
        }
    }
    # CBSD not part of claimed PPA, but in the PPA zone; requests PAL channel
    # will have device_f CBSD ID
    grant_4 = {
        'cbsdId': 4,
        'operationParam': {
            'maxEirp': 10,
            'operationFrequencyRange': {
                'lowFrequency': 3550000000,
                'highFrequency': 3560000000
            }
        }
    }
    # Create the actual config.
    devices = [device_a, device_b, device_c, device_e, device_f]
    grant_requests = [grant_0, grant_1, grant_2, grant_3, grant_4,]
    # Devices inside and part of the claimed PPA.
    # Contains the index of devices in the devices list.
    # Eg: 0 means devices[0] which is device_a
    ppa_cluster_list = [0]
    # Devices in the zone, but not part of PPA.
    # Contains the index of devices in the devices list.
    # Eg: 4 means devices[4] which is device_f
    devices_in_ppa_zone = [4]
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record, pal_record = makePpaAndPalRecordsConsistent(
        ppa_record, [pal_record], pal_low_frequency, pal_high_frequency,
        devices[ppa_cluster_list[0]]['userId'])
    # Move devices in ppa_cluster_list and devices_in_ppa_zone
    # into the PPA zone
    for device_index in ppa_cluster_list:
      devices[device_index]['installationParam']['latitude'], devices[
          device_index]['installationParam'][
              'longitude'] = getRandomLatLongInPolygon(ppa_record)
    for device_index in devices_in_ppa_zone:
      devices[device_index]['installationParam']['latitude'], devices[
          device_index]['installationParam'][
              'longitude'] = getRandomLatLongInPolygon(ppa_record)

    config = {
        'registrationRequest': devices,
        'conditionalRegistrationData': conditionals,
        'ppa': {
            'ppaRecord': ppa_record,
            'palRecords': pal_record,
            # Indexing the same way as CBSD IDs.
            'ppaClusterList': ppa_cluster_list
        },
        'grantRequest': grant_requests,
        'expectedResponseCodes': [
            (0,),  # all valid params => SUCCESS
            (102,),  # missing CBSD ID => MISSING_PARAM
            (103,),  # LowFrequency > HighFrequency => INVALID_VALUE
            (300,),  # partially overlapping CBRS band => UNSUPPORTED_SPECTRUM
            (400,),  # CBSD inside (but not part of) claimed PPA => INTERFERENCE
        ]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_GRA_17_default_config)
  def test_WINNF_FT_S_GRA_17(self, config_filename):
    """[Configurable] Array grant request."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertEqual(
        len(config['registrationRequest']),
        len(config['grantRequest']))
    self.assertEqual(
        len(config['grantRequest']),
        len(config['expectedResponseCodes']))

    # Whitelist FCC IDs.
    for device in config['registrationRequest']:
      self._sas_admin.InjectFccId({
          'fccId': device['fccId'],
          'fccMaxEirp': 47
      })

    # Whitelist user IDs.
    for device in config['registrationRequest']:
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Pre-load conditional registration data for N3 CBSDs.
    if ('conditionalRegistrationData' in config) and (
        config['conditionalRegistrationData']):
      self._sas_admin.PreloadRegistrationData(
          config['conditionalRegistrationData'])

    # Inject PAL database record
    for pal_record in config['ppa']['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Register devices
    cbsd_ids = self.assertRegistered(config['registrationRequest'])

    # Update PPA record with device's CBSD ID and Inject zone data
    for device_index in config['ppa']['ppaClusterList']:
      config['ppa']['ppaRecord']['ppaInfo']['cbsdReferenceId'] = [
          cbsd_ids[device_index]
      ]
    zone_id = self._sas_admin.InjectZoneData({
        'record': config['ppa']['ppaRecord']
    })
    self.assertTrue(zone_id)

    # Send Grant request
    grant_request = config['grantRequest']
    addCbsdIdsToRequests(cbsd_ids, grant_request)
    request = {'grantRequest': grant_request}
    responses = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(responses), len(config['expectedResponseCodes']))
    for i, response in enumerate(responses):
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_response_codes)
      # If the corresponding request contained a valid cbsdId, the
      # response shall contain the same cbsdId.
      if 'cbsdId' in grant_request[i]:
        if grant_request[i]['cbsdId'] in cbsd_ids:
          self.assertEqual(response['cbsdId'], grant_request[i]['cbsdId'])
          # If response is SUCCESS, verify the response contains a
          # valid Grant ID.
          if response['response']['responseCode'] == 0:
            self.assertTrue('grantId' in response)
          else:
            self.assertFalse('grantId' in response)
