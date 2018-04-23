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

from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
from functools import partial
import json
import os
import sas
import sas_testcase
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generatePpaRecords
import time
import test_harness_objects
from util import winnforum_testcase, configurable_testcase, getCertificateFingerprint, writeConfig, \
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
    device_7 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_g.json')))
    device_8 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_h.json')))

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
    grant_request_7 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_2.json')))
    grant_request_8 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_3.json')))

    # device_b device_d and device_h are of Category B
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
    self.assertEqual(device_8['cbsdCategory'], 'B')
    conditionals_device_8 = {
        'cbsdCategory': device_8['cbsdCategory'],
        'fccId': device_8['fccId'],
        'cbsdSerialNumber': device_8['cbsdSerialNumber'],
        'airInterface': device_8['airInterface'],
        'installationParam': device_8['installationParam'],
        'measCapability': device_8['measCapability']
    }

    conditionals = [conditionals_device_2, conditionals_device_4, conditionals_device_8]
    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']
    del device_8['cbsdCategory']
    del device_8['airInterface']
    del device_8['installationParam']
    del device_8['measCapability']

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

    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000

    ppa_record_1, pal_records_1 = makePpaAndPalRecordsConsistent(ppa_record,
                                                                 [pal_record],
                                                                 pal_low_frequency,
                                                                 pal_high_frequency,
                                                                 'test_user_1')
    # Define DPAs
    dpa_1 = {
       'dpaId': 'east_dpa_4',
       'frequencyRange': {'lowFrequency': 3550000000, 'highFrequency': 3650000000}
    }
    dpa_2 = {
       'dpaId': 'east_dpa_5',
       'frequencyRange': {'lowFrequency': 3550000000, 'highFrequency': 3650000000}
    }
    dpa_3 = {
       'dpaId': 'east_dpa_6',
       'frequencyRange': {'lowFrequency': 3550000000, 'highFrequency': 3650000000}
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
        'ppaRecords': [ppa_record_1],
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
    sas_test_harness_device_1['userId'] = "test_user_id_g"

    sas_test_harness_device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    sas_test_harness_device_2['fccId'] = "test_fcc_id_h"
    sas_test_harness_device_2['userId'] = "test_user_id_h"

    sas_test_harness_device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    sas_test_harness_device_3['fccId'] = "test_fcc_id_i"
    sas_test_harness_device_3['userId'] = "test_user_id_i"

    sas_test_harness_device_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    sas_test_harness_device_4['fccId'] = "test_fcc_id_j"
    sas_test_harness_device_4['userId'] = "test_user_id_j"

    sas_test_harness_device_5 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_e.json')))
    sas_test_harness_device_5['fccId'] = "test_fcc_id_k"
    sas_test_harness_device_5['userId'] = "test_user_id_k"

    sas_test_harness_device_6 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_f.json')))
    sas_test_harness_device_6['fccId'] = "test_fcc_id_l"
    sas_test_harness_device_6['userId'] = "test_user_id_l"

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_0 = generateCbsdRecords([sas_test_harness_device_1], [[grant_request_1]])

    # Generate Cbsd FAD Records for SAS Test Harness 1, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_1 = generateCbsdRecords([sas_test_harness_device_4, sas_test_harness_device_5],
                                                                          [[grant_request_2, grant_request_3], [grant_request_4]])

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 1
    cbsd_fad_records_iteration_1_sas_test_harness_0 = generateCbsdRecords([sas_test_harness_device_2, sas_test_harness_device_3],
                                                                          [[grant_request_1], [grant_request_2]])

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
    dump_records_iteration_0_sas_test_harness_0 = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_0
    }
    dump_records_iteration_1_sas_test_harness_0 = {
        'cbsdRecords': cbsd_fad_records_iteration_1_sas_test_harness_0
    }
    dump_records_iteration_0_sas_test_harness_1 = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_1
    }
    dump_records_iteration_1_sas_test_harness_1 = {
        'cbsdRecords': cbsd_fad_records_iteration_1_sas_test_harness_1
    }

    # Create the actual config.
    iteration0_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_iteration_0_domain_proxy_0, cbsd_records_iteration_0_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_7,
            'grantRequest': grant_request_7,
            'clientCert': os.path.join('certs', 'client.cert'),
            'clientKey': os.path.join('certs', 'client.key')
        }],
        'protectedEntities': protected_entities_iteration_0,
        'dpaActivationList': [dpa_1, dpa_2],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [dump_records_iteration_0_sas_test_harness_0, dump_records_iteration_0_sas_test_harness_1]
    }
    iteration1_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_iteration_1_domain_proxy_0, cbsd_records_iteration_1_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_8,
            'grantRequest': grant_request_8,
            'clientCert': os.path.join('certs', 'client.cert'),
            'clientKey': os.path.join('certs', 'client.key')
        }],
        'protectedEntities': protected_entities_iteration_1,
        'dpaActivationList': [dpa_3],
        'dpaDeactivationList': [dpa_1],
        'sasTestHarnessData': [dump_records_iteration_1_sas_test_harness_0, dump_records_iteration_1_sas_test_harness_1]
    }
    config = {
        'conditionalRegistrationData': conditionals,
        'iterationData': [iteration0_config, iteration1_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': os.path.join('certs', 'domain_proxy.cert'),
                                'key': os.path.join('certs', 'domain_proxy.key')},
                               {'cert': os.path.join('certs', 'domain_proxy.cert'),
                                'key': os.path.join('certs', 'domain_proxy.key')}],
        'deltaIap': 2
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_MCP_1_default_config)
  def test_WINNF_FT_S_MCP_1(self, config_filename):
    """SAS manages a mix of GAA and PAL Grants in 3550 MHz
       to 3700 MHz to protect configurable IAP-protected entities and DPAs
    """
    config = loadConfig(config_filename)
    test_type = 'MCP'
    # Invoke MCP test steps
    self.executeMcpTestSteps(config, test_type)

  def executeMcpTestSteps(self, config, test_type):
    """Execute all teststeps for MCP testcase and for xPR testcases till Step22

    Args:
       config: Testcase configuration
       test_type: A string which indicates the type of testcase to be invoked("MCP"/"XPR")
    Return: None
    """
    sas_test_harness_objects = []
    domain_proxy_objects = []

    # Load conditionals
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    for domain_proxy in config['domainProxyConfigs']:
      domain_proxy_objects.append(test_harness_objects.DomainProxy(domain_proxy['cert'],\
                                                                   domain_proxy['key'],
                                                                   self))
    # Step 1 : Load DPAs
    self._sas_admin.TriggerLoadDpas()

    # STEP 2 : ESC inf rms SAS about inactive DPA
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Step 3 : creates multiple SAS TH, and Load predefined FAD,CBSD
    for test_harness in config['sasTestHarnessConfigs']:
      # Initialize SAS Test Harness Server instance to dump FAD records
      sas_test_harness_object = SasTestHarnessServer(test_harness['sasTestHarnessName'],
                                                           test_harness['hostName'],
                                                           test_harness['port'],
                                                           test_harness['serverCert'],
                                                           test_harness['serverKey'],
                                                           test_harness['caCert'])
      # Start the server
      sas_test_harness_object.start()

      # informing SAS UUT about SAS Test Harnesses
      certificate_hash = getCertificateFingerprint(test_harness['serverCert'])
      self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                     'url': sas_test_harness_object.getBaseUrl()})
      sas_test_harness_objects.append(sas_test_harness_object)
   
    # Step 4,5 : Inject IAP protected entities into UUT
    for iteration_content in config['iterationData']:
      cbsd_as_dp_list = []

      # Execute steps for single iteration
      self.executeSingleMCPIteration(test_type, iteration_content, sas_test_harness_objects, 
                                  domain_proxy_objects, cbsd_as_dp_list)

    # Stopping Test harness servers
    for test_harness in sas_test_harness_objects:
      test_harness.shutdown()
      del test_harness

  def checkMcpIap(self, protected_entity, agg_interference_list, iap_refmodel_margin_list, delta_iap):
    """Calculating IAP for each FSS and ESC sensor protection point,
    and for at least 95% of the protection points of each PPA and GWPZ.
    """
    pass

  def callAggregateInterferenceModel(self, cbsd_list, protected_entity):
    """Args:
         cbsd_list: List of cbsds with Authorized grants
         protected_entity: A dictionary with multiple key-value pairs where
         keys are protection entities

       Returns:
         Aggregate Interference list
    """
    pass

  def executeSingleMCPIteration(self, test_type, iteration_content, sas_test_harness_objects,
                                                          domain_proxy_objects, cbsd_as_dp_list):
    """Executes the steps from Step1 to Step22 for MCP and XPR testcases

    Args:
       test_type: A string which indicates the testcase type
       iteration_content: A dictionary with multiple key-value pairs that contain iteration data
       sas_test_harness_objects: SAS Test Harnesses objects
       domain_proxy_objects: Domain proxy objects
       cbsd_as_dp_list: list of Domain Proxy objects, which act like individual CBSD
    """
    fad_test_harnesses_objects = []
    cbsds_with_domain_proxies = []
    protected_entity_records = iteration_content['protectedEntities']
    if 'fssRecords' in protected_entity_records:
      for fss_record in protected_entity_records['fssRecords']:
        self._sas_admin.InjectFss({'record': fss_record})

    if 'gwpzRecords' in protected_entity_records:
      for gwpz_record in protected_entity_records['gwpzRecords']:
        self._sas_admin.InjectWisp({'record': gwpz_record})

    if 'escRecords' in protected_entity_records:
      for esc_record in protected_entity_records['escRecords']:
        self._sas_admin.InjectEscSensorDataRecord({'record': esc_record})

    if 'ppaRecords' in protected_entity_records:
      for ppa_record in protected_entity_records['ppaRecords']:
        self._sas_admin.InjectZoneData({'record': ppa_record})

    # Step 6,7 : Creating FAD Object and Pull FAD records from SAS UUT
    if iteration_content['sasTestHarnessData']:
      fad_uut_object = getFullActivityDumpSasUut(self._sas,
                                                 self._sas_admin)

      # Pull FAD from SAS Test Harnesses and fad objects are created for each SAS Test Harnesses
      for test_harness in sas_test_harness_objects:
        fad_test_harnesses_objects.append(getFullActivityDumpSasTestHarness(
                                          test_harness.getSasTestHarnessInterface()))

    # Step 8 : Trigger CPAS and wait until completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9 : Invoke IAP reference model
    # Call Pre IAP model
    # TODO: To invoke pre-iap model

    # Call IAP reference model
    # TODO: To invoke IAP reference model

    # Step 10 : DP Test Harness Register N(2,k)CBSDs with SAS UUT
    # Use DP objects to get CBSD registered
    for domain_proxy_object, cbsdRequestsWithDomainProxy in zip(domain_proxy_objects,
                                                                iteration_content['cbsdRequestsWithDomainProxies']):
      registration_requests = cbsdRequestsWithDomainProxy['registrationRequests']
      grant_requests = cbsdRequestsWithDomainProxy['grantRequests']

      #  Initiation of Registration and Grant procedures for the configured records
      domain_proxy_object.registerCbsdsAndRequestGrants(registration_requests, grant_requests)

      # Step 11 : Send heartbeat request
      domain_proxy_object.heartbeatForAllActiveGrants()

      # Get the list of CBSDs
      cbsds_with_domain_proxies.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    # Register individual Cbsds(Domain Proxy with single CBSD)
    for cbsd_record in iteration_content['cbsdRecords']:
      proxy = test_harness_objects.DomainProxy(cbsd_record['clientCert'], cbsd_record['clientKey'], self)
      proxy.registerCbsdsAndRequestGrants([cbsd_record['registrationRequest']], [cbsd_record['grantRequest']])
      cbsd_as_dp_list.append(proxy)

    # Step 12 : Invoke Aggregate Interference Model
    # TODO: To invoke Aggregate Interference Model

    # Check MCP.1
    # TODO: To invoke checkMcpIap method

    # Step 13 : Configure SAS Harness with FAD,trigger FAD generation
    for test_harness, test_harness_data in zip(sas_test_harness_objects, iteration_content['sasTestHarnessData']):
      sas_test_harness_dump_records = [test_harness_data['cbsdRecords']]
      test_harness.writeFadRecords(sas_test_harness_dump_records)

    # Step 14,15 : Trigger Full Activty Dump and Pull FAD records from SAS UUT
    fad_uut_object = getFullActivityDumpSasUut(self._sas,
                                               self._sas_admin)

    # Step 16 : Trigger CPAS and wait for its completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 17 : Call IAP reference model
    # TODO: To invoke DPA Move Reference model

    # Call Pre IAP model
    # TODO: To invoke Pre-iap reference model

    # Call IAP reference model
    # TODO: To invoke IAP reference model

    # Step 18,19,20 and 21 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
    for domain_proxy_object in domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()

      # Step 22: Calculating the Aggregate interface and IAP reference model invoke.
      cbsds_with_domain_proxies.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    # Invoke Aggregate Interference Model
    # TODO: To invoke Aggregate Interference Model

    # Check MCP.1
    # TODO: To invoke checkMcpIap method
    # Execute from Step23 to Step30 only for MCP testcase
    if test_type == 'MCP':
      self.executeMCPOnlyTestSteps(iteration_content, domain_proxy_objects, cbsd_as_dp_list)


  def executeMCPOnlyTestSteps(self, iteration_content, domain_proxy_objects, cbsd_as_dp_list):
    """Executes the steps from Step23 to Step30 for MCP testcase

    Args:
       iteration_content: A dictionary with multiple key-value pairs that contain iteration data
       domain_proxy_objects: Domain proxy objects
       cbsd_as_dp_list: list of Domain Proxy objects, which act like individual CBSD
    """
    cbsds_with_domain_proxies = []
    # Step 23: ESC Test harness enables DPA activations
    # deactivated the dpaDeactivationList DPA IDs
    for dpa in iteration_content['dpaActivationList']:
      self._sas_admin.TriggerDpaDeactivation(dpa)

    # activated the dpaActivationList DPA IDs
    # step 24: wait for 240 sec if DPA is activated in step 23 else 15 sec
    for dpa in iteration_content['dpaActivationList']:
      self._sas_admin.TriggerDpaActivation(dpa)
    if iteration_content['dpaActivationList']:
      time.sleep(240)
    else:
      time.sleep(15)

    # Step 25,26,27 and 28 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
    for domain_proxy_object in domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()

      # Step 29
      # TODO: Aggregate interference for DPA

      # Step 30:Invoke Aggregate Interference Model
      cbsds_with_domain_proxies.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    # Invoke Aggregate Interference Model
    # TODO: To invoke Aggregate Interference Model

    # Check MCP.1
    # TODO: To invoke checkMcpIap method

    # check MCP.1 DPA
    # TODO: need to invoke the DPA checkperformHeartbeatAndUpdateGrants
