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
import os
import sas
import sas_testcase
from datetime import datetime
from fake_db_server import FakeDatabaseTestHarness
from util import configurable_testcase, writeConfig, loadConfig,\
    convertRequestToRequestWithCpiSignature


class WinnfDatabaseUpdateTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_WDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for WDB.1"""

    # Load device info
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load PAL database record
    pal_record_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))

    # Fake database test harness configuration
    # The databaseFile WDB_1_PAL_Database.csv is populated with PAL record 
    # details of pal_record_0
    fake_pal_database_config = {
        'hostName': 'localhost',
        'port': 9090,
        'databaseFile': os.path.join('testcases', 'testdata', 'wdb_1', 'WDB_1_PAL_Database.csv')
    }

    # Setting the user ID of the of the CBSD to be the same as PAL ID owner.
    device_b['userId'] = pal_record_0['licensee']

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
        'palRecord': pal_record_0,
        'registrationRequest': device_b,
        'conditionalRegistrationData': conditionals,
        'fakePalDatabaseInfo': fake_pal_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_WDB_1_default_config)
  def test_WINNF_FT_S_WDB_1(self, config_filename):
    """PAL Database Update."""

    config = loadConfig(config_filename)

    # Step 1: Register CBSD C to the SAS UUT.
    cbsd_ids = self.assertRegistered([config['registrationRequest']],
                        config['conditionalRegistrationData'])

    # Step 2: Request creation of PPA 
    pal_id = config['palRecord']['palId']
    ppa_creation_request = {
            "cbsdIds": cbsd_ids,
            "palIds": [pal_id]
        }
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)

    # Validate PPA creation request is failed.
    self.assertEqual(ppa_id, None)

    # Step 3: Create PAL database with a PAL record containg the PAL ID P.
    # Create fake PAL database server
    fake_pal_database_server = FakeDatabaseTestHarness(
                              config['fakePalDatabaseInfo']['databaseFile'],
                              config['fakePalDatabaseInfo']['hostName'],
                              config['fakePalDatabaseInfo']['port'])

    # Start fake PAL database server
    fake_pal_database_server.start()

    # Inject the fake database URL into SAS UUT
    database_url = fake_pal_database_server.getBaseUrl()
    self._sas_admin.InjectDatabaseUrl(database_url)

    # Step 4: Admin Test Harness triggers CPAS
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Request PPA creation
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)
    self.assertNotEqual(ppa_id, None)

    # As Python garbage collector is not very consistent, the deletion
    # of the fake_pal_database_server object is not immediate and consistent.
    # Hence, explicitly stopping Database Test Harness and cleaning up.
    fake_pal_database_server.shutdown()
    del fake_pal_database_server
  
  def generate_WDB_2_default_config(self, filename):
    """Generates the WinnForum configuration for WDB.2"""

    # Load category B device info
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load CPI user info
    cpi_id = 'professional_installer_id_1'
    cpi_name = 'a_name'
    # Read private key for the CPI user
    with open(os.path.join('testcases', 'testdata', 'wdb_2', 'WDB_2_CPI_Private_Key.txt'), 
          'r') as file_handle:
      cpi_private_key = file_handle.read()

    # Convert device_b's registration request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_b)

    # Fake CPI database test harness configuration.
    # The CPI database file WDB_2_CPI_Database.csv has one CPI information for the above CPI
    # user and the public key mentioned in the csv file corresponds to the cpi_private_key.
    fake_cpi_database_config = {
        'hostName': 'localhost',
        'port': 9090,
        'databaseFile': os.path.join('testcases', 'testdata', 'wdb_2', 'WDB_2_CPI_Database.csv')
    }

    # Create the actual config.
    config = {
      'registrationRequest': device_b,
      'fakeDatabaseInfo': fake_cpi_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_WDB_2_default_config)
  def test_WINNF_FT_S_WDB_2(self, config_filename):
    """CPI database update."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Step 1: Register device B and ensure failure
    request = {'registrationRequest': config['registrationRequest']}
    response = self._sas.Registration(request)['registrationResponse']

    # Check the register response code is 103 (INVALID_VALUE).
    self.assertEqual(response['response']['responseCode'], 103)

    # Step 2: Create a CPI database which includes CPI user with credentials
    # matching those used to create the request in Step 1.
    fake_cpi_database_server = FakeDatabaseTestHarness(
        config['fakeDatabaseInfo']['databaseFile'],
        config['fakeDatabaseInfo']['hostName'],
        config['fakeDatabaseInfo']['port'])

    # Start fake GWBL database server.
    fake_cpi_database_server.start()

    # Inject the fake database URL into SAS UUT
    database_url = fake_cpi_database_server.getBaseUrl()
    self._sas_admin.InjectDatabaseUrl(database_url)

    # Step 3: Trigger daily activities.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Register the same device and ensure SUCCESS
    request = {'registrationRequest': config['registrationRequest']}
    response = self._sas.Registration(request)['registrationResponse']

    # Check the register response code is 0 (SUCCESS).
    self.assertEqual(response['response']['responseCode'], 0)

    # As Python garbage collector is not very consistent,
    # explicitly stopping database test harnesses and cleaning up.
    fake_cpi_database_server.shutdown()
    del fake_cpi_database_server	
