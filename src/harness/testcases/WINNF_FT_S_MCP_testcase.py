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
import json
import os
import sas
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig


class MultiConstraintProtectionTestcase(constraint_testcase.ConstraintTestcase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()
  
    def tearDown(self):
        pass
  
    def generate_MCP_1_default_config(self, filename):
        """ Generates the WinnForum configuration for MCP.1. """
        # Load CBSD
        device_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_a.json')))
        device_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_b.json')))
        device_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_c.json')))
        device_4 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_d.json')))
  
        # Load Grant requests
        grant_request_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_request_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_1.json')))
        grant_request_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_2.json')))
        grant_request_4 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_3.json')))
     
        # Load Conditional Data 
        cbsd_conditional_device_1 = {
           'cbsdCategory': device_1['cbsdCategory'],
           'fccId': device_1['fccId'],
           'cbsdSerialNumber': device_1['cbsdSerialNumber'],
           'airInterface': device_1['airInterface'],
           'installationParam': device_1['installationParam'],
           'measCapability': device_1['measCapability']
         }
        cbsd_conditional_device_2 = {
           'cbsdCategory': device_2['cbsdCategory'],
           'fccId': device_2['fccId'],
           'cbsdSerialNumber': device_2['cbsdSerialNumber'],
           'airInterface': device_2['airInterface'],
           'installationParam': device_2['installationParam'],
           'measCapability': device_2['measCapability']
        }
        # Remove conditionals from registration
        del device_1['cbsdCategory']
        del device_1['airInterface']
        del device_1['installationParam']
        del device_1['measCapability']
        del device_2['cbsdCategory']
        del device_2['airInterface']
        del device_2['installationParam']
        del device_2['measCapability']
       
        conditionals_iter_1 = {'registrationData': [cbsd_conditional_device_1, cbsd_conditional_device_2]}
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
        ppa_record_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'ppa_record_0.json'))) 
        pal_record_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
        
        # Load DPA record
        dpa_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'dpa_0.json')))
        dpa_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'dpa_1.json')))
        dpa_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'dpa_2.json')))

        # Registration configuration for iteration 1
        cbsd_records_iter_1 = {'registrationRequests': [device_1, device_2],
                               'grantRequests': [grant_request_1, grant_request_2],
                               'conditionalRequests': conditionals_iter_1
                               }
        cbsd_records_iter_2 = {'registrationRequests': [device_3, device_4],
                               'grantRequests': [grant_request_3, grant_request_4]}
        pal_and_ppa_record_1 = {'PAL': pal_record_1, 'PPA': ppa_record_1}
        protected_entities_iter_1 = {'PalAndPpa': [pal_and_ppa_record_1], 'ESC': [esc_record_1]}
        protected_entities_iter_2 = {'GWPZ': [gwpz_record_1], 'FSS': [fss_record_1]}

        # SAS Test Harness FAD records
        # This section parameters are subjected to change based 
        # on the SAS Test Harness design, which is currenlty is in progress
        sas_th_cbsd_0 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_0.json')))
        sas_th_cbsd_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_1.json')))
        sas_th_cbsd_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_2.json')))
        sas_th_cbsd_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_3.json')))
        sas_th_cbsd_4 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_4.json')))
        sas_th_cbsd_5 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_5.json')))
        sas_th_0_cbsd_iter_0 = [sas_th_cbsd_0]
        sas_th_0_cbsd_iter_1 = [sas_th_cbsd_1]
        sas_th_0_cbsd_iter_2 = [sas_th_cbsd_2]
        sas_th_1_cbsd_iter_0 = [sas_th_cbsd_3]
        sas_th_1_cbsd_iter_1 = [sas_th_cbsd_4]
        sas_th_1_cbsd_iter_2 = [sas_th_cbsd_5]
    
        sas_harness_0 = {
                    'name': 'SAS-TH-1',
                    'url': 'localhost:9001',
                    'certFile': 'server_a.cert',
                    'keyFile': 'server_a.key',
                    'certificateHash': 'will be provided in future',
                    'cbsdRecord': [sas_th_0_cbsd_iter_0, sas_th_0_cbsd_iter_1, sas_th_0_cbsd_iter_2],
                    'fileServePath': 'sas_harness_2/'
                }
        sas_harness_1 = {
                    'name': 'SAS-TH-2',
                    'url': 'localhost:9002',
                    'certFile': 'server_b.cert',
                    'keyFile': 'server_b.key',
                    'certificateHash': 'will be provided in future',
                    'cbsdRecord': [sas_th_1_cbsd_iter_0, sas_th_1_cbsd_iter_1, sas_th_1_cbsd_iter_2],
                    'fileServePath': 'sas_harness_1/'
                }
        # Create the actual config.
        iter1_config = {
            'cbsdRecords': cbsd_records_iter_1,
            'protectedEntities': protected_entities_iter_1,
            'dpaActiveList': [dpa_1, dpa_2],
            'dpaDeactiveList': [],
            'deltaIap': 2
           }
        iter2_config = {
            'cbsdRecords': cbsd_records_iter_2,
            'protectedEntities': protected_entities_iter_2,
            'dpaActiveList': [dpa_3],
            'dpaDeactiveList': [dpa_1],
            'deltaIap': 2
           }

        config = {
            'iterationData': [iter1_config, iter2_config],
            'sasHarnesses': [sas_harness_0, sas_harness_1],
            'domainProxyConfig': [{'cert': 'dp_1_client.cert', 'key': 'dp_1_client.key'},
                         {'cert': 'dp_2_client.cert', 'key': 'dp_2_client.key'}]
             }
        writeConfig(filename, config)

    @configurable_testcase(generate_MCP_1_default_config) 
    def test_WINNF_FT_S_MCP_1(self, config_filename):
        """SAS manages a mix of GAA and PAL Grants in 3550 MHz
           to 3700 MHz to protect configurable IAP-protected entities and DPAs
        """
        config = loadConfig(config_filename)
