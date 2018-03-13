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

import hashlib
import json
import os
import sas
import sas_testcase
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generatePpaRecords
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, makePpaAndPalRecordsConsistent 

class MultiConstraintProtectionTestcase(sas_testcase.SasTestCase):

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

    ppa_record_1, pal_records_1 = makePpaAndPalRecordsConsistent(ppa_record,
                                                                [pal_record],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                'test_user_1')
    # Define DPA's 
    dpa_1 = {
       'dpaId': 'dpa_east_4',
       'frequencyRange': {'lowFrequency': 3650000000 , 'highFrequency': 3660000000 }
    }
    dpa_2 = {
       'dpaId': 'dpa_east_5',
       'frequencyRange': {'lowFrequency': 3660000000 , 'highFrequency': 3670000000 }
    }
    dpa_3 = {
       'dpaId': 'dpa_east_6',
       'frequencyRange': {'lowFrequency': 3670000000 , 'highFrequency': 3680000000 }
    }

    # Registration and grant records for multiple iterations
    cbsd_records_iteration_0_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2],
        'grantRequests': [grant_request_1, grant_request_2]
    }
    cbsd_records_iteration_0_domain_proxy_1 = {
        'registrationRequests': [device_3],
        'grantRequests': [grant_request_3]
    }
    cbsd_records_iteration_1_domain_proxy_0 = {
        'registrationRequests': [device_4],
        'grantRequests': [grant_request_4]
    }
    cbsd_records_iteration_1_domain_proxy_1 = {
        'registrationRequests': [device_5, device_6],
        'grantRequests': [grant_request_5, grant_request_6]
    }
    
    # Protected entities records for multiple iterations
    protected_entities_iteration_0 = {
        'palRecords': pal_records_1,
        'ppaRecords': ppa_record_1, 
        'escRecords': [esc_record_1]
    }
    protected_entities_iteration_1 = {
        'gwpzRecords': [gwpz_record_1], 
        'fssRecords': [fss_record_1]
    }

    # SAS Test Harnesses configurations, 
    # Following configurations are for two SAS test harnesses for two iterations
    sas_test_harness_device_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    sas_test_harness_device_1['fccId'] = "test_fcc_id_g"
    sas_test_harness_device_1['userId'] =  "test_user_id_g"

    sas_test_harness_device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    sas_test_harness_device_2['fccId'] = "test_fcc_id_h"
    sas_test_harness_device_2['userId'] =  "test_user_id_h"

    sas_test_harness_device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    sas_test_harness_device_3['fccId'] = "test_fcc_id_i"
    sas_test_harness_device_3['userId'] =  "test_user_id_i"

    sas_test_harness_device_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    sas_test_harness_device_4['fccId'] = "test_fcc_id_j"
    sas_test_harness_device_4['userId'] =  "test_user_id_j"

    sas_test_harness_device_5 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_e.json')))
    sas_test_harness_device_5['fccId'] = "test_fcc_id_k"
    sas_test_harness_device_5['userId'] =  "test_user_id_k"

    sas_test_harness_device_6 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_f.json')))
    sas_test_harness_device_6['fccId'] = "test_fcc_id_l"
    sas_test_harness_device_6['userId'] =  "test_user_id_l"

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_0 = generateCbsdRecords([sas_test_harness_device_1], [[grant_request_1]])

    # Generate Cbsd FAD Records for SAS Test Harness 1, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_1 = generateCbsdRecords([sas_test_harness_device_4,sas_test_harness_device_5],
                                                                          [[grant_request_2, grant_request_3], [grant_request_4]])

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 1
    cbsd_fad_records_iteration_1_sas_test_harness_0 = generateCbsdRecords([sas_test_harness_device_2,sas_test_harness_device_3],
                                                                          [[grant_request_1],[grant_request_2]])

    # Generate Cbsd FAD Records for SAS Test Harness 1, iteration 1
    cbsd_fad_records_iteration_1_sas_test_harness_1 = generateCbsdRecords([sas_test_harness_device_6], [[grant_request_5, grant_request_6]])
   
    # SAS Test Harnesses configuration  
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': 'localhost',
        'port': 9001,
        'serverCert': os.path.join('certs', 'server.cert'),
        'serverKey': os.path.join('certs', 'server.key'),
        'caCert': os.path.join('certs', 'ca.cert')
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': 'localhost',
        'port': 9002,
        'serverCert': os.path.join('certs', 'server.cert'),
        'serverKey': os.path.join('certs', 'server.key'),
        'caCert': os.path.join('certs', 'ca.cert')
    }

    # Generate SAS Test Harnesses dump records for multiple iterations   
    sas_test_harness_0_iteration_0_dump_records = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_0
    }
    sas_test_harness_0_iteration_1_dump_records = {
        'cbsdRecords': cbsd_fad_records_iteration_1_sas_test_harness_0
    }
    sas_test_harness_1_iteration_0_dump_records = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_1
    }
    sas_test_harness_1_iteration_1_dump_records = {
        'cbsdRecords': cbsd_fad_records_iteration_1_sas_test_harness_1
    }

    # Create the actual config.
    iteration0_config = {
        'cbsdRequests': [cbsd_records_iteration_0_domain_proxy_0,cbsd_records_iteration_0_domain_proxy_1],
        'protectedEntities': protected_entities_iteration_0,
        'dpaActivationList': [dpa_1, dpa_2],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [sas_test_harness_0_iteration_0_dump_records,sas_test_harness_1_iteration_0_dump_records]
    }
    iteration1_config = {
        'cbsdRequests': [cbsd_records_iteration_1_domain_proxy_0,cbsd_records_iteration_1_domain_proxy_1],
        'protectedEntities': protected_entities_iteration_1,
        'dpaActivationList': [dpa_3],
        'dpaDeactivationList': [dpa_1],
        'sasTestHarnessData': [sas_test_harness_0_iteration_1_dump_records,sas_test_harness_1_iteration_1_dump_records]
    }
    config = {
        'conditionalRegistrationData': conditionals,      
        'iterationData': [iteration0_config, iteration1_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': os.path.join('certs', 'dp_1_client.cert'),
                                'key':  os.path.join('certs', 'dp_1_client.key')},
                               {'cert': os.path.join('certs', 'dp_2_client.cert'),
                                'key':  os.path.join('certs', 'dp_2_client.key')}],
        'deltaIap': 2
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_MCP_1_default_config) 
  def test_WINNF_FT_S_MCP_1(self, config_filename):
    """SAS manages a mix of GAA and PAL Grants in 3550 MHz
       to 3700 MHz to protect configurable IAP-protected entities and DPAs
    """
    config = loadConfig(config_filename)
