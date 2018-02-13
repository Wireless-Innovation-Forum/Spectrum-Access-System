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
import sas_objects
import time
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig


class AggregateInterfaceProtectionTestcase(constraint_testcase.ConstraintTestcase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()
  
    def tearDown(self):
        pass
  
    def generate_XPR_1_default_config(self, filename):
        """ Generates the WinnForum configuration for XPR.1. """
        # Load CBSD
        device_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_a.json')))
        device_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_c.json')))

        # Load Grant requests
        grant_request_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_request_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))

        # Load PPA record
        ppa_record_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'ppa_record_0.json'))) 
        # Registration configuration for iteration 1
        cbsd_records_iter_1 = {'registrationRequests': [device_1, device_2],
                              'grantRequests': [grant_request_1, grant_request_2]}

        protected_entities_iter_1 = {'PPA': [ppa_record_1]}

        # Create the actual config.
        config = {
            'cbsdRecordsN1': [cbsd_records_iter_1],
            'protectedEntitiesPIAP': [protected_entities_iter_1],
            'dpConfig': {'cert': 'dp_client.cert', 'key': 'dp_client.key'},
            'K': 1,
            'headroom': {'MgPpa': 2, 'MgGwpz': 2, 'MgCochannel': 2,
                         'MgBlocking': 2, 'MgOobe': 2, 'MgEsc': 2},
            'protectionThreshold': {'QPpa': -80, 'QGwpz': -80,
                                    'QCochannel': -129, 'QBlocking': -60, 'QEsc': -109},
            'deltaIap': 2
  
           }
        writeConfig(filename, config)

    @configurable_testcase(generate_XPR_1_default_config) 
    def test_WINNF_FT_S_XPR_1(self, config_filename):
        """Grants from Multiple CBSDs Inside and Outside
           the Neighborhood (Y) of a Protected Entity (X)
        """
        config = loadConfig(config_filename)
        test_execution_type = 'xPR'
        # Invoking MCP test steps with flag indicating xPR execution
        self.executeMCPTestSteps(config,test_execution_type)
