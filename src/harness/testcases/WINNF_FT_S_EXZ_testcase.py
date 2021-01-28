#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
from datetime import datetime

import common_strings
import sas
import sas_testcase
from util import addCbsdIdsToRequests, configurable_testcase, writeConfig, loadConfig, json_load


class ExclusionZoneTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_EXZ_1_default_config(self, filename):
    """Generates the WinnForum configuration for EXZ.1."""
    # Load Exclusion Zones
    exz_record = json_load(
        os.path.join('testcases', 'testdata', 'exz_record_0.json'))
    frequency_ranges = [{'lowFrequency': 3550000000, 'highFrequency': 3600000000},
                        {'lowFrequency': 3600000000, 'highFrequency': 3650000000}
                       ]
    exz_record_1 = {
        'zone': exz_record,
        'frequencyRanges': frequency_ranges
    }

    exz_record = json_load(
        os.path.join('testcases', 'testdata', 'exz_record_1.json'))
    frequency_ranges = [{'lowFrequency': 3650000000, 'highFrequency': 3660000000},
                        {'lowFrequency': 3660000000, 'highFrequency': 3670000000}
                       ]
    exz_record_2 = {
        'zone': exz_record,
        'frequencyRanges': frequency_ranges
    }

    # Load N2 devices info and move them to each located outside 50 meters of exclusion zone exz_record_2
    device_N2_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_N2_1['installationParam']['latitude'] = 42.37477
    device_N2_1['installationParam']['longitude'] = -100.93139
    device_N2_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_N2_2['installationParam']['latitude'] = 42.42548
    device_N2_2['installationParam']['longitude'] = -99.8767

    # Forming N2 grant request with exz_record_2 overlapping frequency
    grant_N2_1 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3650000000
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3660000000
    grant_N2_2 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3660000000
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3670000000

    # Load N3_1 device located within exclusion zone exz_record_1
    device_N3_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_N3_1['installationParam']['latitude'] = 39.66068
    device_N3_1['installationParam']['longitude'] = -96.63024
    device_N3_1['fccId'] = "test_fcc_id_aa"
    device_N3_1['cbsdSerialNumber'] = "test_serial_number_aa"

    # Forming N3_1 grant request with exz_record_1 overlapping frequency
    grant_N3_1 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3550000000
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3560000000

    # Load N3_2 device located within exclusion zone exz_record_2
    device_N3_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_N3_2['installationParam']['latitude'] = 42.65012
    device_N3_2['installationParam']['longitude'] = -100.79956
    device_N3_2['fccId'] = "test_fcc_id_bb"
    device_N3_2['cbsdSerialNumber'] = "test_serial_number_bb"

    # Forming N3_2 grant request with exz_record_2 overlapping frequency
    grant_N3_2 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3650000000
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3660000000

    # Load N4_1 device located within 50 meters of exclusion zone exz_record_1
    device_N4_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_N4_1['installationParam']['latitude'] = 39.91706
    device_N4_1['installationParam']['longitude'] = -96.68082
    device_N4_1['fccId'] = "test_fcc_id_bbb"
    device_N4_1['cbsdSerialNumber'] = "test_serial_number_bbb"

    # Forming N4_1 grant request with exz_record_1 overlapping frequency
    grant_N4_1 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N4_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3550000000
    grant_N4_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3560000000

    # Load N4_2 device located within 50 meters of exclusion zone exz_record_2
    device_N4_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_N4_2['installationParam']['latitude'] = 42.89723
    device_N4_2['installationParam']['longitude'] = -100.74354
    device_N4_2['fccId'] = "test_fcc_id_ccc"
    device_N4_2['cbsdSerialNumber'] = "test_serial_number_ccc"

    # Forming N4_2 grant request with exz_record_2 overlapping frequency
    grant_N4_2 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N4_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3650000000
    grant_N4_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3660000000

    #Creating conditionals for Cat B devices
    self.assertEqual(device_N2_2['cbsdCategory'], 'B')
    conditionalsN2 = {
        'cbsdCategory': device_N2_2['cbsdCategory'],
        'fccId': device_N2_2['fccId'],
        'cbsdSerialNumber': device_N2_2['cbsdSerialNumber'],
        'airInterface': device_N2_2['airInterface'],
        'installationParam': device_N2_2['installationParam'],
        'measCapability': device_N2_2['measCapability']
    }
    del device_N2_2['cbsdCategory']
    del device_N2_2['airInterface']
    del device_N2_2['installationParam']
    del device_N2_2['measCapability']

    self.assertEqual(device_N3_2['cbsdCategory'], 'B')
    conditionalsN3 = {
        'cbsdCategory': device_N3_2['cbsdCategory'],
        'fccId': device_N3_2['fccId'],
        'cbsdSerialNumber': device_N3_2['cbsdSerialNumber'],
        'airInterface': device_N3_2['airInterface'],
        'installationParam': device_N3_2['installationParam'],
        'measCapability': device_N3_2['measCapability']
    }
    del device_N3_2['cbsdCategory']
    del device_N3_2['airInterface']
    del device_N3_2['installationParam']
    del device_N3_2['measCapability']

    self.assertEqual(device_N4_1['cbsdCategory'], 'B')
    conditionalsN4 = {
        'cbsdCategory': device_N4_1['cbsdCategory'],
        'fccId': device_N4_1['fccId'],
        'cbsdSerialNumber': device_N4_1['cbsdSerialNumber'],
        'airInterface': device_N4_1['airInterface'],
        'installationParam': device_N4_1['installationParam'],
        'measCapability': device_N4_1['measCapability']
    }
    del device_N4_1['cbsdCategory']
    del device_N4_1['airInterface']
    del device_N4_1['installationParam']
    del device_N4_1['measCapability']

    # Create the actual config.
    grants_N2 = [grant_N2_1, grant_N2_2]
    grants_N3 = [grant_N3_1, grant_N3_2]
    grants_N4 = [grant_N4_1, grant_N4_2]

    devices_N2 = [device_N2_1, device_N2_2]
    devices_N3 = [device_N3_1, device_N3_2]
    devices_N4 = [device_N4_1, device_N4_2]

    conditionals = [conditionalsN2, conditionalsN3, conditionalsN4]

    config = {
        'registrationRequestsN2' : devices_N2,
        'registrationRequestsN3' : devices_N3,
        'registrationRequestsN4' : devices_N4,
        'exclusionZoneRecords' : [exz_record_1, exz_record_2],
        'grantRequestsN2' : grants_N2,
        'grantRequestsN3' : grants_N3,
        'grantRequestsN4' : grants_N4,
        'conditionalRegistrationData': conditionals
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_EXZ_1_default_config)
  def test_WINNF_FT_S_EXZ_1(self,config_filename):
    """Injected Exclusion Zones

    The responseCode = 400 for CBSDs located within 50meters of all Exclusion Zones
    or inside Exclusion Zones.
    """
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequestsN2': list,
            'registrationRequestsN3': list,
            'registrationRequestsN4': list,
            'exclusionZoneRecords': list,
            'grantRequestsN2': list,
            'grantRequestsN3': list,
            'grantRequestsN4': list,
            'conditionalRegistrationData': list
        })
    self.assertGreater(len(config['exclusionZoneRecords']) , 0)
    self.assertEqual(len(config['registrationRequestsN2']),len(config['grantRequestsN2']))
    self.assertEqual(len(config['registrationRequestsN3']),len(config['grantRequestsN3']))
    self.assertEqual(len(config['registrationRequestsN4']),len(config['grantRequestsN4']))

    # Inject EXZ database records
    for exclusion_zone in config['exclusionZoneRecords']:
      self._sas_admin.InjectExclusionZone(exclusion_zone)

    # Pre-load conditional registration data for N2,N3 and N4 CBSDs.
    if config['conditionalRegistrationData']:
      for data in config['conditionalRegistrationData']:
        self._sas_admin.InjectFccId({'fccId': data['fccId']})
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    try:
      # Register N2 devices
      cbsd_ids_N2 = self.assertRegistered(config['registrationRequestsN2'])

      # Register N3 devices
      cbsd_ids_N3 = self.assertRegistered(config['registrationRequestsN3'])

      # Register N4 devices
      cbsd_ids_N4 = self.assertRegistered(config['registrationRequestsN4'])
    except Exception as e:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)

    # Execute CPAS and wait untill completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Sending grant requests for N2 and validating the response code is 0
    grant_request_N2 = []
    for index,grants in enumerate(config['grantRequestsN2']):
      grants['cbsdId'] = cbsd_ids_N2[index]
      grant_request_N2.append(grants)

    request_N2 = {'grantRequest': grant_request_N2}
    response_N2 = self._sas.Grant(request_N2)['grantResponse']
    self.assertEqual(len(response_N2), len(grant_request_N2))

    for response_num, response in enumerate(response_N2):
      logging.info('Looking at Grant response number %d', response_num)
      logging.info('Expecting to see response code 0 in Grant response: %s',
                   response)
      self.assertEqual(response['cbsdId'], request_N2['grantRequest'][response_num]['cbsdId'])
      self.assertTrue('grantId' in response)
      self.assertEqual(response['response']['responseCode'], 0)

    # Sending grant requests for N3 and validating the response code is 400
    grant_request_N3 = []
    for index,grants in enumerate(config['grantRequestsN3']):
      grants['cbsdId'] = cbsd_ids_N3[index]
      grant_request_N3.append(grants)

    request_N3 = {'grantRequest': grant_request_N3}
    response_N3 = self._sas.Grant(request_N3)['grantResponse']
    self.assertEqual(len(response_N3), len(grant_request_N3))

    for response_num, response in enumerate(response_N3):
      logging.info('Looking at Grant response number %d', response_num)
      logging.info('Expecting to see response code 400 in Grant response: %s',
                   response)
      self.assertEqual(response['cbsdId'], request_N3['grantRequest'][response_num]['cbsdId'])
      self.assertFalse('grantId' in response)
      self.assertEqual(response['response']['responseCode'], 400)

    # Sending grant requests for N4 and validating the response code is 400
    grant_request_N4 = []
    for index,grants in enumerate(config['grantRequestsN4']):
      grants['cbsdId'] = cbsd_ids_N4[index]
      grant_request_N4.append(grants)

    request_N4 = {'grantRequest': grant_request_N4}
    response_N4 = self._sas.Grant(request_N4)['grantResponse']
    self.assertEqual(len(response_N4), len(grant_request_N4))

    for response_num, response in enumerate(response_N4):
      logging.info('Looking at Grant response number %d', response_num)
      logging.info('Expecting to see response code 400 in Grant response: %s',
                   response)
      self.assertEqual(response['cbsdId'], request_N4['grantRequest'][response_num]['cbsdId'])
      self.assertFalse('grantId' in response)
      self.assertEqual(response['response']['responseCode'], 400)

  def generate_EXZ_2_default_config(self, filename):
    """Generates the WinnForum configuration for EXZ.2."""

    # Loading N1 set of CBSDs each located outside 50 meters of all Exclusion Zones
    device_N1_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    # Moving device_N1_1 just outside of 50 meters from exclusion zone of
    # 'East-Gulf Combined Contour'
    device_N1_1['installationParam']['latitude'] = 40.31260
    device_N1_1['installationParam']['longitude'] = -96.25100

    device_N1_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    # Moving device_N1_2 just outside of 50 meters from exclusion zone of
    # 'West Combined Contour'
    device_N1_2['installationParam']['latitude'] = 33.58101 
    device_N1_2['installationParam']['longitude'] = -114.35775 

    device_N1_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    # Moving device_N1_3 just outside of 50 meters from exclusion zone of
    # 'West Combined Contour'
    device_N1_3['installationParam']['latitude'] = 33.85263
    device_N1_3['installationParam']['longitude'] = -106.57198

    # Loading N2 set of CBSDs each located within at least one Exclusion Zone
    device_N2_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    # Moving device_N2_1 to a location inside the exclusion zone of
    # 'West Combined Contour'
    device_N2_1['installationParam']['latitude'] = 37.26531 
    device_N2_1['installationParam']['longitude'] = -121.89331
    device_N2_1['fccId'] = "test_fcc_id_bb"
    device_N2_1['cbsdSerialNumber'] = "test_serial_number_bb"

    device_N2_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    # Moving device_N2_2 to a location inside the exclusion zone of
    # 'East-Gulf Combined Contour'
    device_N2_2['installationParam']['latitude'] = 30.69461
    device_N2_2['installationParam']['longitude'] = -89.82421 
    device_N2_2['fccId'] = "test_fcc_id_cc"
    device_N2_2['cbsdSerialNumber'] = "test_serial_number_cc"

    # Loading N3 set of CBSDs each located within 50 meters of at least one Exclusion Zone
    device_N3_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    # Moving device_N3_1 to a location within 50 meters from the exclusion zone
    # of 'East-Gulf Combined Contour'
    device_N3_1['installationParam']['latitude'] = 43.936508
    device_N3_1['installationParam']['longitude'] = -71.098682 
    device_N3_1['fccId'] = "test_fcc_id_aaa"
    device_N3_1['cbsdSerialNumber'] = "test_serial_number_aaa"

    device_N3_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    # Moving device_N3_2 to a location within 50 meters from the exclusion zone
    # of 'West Combined Contour'
    device_N3_2['installationParam']['latitude'] = 47.34734
    device_N3_2['installationParam']['longitude'] = -124.15241
    device_N3_2['fccId'] = "test_fcc_id_bbb"
    device_N3_2['cbsdSerialNumber'] = "test_serial_number_bbb"

    device_N3_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    # Moving device_N3_3 to a location within 50 meters from the exclusion zone
    # of 'East-Gulf Combined Contour'
    device_N3_3['installationParam']['latitude'] = 39.489834
    device_N3_3['installationParam']['longitude'] = -77.129077
    device_N3_3['fccId'] = "test_fcc_id_ccc"
    device_N3_3['cbsdSerialNumber'] = "test_serial_number_ccc"

    # Forming N1 grant request with overlapping frequency
    grant_N1_1 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N1_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000
    grant_N1_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000
    grant_N1_2 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N1_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000
    grant_N1_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000
    grant_N1_3 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N1_3['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000
    grant_N1_3['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000

    # Forming N2 grant request
    grant_N2_1 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3550000000
    grant_N2_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3555000000
    grant_N2_2 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3550000000
    grant_N2_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3555000000

    # Forming N3 grant request with overlapping frequency
    grant_N3_1 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000
    grant_N3_1['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000
    grant_N3_2 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000
    grant_N3_2['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000
    grant_N3_3 = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_N3_3['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3645000000
    grant_N3_3['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3655000000

    # Creating conditionals for Cat B devices
    self.assertEqual(device_N1_2['cbsdCategory'], 'B')
    conditionals_N1 = {
        'cbsdCategory': device_N1_2['cbsdCategory'],
        'fccId': device_N1_2['fccId'],
        'cbsdSerialNumber': device_N1_2['cbsdSerialNumber'],
        'airInterface': device_N1_2['airInterface'],
        'installationParam': device_N1_2['installationParam'],
        'measCapability': device_N1_2['measCapability']
    }
    del device_N1_2['cbsdCategory']
    del device_N1_2['airInterface']
    del device_N1_2['installationParam']
    del device_N1_2['measCapability']

    self.assertEqual(device_N2_1['cbsdCategory'], 'B')
    conditionals_N2 = {
        'cbsdCategory': device_N2_1['cbsdCategory'],
        'fccId': device_N2_1['fccId'],
        'cbsdSerialNumber': device_N2_1['cbsdSerialNumber'],
        'airInterface': device_N2_1['airInterface'],
        'installationParam': device_N2_1['installationParam'],
        'measCapability': device_N2_1['measCapability']
    }
    del device_N2_1['cbsdCategory']
    del device_N2_1['airInterface']
    del device_N2_1['installationParam']
    del device_N2_1['measCapability']

    self.assertEqual(device_N3_2['cbsdCategory'], 'B')
    conditionals_N3 = {
        'cbsdCategory': device_N3_2['cbsdCategory'],
        'fccId': device_N3_2['fccId'],
        'cbsdSerialNumber': device_N3_2['cbsdSerialNumber'],
        'airInterface': device_N3_2['airInterface'],
        'installationParam': device_N3_2['installationParam'],
        'measCapability': device_N3_2['measCapability']
    }
    del device_N3_2['cbsdCategory']
    del device_N3_2['airInterface']
    del device_N3_2['installationParam']
    del device_N3_2['measCapability']

    # Create the actual config.
    grants_N1 = [grant_N1_1, grant_N1_2, grant_N1_3]
    grants_N2 = [grant_N2_1, grant_N2_2]
    grants_N3 = [grant_N3_1, grant_N3_2, grant_N3_3]

    devices_N1 = [device_N1_1, device_N1_2, device_N1_3]
    devices_N2 = [device_N2_1, device_N2_2]
    devices_N3 = [device_N3_1, device_N3_2, device_N3_3]

    config = {
        'registrationRequestsN1': devices_N1,
        'registrationRequestsN2': devices_N2,
        'registrationRequestsN3': devices_N3,
        'grantRequestsN1': grants_N1,
        'grantRequestsN2': grants_N2,
        'grantRequestsN3': grants_N3,
        'conditionalRegistrationDataN1': [conditionals_N1],
        'conditionalRegistrationDataN2': [conditionals_N2],
        'conditionalRegistrationDataN3': [conditionals_N3]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_EXZ_2_default_config)
  def test_WINNF_FT_S_EXZ_2(self, config_filename):
    """Exclusion Zones defined in NTIA TR 15-517

    The responseCode = 400 for CBSDs located within 50meters of all Exclusion Zones
    or inside Exclusion Zones.
    """

    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequestsN1']), len(config['grantRequestsN1']))
    self.assertEqual(len(config['registrationRequestsN2']), len(config['grantRequestsN2']))
    self.assertEqual(len(config['registrationRequestsN3']), len(config['grantRequestsN3']))

    # Enforce NTIA Exlusion zones
    self._sas_admin.TriggerEnableNtiaExclusionZones()

    try:
      # Register N1 devices
      cbsd_ids_N1 = self.assertRegistered(config['registrationRequestsN1'], config['conditionalRegistrationDataN1'])

      # Register N2 devices
      cbsd_ids_N2 = self.assertRegistered(config['registrationRequestsN2'], config['conditionalRegistrationDataN2'])

      # Register N3 devices
      cbsd_ids_N3 = self.assertRegistered(config['registrationRequestsN3'], config['conditionalRegistrationDataN3'])
    except Exception as e:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Generating grant requests for N1 and validating responses
    grant_request_N1 = config['grantRequestsN1']
    addCbsdIdsToRequests(cbsd_ids_N1, grant_request_N1)

    request_N1 = {'grantRequest': grant_request_N1}
    response_N1 = self._sas.Grant(request_N1)['grantResponse']
    self.assertEqual(len(response_N1), len(grant_request_N1))

    # Generating grant requests for N2 and validating responses
    # Request grant
    grant_request_N2 = config['grantRequestsN2']
    addCbsdIdsToRequests(cbsd_ids_N2, grant_request_N2)

    request_N2 = {'grantRequest': grant_request_N2}
    response_N2 = self._sas.Grant(request_N2)['grantResponse']
    self.assertEqual(len(response_N2), len(grant_request_N2))

    for response_num, response in enumerate(response_N2):
      self.assertEqual(response['cbsdId'], request_N2['grantRequest'][response_num]['cbsdId'])
      self.assertFalse('grantId' in response)
      self.assertEqual(response['response']['responseCode'], 400)

    # Generating grant requests for N3 and validating responses
    grant_request_N3 = config['grantRequestsN3']
    addCbsdIdsToRequests(cbsd_ids_N3, grant_request_N3)

    request_N3 = {'grantRequest': grant_request_N3}
    response_N3 = self._sas.Grant(request_N3)['grantResponse']
    self.assertEqual(len(response_N3), len(grant_request_N3))

    for response_num, response in enumerate(response_N3):
      self.assertEqual(response['cbsdId'], request_N3['grantRequest'][response_num]['cbsdId'])
      self.assertFalse('grantId' in response)
      self.assertEqual(response['response']['responseCode'], 400)

