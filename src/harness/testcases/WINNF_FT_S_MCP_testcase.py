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

import constraint_testcase
import hashlib
import json
import os
import sas
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generatePpaRecords
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, makePpaAndPalRecordsConsistent 


class MultiConstraintProtectionTestcase(constraint_testcase.ConstraintTestcase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_MCP_1_default_config(self, filename):
    """ Generates the WinnForum configuration for MCP.1. """
    # Load devices for SAS UUT for multiple iterations through multiple domain proxy's
    device_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_5 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_6 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_f.json')))

    # Load Grant requests
    grant_request_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_request_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_1.json')))
    grant_request_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_2.json')))
    grant_request_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_3.json')))
    grant_request_5 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_request_6 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_1.json')))
  
    # device_b is Category B
    # Load Conditional Data
    self.assertEqual(device_2['cbsdCategory'], 'B') 
    conditionals_b = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }
    
    conditionals = {'registrationData': [conditionals_b]}
    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
   
    # Load GWPZ Record
    gwpz_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'gwpz_record_0.json')))

    # Load FSS record
    fss_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))

    # Load ESC record
    esc_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
  
    # Load PPA record
    ppa_record = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_0.json'))) 
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))

    pal_low_frequency = 3550000000.0
    pal_high_frequency = 3560000000.0        

    ppa_record_1, pal_record_1 = makePpaAndPalRecordsConsistent(ppa_record,
                                                                [pal_record],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                'test_user_1')
    # Load DPA record
    dpa_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'dpa_0.json')))
    dpa_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'dpa_1.json')))
    dpa_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'dpa_0.json')))

    # Registration and grant records for multiple iterations
    cbsd_records_iter_1_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2],
        'grantRequests': [grant_request_1, grant_request_2],
        'conditionalRegistrationData': conditionals
    }
    cbsd_records_iter_1_domain_proxy_1 = {
        'registrationRequests': [device_3],
        'grantRequests': [grant_request_3],
        'conditionalRegistrationData': {}
    }
    cbsd_records_iter_2_domain_proxy_0 = {
        'registrationRequests': [device_4],
        'grantRequests': [grant_request_4],
        'conditionalRegistrationData': {}
    }
    cbsd_records_iter_2_domain_proxy_1 = {
        'registrationRequests': [device_5, device_6],
        'grantRequests': [grant_request_5, grant_request_6],
        'conditionalRegistrationData': {}
    }
    
    # Protected entities records for multiple iterations
    protected_entities_iter_1 = {
        'palRecords': [pal_record_1],
        'ppaRecords': [ppa_record_1], 
        'escRecords': [esc_record_1]
    }
    protected_entities_iter_2 = {
        'gwpzRecords': [gwpz_record_1], 
        'fssRecords': [fss_record_1]
    }

    # SAS Test Harnesses configurations, 
    # Following configurations are for two SAS test harnesses for two iterations
    sas_test_harness_device_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    sas_test_harness_device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    sas_test_harness_device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    sas_test_harness_device_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    sas_test_harness_device_5 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_e.json')))
    sas_test_harness_device_6 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_f.json')))

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 0
    cbsd_fad_records_sas_test_harness_0_iteration_0 = generateCbsdRecords([sas_test_harness_device_1], [[grant_request_1]])

    # Generate Cbsd FAD Records for SAS Test Harness 1, iteration 0
    cbsd_fad_records_sas_test_harness_1_iteration_0 = generateCbsdRecords([sas_test_harness_device_4,sas_test_harness_device_5],
                                                                          [[grant_request_2, grant_request_3], [grant_request_4]])

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 1
    cbsd_fad_records_sas_test_harness_0_iteration_1 = generateCbsdRecords([sas_test_harness_device_2,sas_test_harness_device_3],
                                                                          [[grant_request_1],[grant_request_2]])

    # Generate Cbsd FAD Records for SAS Test Harness 1, iteration 1
    cbsd_fad_records_sas_test_harness_1_iteration_1 = generateCbsdRecords([sas_test_harness_device_6], [[grant_request_5, grant_request_6]])
   
    # SAS Test Harnesses configuration  
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': 'localhost',
        'port': 9001,
        'serverCert': "certs/server.cert",
        'serverKey': "certs/server.key",
        'caCert': "certs/ca.cert"
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': 'localhost',
        'port': 9002,
        'serverCert': "certs/server.cert",
        'serverKey': "certs/server.key",
        'caCert': "certs/ca.cert"
    }

    # Generate SAS Test Harnesses dump records for multiple iterations   
    sas_test_harness_0_dump_records_iteration_0 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_0_iteration_0
    }
    sas_test_harness_0_dump_records_iteration_1 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_0_iteration_1
    }
    sas_test_harness_1_dump_records_iteration_0 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_1_iteration_0
    }
    sas_test_harness_1_dump_records_iteration_1 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_1_iteration_1
    }

    # Create the actual config.
    iteration1_config = {
        'cbsdRequests': [cbsd_records_iter_1_domain_proxy_0,cbsd_records_iter_1_domain_proxy_1],
        'protectedEntities': protected_entities_iter_1,
        'dpaActivationList': [dpa_1, dpa_2],
        'dpaDeactivationList': [],
        'sasTestHarnessesData': [sas_test_harness_0_dump_records_iteration_0,sas_test_harness_1_dump_records_iteration_0]
    }
    iteration2_config = {
        'cbsdRequests': [cbsd_records_iter_2_domain_proxy_0,cbsd_records_iter_2_domain_proxy_1],
        'protectedEntities': protected_entities_iter_2,
        'dpaActivationList': [dpa_3],
        'dpaDeactivationList': [dpa_1],
        'sasTestHarnessesData': [sas_test_harness_0_dump_records_iteration_1,sas_test_harness_1_dump_records_iteration_1]
    }
    config = {
        'iterationData': [iteration1_config, iteration2_config],
        'sasTestHarnesses': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': 'dp_1_client.cert', 
                                'key':  'dp_1_client.key'},
                               {'cert': 'dp_2_client.cert',
                                'key':  'dp_2_client.key'}],
        'deltaIap': 2
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_MCP_1_default_config) 
  def test_WINNF_FT_S_MCP_1(self, config_filename):
    """SAS manages a mix of GAA and PAL Grants in 3550 MHz
       to 3700 MHz to protect configurable IAP-protected entities and DPAs
    """
    config = loadConfig(config_filename)
