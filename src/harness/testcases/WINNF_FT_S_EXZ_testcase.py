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
    device_N2_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_N2_1['installationParam']['latitude'] = 40.31304
    device_N2_1['installationParam']['longitude'] =  -96.25122
    device_N2_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_N2_2['installationParam']['latitude'] = 40.35491
    device_N2_2['installationParam']['longitude'] =  -96.4215
    device_N2_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_N2_3['installationParam']['latitude'] = 40.40931
    device_N2_3['installationParam']['longitude'] =  -96.09191

    # Load Devices located within at least one exclusion zones
    device_N3_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_N3_1['installationParam']['latitude'] = 39.6945
    device_N3_1['installationParam']['longitude'] =  -96.427
    device_N3_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_N3_2['installationParam']['latitude'] = 39.66068
    device_N3_2['installationParam']['longitude'] =  -96.72912

    # Load Devices located within 50 meters of at least one exclusion zones
    device_N4_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_N4_1['installationParam']['latitude'] = 39.96317
    device_N4_1['installationParam']['longitude'] =  -96.24692
    device_N4_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_N4_2['installationParam']['latitude'] = 39.96488
    device_N4_2['installationParam']['longitude'] =  -96.27267
    device_N4_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_N4_3['installationParam']['latitude'] = 39.96422
    device_N4_3['installationParam']['longitude'] =  -96.26649
   
    #Load Exclusion Zones
    exz_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'exz_record_0.json')))
    exz_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'exz_record_1.json')))


    # Forming N2 grant request with overlapping frequency
    grant_N2_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))   
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N2_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N2_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N2_3['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N2_3['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0

    # Forming N3 grant request 
    grant_N3_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3655000000.0
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3650000000.0
    grant_N3_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3655000000.0
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3650000000.0


    # Forming N4 grant request with overlapping frequency
    grant_N4_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N4_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N4_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N4_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N4_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N4_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N4_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N4_3['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N4_3['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
 
    grants_N2 = [grant_N2_1, grant_N2_2, grant_N2_3]
    grants_N3 = [grant_N3_1, grant_N3_2]
    grants_N4 = [grant_N4_1, grant_N4_2, grant_N4_3]


    # Creating frequency ranges for exz0 and exz1
    freqrange_exzrec0 = {'lowFrequency': 3550000000, 'highFrequency': 3650000000 }
    freqrange_exzrec1 = {'lowFrequency': 3650000000, 'highFrequency': 3700000000 }

    # Create the actual config.
    devices_N2 = [device_N2_1, device_N2_2, device_N2_3]
    devices_N3 = [device_N3_1, device_N3_2]
    devices_N4 = [device_N4_1, device_N4_2, device_N4_3]

    ex_zones = [exz_record_0, exz_record_1]
    freq_ranges = [freqrange_exzrec0,freqrange_exzrec1]


    config = {
        'registrationRequests_N2' : devices_N2,
        'registrationRequests_N3' : devices_N3,
        'registrationRequests_N4' : devices_N4, 
        'exclusionZoneRecords' : ex_zones,
        'frequencyRange' : freq_ranges,
        'grants_N2' : grants_N2,
        'grants_N3' : grants_N3, 
        'grants_N4' : grants_N4 
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

    for i in range(len(config['exclusionZoneRecords'])):
       # Inject EXZ database records
       exzData = {'exclusionZone': config['exclusionZoneRecords'][i]}
       self._sas_admin.InjectExclusionZone({'record': exzData},config['frequencyRange'][i])    


    # Register N2 devices
    cbsd_ids_N2 = self.assertRegistered(config['registrationRequests_N2'])

    # Register N3 devices
    cbsd_ids_N3 = self.assertRegistered(config['registrationRequests_N3'])

    # Register N4 devices
    cbsd_ids_N4 = self.assertRegistered(config['registrationRequests_N4'])

    # Execute CPAS and wait untill completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Generating grant requests for N2 and validating responses
    grant_request = []
    for i in range(len(config['grants_N2'])):
        config['grants_N2'][i]['cbsdId'] = cbsd_ids_N2[i]
        grant_request.append(config['grants_N2'][i])

    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))

    for response_num, resp in enumerate(response):
          self.assertEqual(resp['cbsdId'], cbsd_ids_N2[response_num])
          self.assertTrue('grantId' in resp)
          #self.assertEqual(resp['response']['responseCode'], 400)


    # Generating grant requests for N3 and validating responses
    grant_request = []
    for i in range(len(config['grants_N3'])):
        config['grants_N3'][i]['cbsdId'] = cbsd_ids_N3[i]
        grant_request.append(config['grants_N3'][i])

  
    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))

    for response_num, resp in enumerate(response):
          self.assertEqual(resp['cbsdId'], cbsd_ids_N3[response_num])
          self.assertTrue('grantId' in resp)
          #self.assertEqual(resp['response']['responseCode'], 400)

    # Generating grant requests for N4 and validating responses
    grant_request = []
    for i in range(len(config['grants_N4'])):
        config['grants_N4'][i]['cbsdId'] = cbsd_ids_N4[i]
        grant_request.append(config['grants_N4'][i])


    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))

    for response_num, resp in enumerate(response):
          self.assertEqual(resp['cbsdId'], cbsd_ids_N4[response_num])
          self.assertTrue('grantId' in resp)
          #self.assertEqual(resp['response']['responseCode'], 400)


  def generate_EXZ_2_default_config(self, filename):
    """Generates the WinnForum configuration for EXZ.2."""
    # Load device info
    # Load Devices located outside 50 meters of exclusion zones
    device_N1_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_N1_1['installationParam']['latitude'] = 40.31260
    device_N1_1['installationParam']['longitude'] =  -96.25100
    device_N1_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_N1_2['installationParam']['latitude'] = 40.31304
    device_N1_2['installationParam']['longitude'] =  -96.25122
    device_N1_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_N1_3['installationParam']['latitude'] = 40.31358
    device_N1_3['installationParam']['longitude'] =  -96.25144

    # Load Devices located within at least one exclusion zones
    device_N2_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_N2_1['installationParam']['latitude'] = 39.6920
    device_N2_1['installationParam']['longitude'] =  -96.400
    device_N2_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_N2_2['installationParam']['latitude'] = 39.6945
    device_N2_2['installationParam']['longitude'] =  -96.427

    # Load Devices located within 50 meters of at least one exclusion zones
    device_N3_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_N3_1['installationParam']['latitude'] = 39.96300
    device_N3_1['installationParam']['longitude'] =  -96.24656
    device_N3_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_N3_2['installationParam']['latitude'] = 39.96317
    device_N3_2['installationParam']['longitude'] =  -96.24692
    device_N3_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_N3_3['installationParam']['latitude'] = 39.96330
    device_N3_3['installationParam']['longitude'] =  -96.24712


    # Forming N1 grant request with overlapping frequency
    grant_N1_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))   
    grant_N1_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N1_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N1_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N1_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N1_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N1_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N1_3['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N1_3['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0

    # Forming N2 grant request 
    grant_N2_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3655000000.0
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3650000000.0
    grant_N2_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3655000000.0
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3650000000.0


    # Forming N3 grant request with overlapping frequency
    grant_N3_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N3_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
    grant_N3_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_N3_3['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000.0
    grant_N3_3['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000.0
 
    grants_N1 = [grant_N1_1, grant_N1_2, grant_N1_3]
    grants_N2 = [grant_N2_1, grant_N2_2]
    grants_N3 = [grant_N3_1, grant_N3_2, grant_N3_3]


    # Create the actual config.
    devices_N1 = [device_N1_1, device_N1_2, device_N1_3]
    devices_N2 = [device_N2_1, device_N2_2]
    devices_N3 = [device_N3_1, device_N3_2, device_N3_3]

    config = {
        'registrationRequests_N1' : devices_N1,
        'registrationRequests_N2' : devices_N2,
        'registrationRequests_N3' : devices_N3,
        'grants_N1' : grants_N1,
        'grants_N2' : grants_N2,
        'grants_N3' : grants_N3
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


    # Register N1 devices
    cbsd_ids_N1 = self.assertRegistered(config['registrationRequests_N1'])

    # Register N2 devices
    cbsd_ids_N2 = self.assertRegistered(config['registrationRequests_N2'])

    # Register N3 devices
    cbsd_ids_N3 = self.assertRegistered(config['registrationRequests_N3'])


    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Generating grant requests for N1 and validating responses
    grant_request = []
    for i in range(len(config['grants_N1'])):
        config['grants_N1'][i]['cbsdId'] = cbsd_ids_N1[i]
        grant_request.append(config['grants_N1'][i])

    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))

    for response_num, resp in enumerate(response):
          self.assertEqual(resp['cbsdId'], cbsd_ids_N1[response_num])
          self.assertTrue('grantId' in resp)
          #self.assertEqual(resp['response']['responseCode'], 400)


    # Generating grant requests for N2 and validating responses
    grant_request = []
    for i in range(len(config['grants_N2'])):
        config['grants_N2'][i]['cbsdId'] = cbsd_ids_N2[i]
        grant_request.append(config['grants_N2'][i])

  
    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))

    for response_num, resp in enumerate(response):
          self.assertEqual(resp['cbsdId'], cbsd_ids_N2[response_num])
          self.assertTrue('grantId' in resp)
          #self.assertEqual(resp['response']['responseCode'], 400)

    # Generating grant requests for N3 and validating responses
    grant_request = []
    for i in range(len(config['grants_N3'])):
        config['grants_N3'][i]['cbsdId'] = cbsd_ids_N3[i]
        grant_request.append(config['grants_N3'][i])


    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))

    for response_num, resp in enumerate(response):
          self.assertEqual(resp['cbsdId'], cbsd_ids_N3[response_num])
          self.assertTrue('grantId' in resp)
          #self.assertEqual(resp['response']['responseCode'], 400)

