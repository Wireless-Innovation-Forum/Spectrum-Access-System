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
import logging
import common_strings
from concurrent.futures import ThreadPoolExecutor
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
import sas
import sas_testcase
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generatePpaRecords, generateCbsdReferenceId
import test_harness_objects
from util import winnforum_testcase, writeConfig, loadConfig, configurable_testcase, \
  getRandomLatLongInPolygon, makePpaAndPalRecordsConsistent, \
  addCbsdIdsToRequests, getCertFilename, getCertificateFingerprint, \
  getFqdnLocalhost, getUnusedPort
from testcases.WINNF_FT_S_MCP_testcase import McpXprCommonTestcase

from reference_models.pre_iap_filtering import pre_iap_filtering

class PpaProtectionTestcase(McpXprCommonTestcase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    self.ShutdownServers()

  def generate_PPR_1_default_config(self, filename):
    """ Generates the WinnForum configuration for PPR.1. """

    # Load PPA record
    ppa_record = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))

    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000

    ppa_record_1, pal_records_1 = makePpaAndPalRecordsConsistent(
                                  ppa_record,
                                  [pal_record],
                                  pal_low_frequency,
                                  pal_high_frequency,
                                  'test_user_1'
    )

    # Load devices info
    device_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Moving device_1 to a location within 40 KMs of PPA zone
    device_1['installationParam']['latitude'] = 38.8203
    device_1['installationParam']['longitude'] = -97.2741

    device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Moving device_2 to a location outside 40 KMs of PPA zone
    device_2['installationParam']['latitude'] = 39.31476
    device_2['installationParam']['longitude'] = -96.75139

    device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    # Moving device_3 to a location within PPA zone
    device_3['installationParam']['latitude'], \
    device_3['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record_1)

    device_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    # Moving device_4 to a location within PPA zone
    device_4['installationParam']['latitude'], \
    device_4['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record_1)

    # Load Grant requests
    grant_request_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_request_1['operationParam']['operationFrequencyRange']['lowFrequency'] = 3550000000
    grant_request_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3560000000

    grant_request_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_1.json')))
    grant_request_2['operationParam']['operationFrequencyRange']['lowFrequency'] = 3550000000
    grant_request_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3560000000
    
    grant_request_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_2.json')))
    grant_request_3['operationParam']['operationFrequencyRange']['lowFrequency'] = 3550000000
    grant_request_3['operationParam']['operationFrequencyRange']['highFrequency'] = 3560000000

    grant_request_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_request_4['operationParam']['operationFrequencyRange']['lowFrequency'] = 3550000000
    grant_request_4['operationParam']['operationFrequencyRange']['highFrequency'] = 3560000000

    # device_b and device_d are Category B
    # Load Conditional Data
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_device_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }

    self.assertEqual(device_4['cbsdCategory'], 'B')
    conditionals_device_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }

    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']

    # Registration and grant records
    cbsd_records_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2],
        'grantRequests': [grant_request_1, grant_request_2],
        'conditionalRegistrationData': [conditionals_device_2]
    }
    cbsd_records_domain_proxy_1 = {
        'registrationRequests': [device_3],
        'grantRequests': [grant_request_3],
        'conditionalRegistrationData': []
    }

    # Protected entity record
    protected_entities = {
        'palRecords': pal_records_1,
        'ppaRecords': [ppa_record_1]
    }

    iteration_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_domain_proxy_0,
                                          cbsd_records_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_4,
            'grantRequest': grant_request_4,
            'conditionalRegistrationData': conditionals_device_4,
            'clientCert': getCertFilename('device_d.cert'),
            'clientKey': getCertFilename('device_d.key')
        }],
        'protectedEntities': protected_entities,
        'dpaActivationList': [],
        'dpaDeactivationList': [],
        'sasTestHarnessData': []
    }

    # Create the actual config.
    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration_config],
        'sasTestHarnessConfigs': [],
        'domainProxyConfigs': [{
            'cert': getCertFilename('domain_proxy.cert'),
            'key': getCertFilename('domain_proxy.key')
        }, {
            'cert': getCertFilename('domain_proxy_1.cert'),
            'key': getCertFilename('domain_proxy_1.key')
        }]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PPR_1_default_config)
  def test_WINNF_FT_S_PPR_1(self, config_filename):
    """Single SAS PPA Protection
    """
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR1')

  def generate_PPR_2_default_config(self, filename):
    """ Generates the WinnForum configuration for PPR.2. """

    # Load PPA record
    ppa_record = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))

    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000

    ppa_record_1, pal_records_1 = makePpaAndPalRecordsConsistent(
                                  ppa_record,
                                  [pal_record],
                                  pal_low_frequency,
                                  pal_high_frequency,
                                  'test_user_1'
    )

    # Load devices info
    device_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Moving device_1 to a location within 40 KMs of PPA zone
    device_1['installationParam']['latitude'] = 38.8203
    device_1['installationParam']['longitude'] = -97.2741

    device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Moving device_2 to a location outside 40 KMs of PPA zone
    device_2['installationParam']['latitude'] = 39.31476
    device_2['installationParam']['longitude'] = -96.75139

    device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    # Moving device_3 to a location within PPA zone
    device_3['installationParam']['latitude'], \
    device_3['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record_1)

    device_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    # Moving device_4 to a location within PPA zone
    device_4['installationParam']['latitude'], \
    device_4['installationParam']['longitude'] = getRandomLatLongInPolygon(ppa_record_1)

    # Load Grant requests with overlapping frequency range for all devices
    grant_request_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_request_1['operationParam']['operationFrequencyRange']['lowFrequency'] = 3550000000
    grant_request_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3560000000

    grant_request_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_1.json')))
    grant_request_2['operationParam']['operationFrequencyRange']['lowFrequency'] = 3570000000
    grant_request_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3580000000

    grant_request_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_2.json')))
    grant_request_3['operationParam']['operationFrequencyRange']['lowFrequency'] = 3590000000
    grant_request_3['operationParam']['operationFrequencyRange']['highFrequency'] = 3600000000

    grant_request_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_request_4['operationParam']['operationFrequencyRange']['lowFrequency'] = 3610000000
    grant_request_4['operationParam']['operationFrequencyRange']['highFrequency'] = 3620000000

    # device_b and device_d are Category B
    # Load Conditional Data
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_device_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }

    self.assertEqual(device_4['cbsdCategory'], 'B')
    conditionals_device_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }

    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']

    # Registration and grant records
    cbsd_records_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2],
        'grantRequests': [grant_request_1, grant_request_2],
        'conditionalRegistrationData': [conditionals_device_2]
    }
    cbsd_records_domain_proxy_1 = {
        'registrationRequests': [device_3],
        'grantRequests': [grant_request_3],
        'conditionalRegistrationData': []
    }

    # Protected entity record
    protected_entities = {
        'palRecords': pal_records_1,
        'ppaRecords': [ppa_record_1]
    }

    # SAS Test Harnesses configurations,
    # Following configurations are for two SAS test harnesses
    sas_test_harness_device_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    sas_test_harness_device_1['fccId'] = "test_fcc_id_e"
    sas_test_harness_device_1['userId'] = "test_user_id_e"

    sas_test_harness_device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    sas_test_harness_device_2['fccId'] = "test_fcc_id_f"
    sas_test_harness_device_2['userId'] = "test_user_id_f"

    sas_test_harness_device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    sas_test_harness_device_3['fccId'] = "test_fcc_id_g"
    sas_test_harness_device_3['userId'] = "test_user_id_g"

    # Generate Cbsd FAD Records for SAS Test Harness 0
    cbsd_fad_records_sas_test_harness_0 = generateCbsdRecords(
                                          [sas_test_harness_device_1],
                                          [[grant_request_1]]
    )

    # Generate Cbsd FAD Records for SAS Test Harness 1
    cbsd_fad_records_sas_test_harness_1 = generateCbsdRecords(
                                          [sas_test_harness_device_2, sas_test_harness_device_3],
                                          [[grant_request_2], [grant_request_3]]
    )

    # Generate SAS Test Harnesses dump records
    dump_records_sas_test_harness_0 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_0
    }
    dump_records_sas_test_harness_1 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_1
    }

    # SAS Test Harnesses configuration
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert')
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas_1.cert'),
        'serverKey': getCertFilename('sas_1.key'),
        'caCert': getCertFilename('ca.cert')
    }

    iteration_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_domain_proxy_0,
                                          cbsd_records_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_4,
            'grantRequest': grant_request_4,
            'conditionalRegistrationData': conditionals_device_4,
            'clientCert': getCertFilename('device_d.cert'),
            'clientKey': getCertFilename('device_d.key')
        }],
        'protectedEntities': protected_entities,
        'dpaActivationList': [],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [dump_records_sas_test_harness_0,
                               dump_records_sas_test_harness_1]
    }

    # Create the actual config.
    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config,
                                  sas_test_harness_1_config],
        'domainProxyConfigs': [{
             'cert': getCertFilename('domain_proxy.cert'),
             'key': getCertFilename('domain_proxy.key')
        }, {
            'cert': getCertFilename('domain_proxy_1.cert'),
            'key': getCertFilename('domain_proxy_1.key')}
        ]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PPR_2_default_config)
  def test_WINNF_FT_S_PPR_2(self, config_filename):
    """Multiple SAS PPA Protection
    """
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR2')

  def generate_PPR_3_default_config(self, filename):
    """High-level description of the default config:

        SAS UUT has devices B, D; first gets a PAL grant and second is GAA.
        SAS TH has devices A, C, E, none of which have a PAL grant.

        SAS UUT has one PPA, with device B as the only CBSD.
        SAS TH has one PPA, with only non-granted CBSDs.
        The PPAs derive from different but adjacent PALs.

        Both PPAs are on 3620-3630 MHz, as are all grants except device D's.
        Device D's grant overlaps 3620-3630 but extends beyond.
    """
    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 38.842176
    device_a['installationParam']['longitude'] = -97.092863
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 38.815291
    device_b['installationParam']['longitude'] = -97.198805
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c['installationParam']['latitude'] = 38.816782
    device_c['installationParam']['longitude'] = -97.102965
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_d['installationParam']['latitude'] = 38.758462
    device_d['installationParam']['longitude'] = -97.189036
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_e['installationParam']['latitude'] = 38.761748
    device_e['installationParam']['longitude'] = -97.118459

    # Pre-load conditionals and remove REG-conditional fields from registration
    # requests.
    conditional_keys = [
        'cbsdCategory', 'fccId', 'cbsdSerialNumber', 'airInterface',
        'installationParam', 'measCapability'
    ]
    reg_conditional_keys = [
        'cbsdCategory', 'airInterface', 'installationParam', 'measCapability'
    ]
    conditionals_b = {key: device_b[key] for key in conditional_keys}
    device_b = {
        key: device_b[key]
        for key in device_b
        if key not in reg_conditional_keys
    }
    conditionals_d = {key: device_d[key] for key in conditional_keys}
    device_d = {
        key: device_d[key]
        for key in device_d
        if key not in reg_conditional_keys
    }

    # Load grant requests (default is 3620-3630).
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_d = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_d['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3620000000
    grant_d['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3640000000
    grant_e = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # CBSDs in SAS UUT.
    domain_proxy = {
        'registrationRequests': [device_b, device_d],
        'grantRequests': [grant_b, grant_d],
        'conditionalRegistrationData': [conditionals_b, conditionals_d],
        'cert': getCertFilename('domain_proxy.cert'),
        'key': getCertFilename('domain_proxy.key')
    }

    # One PPA in SAS UUT.
    pal_low_frequency = 3620000000
    pal_high_frequency = 3630000000
    pal_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    ppa_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record_0, pal_records_0 = makePpaAndPalRecordsConsistent(
        ppa_record_0, [pal_record_0], pal_low_frequency, pal_high_frequency,
        'test_user_1')
    device_b['userId'] = 'test_user_1'
    ppa_cluster_list = [0]  # The first device is device B.

    # One PPA in the peer SAS test harness.
    pal_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    pal_record_1['fipsCode'] = 20041084500
    ppa_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_1.json')))
    ppa_record_1['zone']['features'][0]['geometry']['coordinates'] = [[[
        -97.13, 38.85
    ], [-97.13, 38.75], [-97.05, 38.75], [-97.05, 38.85], [-97.13, 38.85]]]
    ppa_record_1, pal_records_1 = makePpaAndPalRecordsConsistent(
        ppa_record_1, [pal_record_1], pal_low_frequency, pal_high_frequency,
        'test_user_2')

    # Generate FAD records.
    cbsd_records = [device_a, device_c, device_e]
    grant_record_list = [[grant_a], [grant_c], [grant_e]]
    # Create CBSD reference IDs.
    cbsd_reference_id1 = generateCbsdReferenceId('test_fcc_id_x',
                                                 'test_serial_number_x')
    cbsd_reference_id2 = generateCbsdReferenceId('test_fcc_id_y',
                                                 'test_serial_number_y')
    cbsd_reference_ids = [[cbsd_reference_id1, cbsd_reference_id2]]
    # Create records.
    sas_harness_dump_records = {
        'cbsdRecords': generateCbsdRecords(cbsd_records, grant_record_list),
        'ppaRecords': generatePpaRecords([ppa_record_1], cbsd_reference_ids),
    }

    # SAS test harness configuration.
    sas_harness_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': 'certs/ca.cert'
    }

    config = {
        'domainProxy':
            domain_proxy,  # Includes registration and grant requests.
        'ppaRecord': ppa_record_0,  # PPA in SAS UUT.
        'ppaClusterList':
            ppa_cluster_list,  # Same format and semantics as SIQ.12.
        'palRecords': [pal_records_0[0],
                       pal_records_1[0]],  # PALs for both PPAs.
        'sasTestHarnessDumpRecords':
            sas_harness_dump_records,  # CBSDs and one PPA.
        'sasTestHarnessConfig':
            sas_harness_config,  # Just the config, no records.
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PPR_3_default_config)
  def test_WINNF_FT_S_PPR_3(self, config_filename):
    config = loadConfig(config_filename)

    # Initialize test-wide variables, and state variables.
    self.config = config
    self.active_dpas = []
    self.sas_test_harness_objects = []
    self.domain_proxy_objects = []
    self.protected_entity_records = {}
    self.num_peer_sases = 1
    self.cpas_executor = ThreadPoolExecutor(max_workers=1)
    self.agg_interf_check_executor = ThreadPoolExecutor(max_workers=1)
    self.sas_uut_fad = None
    self.test_harness_fads = []  # List for consistency with MCP code.
    self.all_dpa_checks_succeeded = True

    # Notify SAS UUT that a peer SAS exists (and start the SAS server)
    logging.info('Step 1: activate one SAS test harness and notify SAS UUT.')
    test_harness = config['sasTestHarnessConfig']
    logging.info('Creating SAS TH with config %s', test_harness)

    # Initialize SAS Test Harness Server instance to dump FAD records
    sas_test_harness_object = SasTestHarnessServer(
        test_harness['sasTestHarnessName'], test_harness['hostName'],
        test_harness['port'], test_harness['serverCert'],
        test_harness['serverKey'], test_harness['caCert'])
    self.InjectTestHarnessFccIds(
        config['sasTestHarnessDumpRecords']['cbsdRecords'])
    sas_test_harness_dump_records = [
        config['sasTestHarnessDumpRecords']['cbsdRecords'],
        config['sasTestHarnessDumpRecords']['ppaRecords']
    ]
    sas_test_harness_object.writeFadRecords(sas_test_harness_dump_records)
    # Start the server
    sas_test_harness_object.start()

    # Inform SAS UUT about SAS Test Harness.
    certificate_hash = getCertificateFingerprint(test_harness['serverCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': sas_test_harness_object.getBaseUrl()})

    # Store required info in the test harness.
    self.fad_cert = test_harness['serverCert']
    self.fad_key = test_harness['serverKey']
    self.sas_test_harness_objects.append(sas_test_harness_object)

    # Extract PPA record from peer SAS and add to local protected entities.
    peer_sas_ppa = config['sasTestHarnessDumpRecords']['ppaRecords'][0]
    self.protected_entity_records['ppaRecords'] = [peer_sas_ppa]

    # Inject all PALs (used by SAS UUT PPA and peer SAS PPA)
    logging.info('Step 2: inject PAL records.')
    for index, pal_record in enumerate(config['palRecords']):
      try:
        logging.info('Injecting PAL record #%d', index)
        self._sas_admin.InjectPalDatabaseRecord(pal_record)
      except Exception:
        logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
        raise
    self.protected_entity_records['palRecords'] = config['palRecords']

    # Register, inject PPA, and request grants.
    logging.info('Steps 3 - 5: register, inject PPA, request grants')
    domain_proxy_config = config['domainProxy']
    domain_proxy = test_harness_objects.DomainProxy(self,
                                                    domain_proxy_config['cert'],
                                                    domain_proxy_config['key'])
    self.domain_proxy_objects.append(domain_proxy)
    ppa = domain_proxy.registerCbsdsAndRequestGrantsWithPpa(
        domain_proxy_config['registrationRequests'],
        domain_proxy_config['grantRequests'], config['ppaRecord'],
        config['ppaClusterList'],
        domain_proxy_config['conditionalRegistrationData'])
    # Make sure SAS UUT's PPA is also checked for protection.
    self.protected_entity_records['ppaRecords'].append(ppa)

    # FAD exchange.
    logging.info('Step 6 + 7: FAD exchange')
    self.sas_uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin,
                                                 self.fad_cert, self.fad_key)
    self.test_harness_fads.append(
        getFullActivityDumpSasTestHarness(
            self.sas_test_harness_objects[0].getSasTestHarnessInterface()))

    # Trigger CPAS in SAS UUT, and wait until completion.
    logging.info('Step 8: trigger CPAS')
    self.cpas = self.cpas_executor.submit(
        self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete)

    logging.info('Step 9: execute IAP reference model')
    # Pre-IAP filtering.
    pre_iap_filtering.preIapReferenceModel(self.protected_entity_records,
                                           self.sas_uut_fad,
                                           self.test_harness_fads)
    # IAP reference model.
    self.performIap()

    # Heartbeat, relinquish, grant, heartbeat
    logging.info('Steps 10 - 13: heartbeat, relinquish, grant, heartbeat.')
    domain_proxy.performHeartbeatAndUpdateGrants()

    # Aggregate interference check
    logging.info(
        'Step 14 and CHECK: calculating and checking aggregate interference')
    self.performIapAndDpaChecks()
