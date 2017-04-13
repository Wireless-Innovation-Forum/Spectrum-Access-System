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
from datetime import datetime
import json
import os
import unittest

import sas
from util import winnforum_testcase


class DeregistrationTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINFF_FT_S_DER_1(self):
    """Successful CBSD deregistration request.

    CBSD sends deregistration request to SAS with its correct and valid CBSD
    ID, the response should be SUCCESS.
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

    # Deregister the device
    request = {'deregistrationRequest': [{'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINFF_FT_S_DER_2(self):
    """Valid and correct CBSD ID: two deregistrationRequest objects


    CBSD sends deregistration request to SAS with two deregistrationRequest
    objects that contain correct and valid CBSD ID, the response should be
    SUCCESS.
    """

    # Register the devices
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_1['fccId'] = "test_fcc_id_1"
    device_2['fccId'] = "test_fcc_id_2"
    self._sas_admin.InjectFccId({'fccId': device_1['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})
    request = {'registrationRequest': [device_1, device_2]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_id = []
    for x in range (0, 2) :
      self.assertEqual(response[x]['response']['responseCode'], 0)
      cbsd_id.append(response[x]['cbsdId'])
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id[0]},
        {'cbsdId': cbsd_id[1]}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']
    # Check the deregistration response
    for x in range (0, 2):
      self.assertEqual(response[x]['cbsdId'], cbsd_id[x])
      self.assertEqual(response[x]['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINFF_FT_S_DER_3(self):
    """CBSD deregistration request with missing required parameter.

    The required parameter 'cbsdId' is missing in a deregistration request,
    the response should be FAIL.
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

    # Deregister the device
    request = {'deregistrationRequest': [{}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertFalse('cbsdId' in response)
    self.assertIn(response['response']['responseCode'], [102, 105])

  @winnforum_testcase
  def test_WINFF_FT_S_DER_4(self):
    """Missing CBSD ID: two objects in the DeregistrationRequest.

    CBSD sends Deregistration Request with two objects to the SAS, first
    object has the correct CBSD ID, the second does not have CBSD ID. The
    response for the first object should be SUCCESS. The response for the
    second object should be FAIL.
    """
    
    # Register the devices
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_1['fccId'] = "test_fcc_id_1"
    device_2['fccId'] = "test_fcc_id_2"
    self._sas_admin.InjectFccId({'fccId': device_1['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})
    request = {'registrationRequest': [device_1, device_2]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 0)
    cbsd_id_1 = response[0]['cbsdId']
    del request, response
  
    # Deregister the device
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id_1},
        {}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']
    # Check the deregistration response
    self.assertEqual(response[0]['cbsdId'], cbsd_id_1)
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertFalse('cbsdId' in response[1])
    self.assertIn(response[1]['response']['responseCode'], [102, 105])

  @winnforum_testcase
  def test_WINFF_FT_S_DER_5(self):
    """CBSD deregistration request when CBSD ID does not exist in SAS.

    CBSD sends deregistration request when its CBSD ID is not in SAS,
    the response should be FAIL.
    """

    # Deregister the device before registration, thus the CBSD ID does not exist in SAS
    request = {'deregistrationRequest': [{'cbsdId': 'A nonexistent cbsd id'}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertFalse('cbsdId' in response)
    self.assertIn(response['response']['responseCode'], [103, 105])

  @winnforum_testcase
  def test_WINFF_FT_S_DER_6(self):
    """CBSD ID initially exists, CBSD deregisters first by sending
    Deregistration request. Then sends another Deregistration request
    to check that SAS indeed erased the CBSD information from its
    database.

    The response for the first Deregistration request should be SUCCESS.
    The response for the second Deregistration request should be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)

    # Deregister the device again
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINFF_FT_S_DER_7(self):
    """CBSD ID value invalid: two request objects.

    CBSD sends deregistration request to SAS with two objects in which
    the first object has the correct CBSD ID and the second object
    has an nonexistent CBSD ID. The response for the first
    object should be SUCCESS. The response for the second object
    should be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Deregister the devices
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id},
        {'cbsdId': 'A nonexistent cbsd id'}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']
    # Check the deregistration response
    self.assertEqual(response[0]['cbsdId'], cbsd_id)
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertFalse('cbsdId' in response[1])
    self.assertIn(response[1]['response']['responseCode'], [103, 105])

  @winnforum_testcase
  def test_WINFF_FT_S_DER_8(self):
    """CBSD ID initially exists with a grant, CBSD deregisters,
    then re-registers and attempts to use the old grant ID. This
    is to verify SAS deletes grants on deregistration.

    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request for grant
    grant = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response

    # Send heartbeat so the device will be in Authorized state
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertLess(datetime.utcnow(),
                    datetime.strptime(response['transmitExpireTime'],
                                      '%Y-%m-%dT%H:%M:%SZ'))
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [{'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response, cbsd_id

    # Re-register the device
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Send heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'AUTHORIZED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    response_code = response['response']['responseCode']
    # Check the heartbeat response
    self.assertIn(response_code, [103, 500])
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [{'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
