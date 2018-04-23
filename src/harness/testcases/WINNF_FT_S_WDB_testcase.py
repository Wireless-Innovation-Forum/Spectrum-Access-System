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
import signal
import time
from datetime import datetime
from util import configurable_testcase, writeConfig, loadConfig,\
    convertRequestToRequestWithCpiSignature, makePalRecordsConsistent


class WinnfDatabaseUpdateTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def triggerPpaCreationAndWaitUntilComplete(self, ppa_creation_request):
    """Triggers PPA Creation Admin API and returns PPA ID if the creation status is completed.

    Triggers PPA creation to the SAS UUT. Checks the status of the PPA creation
    by invoking the PPA creation status API. If the status is complete then the
    PPA ID is returned. The status is checked every 10 secs for upto 2 hours.
    Exception is raised if the PPA creation returns error or times out.

    Args:
      ppa_creation_request: A dictionary with a multiple key-value pair containing the
        "cbsdIds", "palIds" and optional "providedContour"(a GeoJSON object).

    Returns:
      A Return value is string format of the PPA ID.

    """
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)

    # Verify ppa_id should not be None.
    self.assertIsNotNone(ppa_id, msg="PPA ID received from SAS UUT as result of "
                                     "PPA Creation is None")

    logging.info('TriggerPpaCreation is in progress')

    # Triggers most recent PPA Creation Status immediately and checks for the
    # status of activity every 10 seconds until it is completed. If the status
    # is not changed within 2 hours it will throw an exception.
    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                  (_ for _ in ()).throw(
                      Exception('Most Recent PPA Creation Status Check Timeout')))

    # Timeout after 2 hours if it's not completed.
    signal.alarm(7200)

    # Check the Status of most recent ppa creation every 10 seconds.
    while not self._sas_admin.GetPpaCreationStatus()['completed']:
      time.sleep(10)

    # Additional check to ensure whether PPA creation status has error.
    self.assertFalse(self._sas_admin.GetPpaCreationStatus()['withError'],
                     msg='There was an error while creating PPA')
    signal.alarm(0)

    return ppa_id

  def assertPpaCreationFailure(self, ppa_creation_request):
    """Trigger PPA Creation Admin API and asserts the failure response.

    Triggers PPA creation to the SAS UUT and handles exception received if the
    PPA creation returns error or times out.Checks the status of the PPA creation
    by invoking the PPA creation status API.If the status is complete then looks for
    withError set to True to declare ppa creation is failed. The status is checked
    every 10 secs for up to 2 hours.

    Args:
      ppa_creation_request: A dictionary with a multiple key-value pair containing the
        "cbsdIds", "palIds" and optional "providedContour"(a GeoJSON object).

    Raises:
      Exception for the following cases:
         a. withError flag set to False even though most recent ppa creation
         status is completed.
         b. SAS UUT does not respond for longer time and timeout.
         c. SAS UUT responds with success response rather than failure response.

    """
    response = self._sas_admin.TriggerPpaCreation(ppa_creation_request)
    logging.info('TriggerPpaCreation is in progress')

    # Triggers most recent PPA Creation Status immediately and checks for the status
    # of activity every 10 seconds until it is completed. If the status is not changed
    # within 2 hours it will throw an exception.
    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                  (_ for _ in ()).throw(
                      Exception('Most Recent PPA Creation Status Check Timeout')))

    # Timeout after 2 hours if it's not completed.
    signal.alarm(7200)

    # Check the Status of most recent ppa creation every 10 seconds.
    while not self._sas_admin.GetPpaCreationStatus()['completed']:
      time.sleep(10)

    # Expect the withError flag in status response should be toggled on to True
    # to indicate PPA creation failure.
    self.assertTrue(self._sas_admin.GetPpaCreationStatus()['withError'],
                    msg='Expected:There is an error in create PPA. But '
                        'PPA creation status indicates no error')
    signal.alarm(0)

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
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record_b_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))

    # Set the PAL frequency.
    pal_low_frequency = 3570000000
    pal_high_frequency = 3580000000

    # Setting the frequency range and user ID(s) 'U' for PAL records.
    pal_records_a = makePalRecordsConsistent([pal_record_a_0, pal_record_a_1],
                                             pal_low_frequency, pal_high_frequency,
                                             device_a['userId'])
    pal_records_b = makePalRecordsConsistent([pal_record_b_0, pal_record_b_1],
                                             pal_low_frequency, pal_high_frequency,
                                             device_b['userId'])

    # Getting PAL IDs from pal records
    pal_ids_a = [pal_records_a[0]['palId'], pal_records_a[1]['palId']]
    pal_ids_b = [pal_records_b[0]['palId'], pal_records_b[1]['palId']]

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

    # Step 1: Register device(s) 'C' with conditional registration data
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # Step 2: Request creation of PPA(s).
    # Forming of PPA creation request(s)
    ppa_creation_requests = []
    for pal_ids in config['palIds']:
      ppa_creation_requests.append({
        "cbsdIds": cbsd_ids,
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
    ppa_ids = []
    for ppa_creation_request in ppa_creation_requests:
      ppa_id = self.triggerPpaCreationAndWaitUntilComplete(ppa_creation_request)
      logging.debug('ppa_id received from SAS UUT:%s', ppa_id)
      ppa_ids.append(ppa_id)

    del ppa_ids

  def generate_WDB_2_default_config(self, filename):
    """Generates the WinnForum configuration for WDB.2"""

    # Load category B devices info
    device_b_0 = json.load(
         open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b_1 = json.load(
         open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Device_b_0 and Device_b_1 are of Category B
    self.assertEqual(device_b_0['cbsdCategory'], 'B')
    self.assertEqual(device_b_1['cbsdCategory'], 'B')

    # Load CPI users info
    cpi_id_b_0 = 'professional_installer_id_1'
    cpi_name_b_0 = 'b1_name'
    cpi_id_b_1 = 'professional_installer_id_2'
    cpi_name_b_1 = 'b2_name'

    # Read private keys for the CPI users
    with open(os.path.join('testcases', 'testdata', 'wdb_2', 'WDB_2_CPI_Private_Key.txt'),
              'r') as file_handle:
      cpi_private_key_b_0 = file_handle.read()

    with open(os.path.join('testcases', 'testdata', 'wdb_2', 'WDB_2_CPI_Private_Key.txt'),
              'r') as file_handle:
      cpi_private_key_b_1 = file_handle.read()

    # Convert CBSDs registration requests to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key_b_0, cpi_id_b_0,
                                            cpi_name_b_0, device_b_0)
    convertRequestToRequestWithCpiSignature(cpi_private_key_b_1, cpi_id_b_1,
                                            cpi_name_b_1, device_b_1)

    # Create the actual config.
    config = {
      'registrationRequests': [device_b_0, device_b_1]
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
    self.assertNotEqual(config['registrationRequests'], None)

    registration_requests = {
        'registrationRequest': config['registrationRequests']
    }

    # Step 1: Register device B and ensure failure
    # Inject FCC ID and User Id of the device(s) into UUT.
    for registration_request in config['registrationRequests']:
      self._sas_admin.InjectFccId({'fccId': registration_request['fccId']})
      self._sas_admin.InjectUserId({'userId': registration_request['userId']})

    # Send registration request for CAT 'B' CBSD 'C' to SAS UUT.
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

    del registration_requests, registration_responses
