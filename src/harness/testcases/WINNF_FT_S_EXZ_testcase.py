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
    device_a_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a_1['installationParam']['latitude'] = 40.31304
    device_a_1['installationParam']['longitude'] =  -96.25122
    device_a_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a_2['installationParam']['latitude'] = 40.35491
    device_a_2['installationParam']['longitude'] =  -96.4215
    device_a_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a_3['installationParam']['latitude'] = 40.40931
    device_a_3['installationParam']['longitude'] =  -96.09191

    # Load Devices located within at least one exclusion zones
    device_b_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b_1['installationParam']['latitude'] = 39.6945
    device_b_1['installationParam']['longitude'] =  -96.427
    device_b_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b_2['installationParam']['latitude'] = 39.66068
    device_b_2['installationParam']['longitude'] =  -96.72912

    # Load Devices located within 50 meters of at least one exclusion zones
    device_c_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c_1['installationParam']['latitude'] = 39.96317
    device_c_1['installationParam']['longitude'] =  -96.24692
    device_c_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c_2['installationParam']['latitude'] = 39.96488
    device_c_2['installationParam']['longitude'] =  -96.27267
    device_c_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c_3['installationParam']['latitude'] = 39.96422
    device_c_3['installationParam']['longitude'] =  -96.26649
   
    #Load Exclusion Zones
    exz_record = json.load(
        open(os.path.join('testcases', 'testdata', 'exz_record_0.json')))
    exz_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'exz_record_1.json')))

    # Create the actual config.
    devices = [device_a_1, device_a_2, device_a_3, device_b_1, device_b_2, device_c_1, device_c_2, device_c_3]
    ex_zones = [exz_record, exz_record_1]
    config = {
        'registrationRequests': devices,
        'exclusionZoneRecords' : ex_zones
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
    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertNotEqual(len(config['exclusionZoneRecords']) , 0, "Exclusion zone records are zero !!!")

    # Get exclusion zone records from config file.
    exz_record = {'exclusionZone': config['exclusionZoneRecords']}

    for i in range(len(exz_record)):
       # Inject EXZ database records
       self._sas_admin.InjectExclusionZone({'record': exz_record})

    # Register the devices
    cbsd_ids = self.assertRegistered(config['registrationRequests'])

    # Execute CPAS and wait untill completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    
    # Send multiple grant requests
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
      grant['cbsdId'] = cbsd_id
      #  Update frequency range to partially overlapping with the frequency 
      #     range of the nearest exclusion zone.
      grant['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3625000000.0
      grant['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3635000000.0
      grant_request.append(grant)

    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    #validate the response
    self.assertEqual(len(response), 8)

    for response_num, resp in enumerate(response):
       if resp['response']['responseCode'] == 0 :
          self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
          self.assertTrue('grantId' in resp)
          self.assertEqual(resp['response']['responseCode'], 0)
       else:
          self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
          self.assertFalse('grantId' in resp)
          self.assertEqual(resp['response']['responseCode'], 400)

  def generate_EXZ_2_default_config(self, filename):
    """Generates the WinnForum configuration for EXZ.2."""
    # Load device info
    # Load Devices located outside 50 meters of exclusion zones
    device_a_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a_1['installationParam']['latitude'] = 40.31260
    device_a_1['installationParam']['longitude'] =  -96.25100
    device_a_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a_2['installationParam']['latitude'] = 40.31304
    device_a_2['installationParam']['longitude'] =  -96.25122
    device_a_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a_3['installationParam']['latitude'] = 40.31358
    device_a_3['installationParam']['longitude'] =  -96.25144

    # Load Devices located within at least one exclusion zones
    device_b_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b_1['installationParam']['latitude'] = 39.6920
    device_b_1['installationParam']['longitude'] =  -96.400
    device_b_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b_2['installationParam']['latitude'] = 39.6945
    device_b_2['installationParam']['longitude'] =  -96.427

    # Load Devices located within 50 meters of at least one exclusion zones
    device_c_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c_1['installationParam']['latitude'] = 39.96300
    device_c_1['installationParam']['longitude'] =  -96.24656
    device_c_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c_2['installationParam']['latitude'] = 39.96317
    device_c_2['installationParam']['longitude'] =  -96.24692
    device_c_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c_3['installationParam']['latitude'] = 39.96330
    device_c_3['installationParam']['longitude'] =  -96.24712
 
    # Create the actual config.
    devices = [device_a_1, device_a_2, device_a_3, device_b_1, device_b_2, device_c_1, device_c_2, device_c_3]
    config = {
        'registrationRequests': devices,
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_EXZ_2_default_config)
  def test_WINNF_FT_S_EXZ_2(self,config_filename):
    """Exclusion Zones defined in NTIA TR 15-517

    The response should be SUCCESS for CBSDs located outside 50meters of all 
    Exclusion Zones.
    The responseCode = 400 for CBSDs located within 50meters of all Exclusion Zones 
    or inside Exclusion Zones. 
    """

    # Enforce NTIA Exlusion zones
    self._sas_admin.TriggerEnableNTIAExclusionZones()
    config = loadConfig(config_filename)
    # Register the devices
    cbsd_ids = self.assertRegistered(config['registrationRequests'])
    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Send multiple grant requests
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
      grant['cbsdId'] = cbsd_id
      #  Update frequency range to partially overlapping with the frequency 
      #     range of the nearest exclusion zone.
      grant['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3625000000.0
      grant['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3635000000.0
      grant_request.append(grant)

    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']

    #validate the response
    self.assertEqual(len(response), 8)

    for response_num, resp in enumerate(response):
       if resp['response']['responseCode'] == 0 :
          self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
          self.assertTrue('grantId' in resp)
          self.assertEqual(resp['response']['responseCode'], 0)
       else:
          self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
          self.assertFalse('grantId' in resp)
          self.assertEqual(resp['response']['responseCode'], 400)

