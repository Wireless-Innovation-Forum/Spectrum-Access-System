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
import logging
import os
import jwt

import sas
import sas_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, generateCpiRsaKeys, generateCpiEcKeys, convertRequestToRequestWithCpiSignature


class ExclusionZoneTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_EXZ_1_default_config(self, filename):
    """Generates the WinnForum configuration for EXZ.1."""
    # Load device info
    # Load Devices located outside 50 meters of exclusion zones
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a_exz.json')))
    # Load Devices located within at least one exclusion zones
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b_exz.json')))
    # Load Devices located within 50 meters of at least one exclusion zones
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c_exz.json')))
   
    # Prepare 3 grant requests.
    # 1. With frequency range partially overlapping with the frequency 
    #     range of the nearest exclusion zone.
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3625000000.0,
        'highFrequency': 3635000000.0
    }

    # 2. With frequency range partially overlapping with the frequency 
    #     range of the nearest exclusion zone.
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3625000000.0
    grant_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3635000000.0

    # 3. With frequency range partially overlapping with the frequency 
    #     range of the nearest exclusion zone.
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3625000000.0
    grant_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3635000000.0

    # Create the actual config.
    devices = [device_a, device_b, device_c]
    grants = [grant_0, grant_1, grant_2]
    config = {
        'fccIds': [(d['fccId'], 47) for d in devices],
        'userIds': [d['userId'] for d in devices],
        'registrationRequests': devices,
        'expectedResponseCodes': [(0,), (0,), (0,)],
        'grantRequests' : grants,
        'expectedGrantResponseCodes': [(0,), (400,), (400,)],
    }
    writeConfig(filename, config)

  def generate_EXZ_2_default_config(self, filename):
    """Generates the WinnForum configuration for EXZ.1."""
    # Load device info
    # Load Devices located outside 50 meters of exclusion zones
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a_exz.json')))
    # Load Devices located within at least one exclusion zones
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b_exz.json')))
    # Load Devices located within 50 meters of at least one exclusion zones
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c_exz.json')))
   
    # Prepare 3 grant requests.
    # 1. With frequency range partially overlapping with the frequency 
    #     range of the nearest exclusion zone.
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3625000000.0,
        'highFrequency': 3635000000.0
    }

    # 2. With frequency range partially overlapping with the frequency 
    #     range of the nearest exclusion zone.
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3625000000.0
    grant_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3635000000.0

    # 3. With frequency range partially overlapping with the frequency 
    #     range of the nearest exclusion zone.
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3625000000.0
    grant_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3635000000.0

    # Create the actual config.
    devices = [device_a, device_b, device_c]
    grants = [grant_0, grant_1, grant_2]
    config = {
        'fccIds': [(d['fccId'], 47) for d in devices],
        'userIds': [d['userId'] for d in devices],
        'registrationRequests': devices,
        'expectedResponseCodes': [(0,), (0,), (0,)],
        'grantRequests' : grants,
        'expectedGrantResponseCodes': [(0,), (400,), (400,)],
    }
    writeConfig(filename, config)



  @configurable_testcase(generate_EXZ_1_default_config)
  def test_WINNF_FT_S_EXZ_1(self,config_filename):
    """Injected Exclusion Zones

    The response should be SUCCESS for CBSDs located outside 50meters of all 
    Exclusion Zones.
    The responseCode = 400 for CBSDs located within 50meters of all Exclusion Zones 
    or inside Exclusion Zones. 
    """

    #Load Exclusion Zones
    exz_record = json.load(
        open(os.path.join('testcases', 'testdata', 'exz_record_0.json')))

    # Inject EXZ database records
    # TODO Need to figure out how to send freqRange
    """
    zone_id = self._sas_admin.InjectExZone({'record':exz_record}, \
                     {'frequencyRange':{'lowFrequency': 3620000000.0,\
                      'highFrequency': 3630000000.0}})
    """
    self._sas_admin.InjectExZone({'record': exz_record})

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertEqual(
        len(config['registrationRequests']),
        len(config['expectedResponseCodes']))

    # Inject FCC IDs.
    for fcc_id in config['fccIds']:
      self._sas_admin.InjectFccId({'fccId': fcc_id})

    # Inject user IDs.
    for user_id in config['userIds']:
      self._sas_admin.InjectUserId({'userId': user_id})
   
    # Register N2, N3 and N4 CBSDs.
    device_cert = self.getCertFilename('dp_client.cert')
    device_key = self.getCertFilename('dp_client.key')

    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request, device_cert, device_key)['registrationResponse']

    # Check registration responses.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    cbsd_ids = []
    for i in range(len(responses)):
      response = responses[i]
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_response_codes)
      if response['response']['responseCode'] == 0:  # SUCCESS
        self.assertTrue('cbsdId' in response)
        cbsd_ids.append(response[i]['cbsdId'])
      else:
        self.assertFalse('cbsdId' in response)

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    del request, response, responses

    # Update CBSD Ids in Grant Req.
    request = {'grantRequest': config['grantRequests']}
    for i in range(len(request)):
       request[i]['cbsdId'] =  cbsd_ids[i] 
   
    
    # Send grant request and get response
    responses = self._sas.Grant(grantReq, device_cert,device_key)['grantResponse']

    # Check grant response array
    self.assertEqual(len(responses), len(config['grantRequests']))
    for i in range(len(responses)):
      response = responses[i]
      expected_grant_response_codes = config['expectedGrantResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_grant_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_grant_response_codes)
      if response['response']['responseCode'] == 0:  # SUCCESS
        self.assertTrue('grantId' in grantResponse)
      else:
        self.assertFalse('cbsdId' in grantResponse)
   
  @configurable_testcase(generate_EXZ_2_default_config)
  def test_WINNF_FT_S_EXZ_2(self,config_filename):
    """Exclusion Zones defined in NTIA TR 15-517

    The response should be SUCCESS for CBSDs located outside 50meters of all 
    Exclusion Zones.
    The responseCode = 400 for CBSDs located within 50meters of all Exclusion Zones 
    or inside Exclusion Zones. 
    """

    # Enforce NTIA Exlusion zones
    self.TriggerEnableNTIAExclusionZones()

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertEqual(
        len(config['registrationRequests']),
        len(config['expectedResponseCodes']))

    # Inject FCC IDs.
    for fcc_id in config['fccIds']:
      self._sas_admin.InjectFccId({'fccId': fcc_id})

    # Inject user IDs.
    for user_id in config['userIds']:
      self._sas_admin.InjectUserId({'userId': user_id})
   
    # Register N2, N3 and N4 CBSDs.
    device_cert = self.getCertFilename('dp_client.cert')
    device_key = self.getCertFilename('dp_client.key')

    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request, device_cert, device_key)['registrationResponse']

    # Check registration responses.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    cbsd_ids = []
    for i in range(len(responses)):
      response = responses[i]
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_response_codes)
      if response['response']['responseCode'] == 0:  # SUCCESS
        self.assertTrue('cbsdId' in response)
        cbsd_ids.append(response[i]['cbsdId'])
      else:
        self.assertFalse('cbsdId' in response)

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    del request, response, responses

    # Update CBSD Ids in Grant Req.
    request = {'grantRequest': config['grantRequests']}
    for i in range(len(request)):
       request[i]['cbsdId'] =  cbsd_ids[i] 
   
    
    # Send grant request and get response
    responses = self._sas.Grant(grantReq, device_cert,device_key)['grantResponse']

    # Check grant response array
    self.assertEqual(len(responses), len(config['grantRequests']))
    for i in range(len(responses)):
      response = responses[i]
      expected_grant_response_codes = config['expectedGrantResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_grant_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_grant_response_codes)
      if response['response']['responseCode'] == 0:  # SUCCESS
        self.assertTrue('grantId' in grantResponse)
      else:
        self.assertFalse('cbsdId' in grantResponse)

