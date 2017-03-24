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
import unittest

import sas
from util import winnforum_testcase


class GrantTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_10_7_4_1_1_1_1(self):
    """Successful CBSD grant request.

    CBSD sends a single grant request when no incumbent is present in the GAA
    frequency range requested by the CBSD. Response should be SUCCESS.
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
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue(response['grantId'])
    self.assertEqual(response['channelType'], 'GAA')
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_10_7_4_1_3_1_1_2(self):
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
    self.assertFalse('cbsdId' in response)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_10_7_4_1_3_1_2_1(self):
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
    self.assertEqual(response['response']['responseCode'], 103)

  def test_WINFF_FT_S_GRA_7(self):
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
  def test_WINFF_FT_S_GRA_16(self):
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
