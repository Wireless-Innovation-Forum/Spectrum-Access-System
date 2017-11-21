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
  def test_WINNF_FT_S_DRG_1(self):
    """Valid and correct CBSD ID: two deregistrationRequest objects
    CBSD sends deregistration request to SAS with two deregistrationRequest
    objects that contain correct and valid CBSD ID, the response should be
    SUCCESS.
    """

    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json'):
      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    cbsd_ids = []
    self.assertEqual(len(response), 2)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [{'cbsdId': cbsd_ids[0]}, {'cbsdId': cbsd_ids[1]}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']

    # Check the deregistration response
    self.assertEqual(len(response), 2)
    for x in range(0, 2):
      self.assertEqual(response[x]['cbsdId'], cbsd_ids[x])
      self.assertEqual(response[x]['response']['responseCode'], 0)
    del request, response

     # Prepare grant requests for two cbsdIds
    grant_1 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[0]
    grant_2 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[1]

    # Send the grant requests
    request = {'grantRequest': [grant_1, grant_2]}
    response = self._sas.Grant(request)['grantResponse']

    # Check the grant responses
    # valid cbsdIds, responseCode should be 103 for both cbsdIds
    self.assertEqual(len(response), 2)
    for x, resp in enumerate(response):
      self.assertEqual(resp['response']['responseCode'], 103)
    del request, response

  @winnforum_testcase
  def test_WINNF_FT_S_DRG_2(self):
    """Missing CBSD ID: two objects in the DeregistrationRequest.
    CBSD sends Deregistration Request with two objects to the SAS, first
    object has the correct CBSD ID, the second does not have CBSD ID. The
    response for the first object should be SUCCESS. The response for the
    second object should be FAIL.
    """

    # Register two devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json'):
      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    cbsd_ids = []
    self.assertEqual(len(response), 2)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Deregister
    # Send a deregister request with two elements
    # 1st element with 1st cbsdId, the 2nd element with no cbsdId
    request = {'deregistrationRequest': [{'cbsdId': cbsd_ids[0]}, {}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']

    # Check the deregistration response
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertFalse('cbsdId' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 102)
    
