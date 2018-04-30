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

import json
import logging
import os
import sas
import sas_testcase
from util import configurable_testcase, writeConfig, loadConfig,\
    convertRequestToRequestWithCpiSignature, makePalRecordsConsistent


class WinnforumDatabaseUpdateTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_WDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for WDB.1"""

    # Load devices info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load PAL records
    pal_record_a_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record_a_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    pal_record_b_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_2.json')))
    
    # FIPS codes of adjacent census tracts
    pal_record_a_0['fipsCode'] = 20063955100
    pal_record_a_1['fipsCode'] = 20063955200

    pal_record_b_0['fipsCode'] = 20195955800

    # Set the PAL frequency.
    pal_low_frequency = 3570000000
    pal_high_frequency = 3580000000

    # Setting the frequency range and user ID(s) 'U' for PAL records.
    pal_records_a = makePalRecordsConsistent([pal_record_a_0, pal_record_a_1],
                                             pal_low_frequency, pal_high_frequency,
                                             device_a['userId'])
    pal_records_b = makePalRecordsConsistent([pal_record_b_0],
                                             pal_low_frequency, pal_high_frequency,
                                             device_b['userId'])

    # Set the locations of devices to reside with in census tracts.
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = 39.0373, -100.4184
    device_b['installationParam']['latitude'], device_b['installationParam'][
        'longitude'] = 38.9583, -99.9055

    # Getting PAL IDs from pal records
    pal_ids_a = [pal_records_a[0]['palId'], pal_records_a[1]['palId']]
    pal_ids_b = [pal_records_b[0]['palId']]

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']
    del device_b['measCapability']

    conditionals = [conditionals_b]

    # Create the actual config file
    config = {
        'palIds': [pal_ids_a, pal_ids_b],
        'registrationRequests': [device_a, device_b],
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations.
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_WDB_1_default_config)
  def test_WINNF_FT_S_WDB_1(self, config_filename):
    """PAL Database Update."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequests']), len(config['palIds']))

    # Step 1: Register device(s) 'C' with conditional registration data
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # Step 2: Request creation of PPA(s).
    # Forming of PPA creation request(s)
    ppa_creation_requests = []
    for cbsd_id, pal_ids in zip(cbsd_ids, config['palIds']):
      ppa_creation_requests.append({
        "cbsdIds": [cbsd_id],
        "palIds": pal_ids
      })

    # Trigger PPA creation
    for ppa_creation_request in ppa_creation_requests:
      self.assertPpaCreationFailure(ppa_creation_request)

    # TODO
    # Step 3: Create PAL database with a PAL record containg the PAL ID 'P'.

    # Step 4: Admin Test Harness triggers CPAS
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 5: Request creation of PPA(s) again
    for ppa_creation_request in ppa_creation_requests:
      ppa_id = self.triggerPpaCreationAndWaitUntilComplete(ppa_creation_request)
      logging.debug('ppa_id received from SAS UUT:%s', ppa_id)

  def generate_WDB_2_default_config(self, filename):
    """Generates the WinnForum configuration for WDB.2"""

    # Load category B devices info
    device_b = json.load(
         open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_d = json.load(
         open(os.path.join('testcases', 'testdata', 'device_d.json')))

    # Device_b and Device_d are of Category B
    self.assertEqual(device_b['cbsdCategory'], 'B')
    self.assertEqual(device_d['cbsdCategory'], 'B')

    # Load CPI users info
    cpi_id_b = 'professional_installer_id_1'
    cpi_name_b = 'b_name'
    cpi_id_d = 'professional_installer_id_2'
    cpi_name_d = 'd_name'

    # Read private keys for the CPI users
    with open(os.path.join('testcases', 'testdata', 'wdb_2', 'WDB_2_CPI_Private_Key.txt'),
              'r') as file_handle:
      cpi_private_key_b = file_handle.read()

    with open(os.path.join('testcases', 'testdata', 'wdb_2', 'WDB_2_CPI_Private_Key.txt'),
              'r') as file_handle:
      cpi_private_key_d = file_handle.read()

    # Convert CBSDs registration requests to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key_b, cpi_id_b,
                                            cpi_name_b, device_b)
    convertRequestToRequestWithCpiSignature(cpi_private_key_d, cpi_id_d,
                                            cpi_name_d, device_d)

    # Create the actual config.
    config = {
      'registrationRequests': [device_b, device_d]
      # TODO
      # Need to add data base configurations.
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_WDB_2_default_config)
  def test_WINNF_FT_S_WDB_2(self, config_filename):
    """CPI database update."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertGreater(len(config['registrationRequests']), 0)

    registration_requests = {
        'registrationRequest': config['registrationRequests']
    }

    # Step 1: Register device B and ensure failure
    # Inject FCC ID and User Id of the device(s) into UUT.
    for registration_request in config['registrationRequests']:
      self._sas_admin.InjectFccId({'fccId': registration_request['fccId']})
      self._sas_admin.InjectUserId({'userId': registration_request['userId']})

    # Send registration requests.
    registration_responses = self._sas.Registration(registration_requests)['registrationResponse']

    # Check registeration response,
    # responseCode should be 103 (INVALID_VALUE).
    for registration_response in registration_responses:
      self.assertEqual(registration_response['response']['responseCode'], 103)

    del registration_responses

    # TODO
    # Step 2: Create a CPI database which includes CPI user with credentials
    # matching those used to create the request in Step 1.

    # Step 3: Trigger daily activities.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Register the same device and ensure SUCCESS
    registration_responses = self._sas.Registration(registration_requests)['registrationResponse']

    # Check registeration response,
    # responseCode should be 0 (SUCCESS).
    for registration_response in registration_responses:
      self.assertEqual(registration_response['response']['responseCode'], 0)
