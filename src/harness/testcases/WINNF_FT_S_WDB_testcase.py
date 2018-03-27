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
from util import configurable_testcase, writeConfig, loadConfig


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

    # Fake database test harness configuration
    fake_database_config = {
        'hostName': 'localhost',
        'port': 9090
    }

    # Load PAL database record
    pal_db_record_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_db_record_0.json')))

    device_b['userId'] = pal_db_record_0['licensee']

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
        'palDbRecord': pal_db_record_0,
        'registrationRequest': device_b,
        'conditionalRegistrationData': conditionals,
        'fakeDatabaseInfo': fake_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_WDB_1_default_config)
  def test_WINNF_FT_S_WDB_1(self, config_filename):
    """PAL Database Update."""

    config = loadConfig(config_filename)

    device_c = config['registrationRequest']

    # Step 1: Register CBSD C to the SAS UUT.
    cbsd_ids = self.assertRegistered([device_c],
                        config['conditionalRegistrationData'])

    # Step 2: Request creation of PPA 
    pal_id = config['palDbRecord']['palId']
    ppa_creation_request = {
            "cbsdIds": cbsd_ids,
            "palIds": [pal_id]
        }
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)

    # Validate PPA creation request is failed.
    self.assertEqual(ppa_id, None)

    # Step 3: Create PAL database with a PAL record containg the PAL ID P.
    # Create fake database server
    fake_database_server = FakeDatabaseTestHarness(
                              config['fakeDatabaseInfo']['hostName'],
                              config['fakeDatabaseInfo']['port'])

    # Write the PAL record into the database file
    fake_database_server.writeDatabaseFile(config['palDbRecord'])

    # Start fake database server
    fake_database_server.start()

    # Inject the fake database URL into SAS UUT
    database_url = fake_database_server.getBaseUrl()
    self._sas_admin.InjectDatabaseUrl(database_url)

    # Step 4: Admin Test Harness triggers CPAS
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Request PPA creation
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)
    self.assertNotEqual(ppa_id, None)

    # As Python garbage collector is not very consistent, the deletion
    # of the fake_database_server object is not immediate and consistent.
    # Hence, explicitly stopping Database Test Harness and cleaning up.
    fake_database_server.shutdown()
    del fake_database_server
