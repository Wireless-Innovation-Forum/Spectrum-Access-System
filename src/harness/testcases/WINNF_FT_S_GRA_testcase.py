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


