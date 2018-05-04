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
<<<<<<< HEAD
import common_strings
=======
from functools import partial
>>>>>>> MCP.1 integration
import json
import os
import sas
import sas_testcase
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generatePpaRecords
from reference_models.pre_iap_filtering import pre_iap_filtering
import time
import test_harness_objects
from util import winnforum_testcase, configurable_testcase, getCertificateFingerprint, writeConfig, \
  loadConfig, makePpaAndPalRecordsConsistent
from full_activity_dump import FullActivityDump
from reference_models.iap import iap 
from reference_models.interference import aggregate_interference, interference
import multiprocessing
from multiprocessing import Pool

NUM_OF_PROCESS = 30
IAP_MARGIN = 1 # Threshold value in dBm

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
      open(os.path.join('testcases', 'mcp_testdata', 'gwpz_record_0.json')))

    # Load FSS record
    fss_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))

    # Load ESC record
    esc_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))

    # Load PPA record
    ppa_record = json.load(
      open(os.path.join('testcases', 'mcp_testdata', 'ppa_record_0.json')))
    pal_record = json.load(
      open(os.path.join('testcases', 'mcp_testdata', 'pal_record_0.json')))

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
            'registration': device_7,
            'grants': grant_request_7,
            'clientCert': sas.GetDefaultDomainProxySSLCertPath(),
            'clientKey': sas.GetDefaultDomainProxySSLKeyPath()
        }],
        'protectedEntities': protected_entities_iteration_0,
        'dpaActivationList': [dpa_1, dpa_2],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [dump_records_iteration_0_sas_test_harness_0, dump_records_iteration_0_sas_test_harness_1]
    }
    iteration1_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_iteration_1_domain_proxy_0, cbsd_records_iteration_1_domain_proxy_1],
        'cbsdRecords': [{
            'registration': device_8,
            'grants': grant_request_8,
            'clientCert': sas.GetDefaultDomainProxySSLCertPath(),
            'clientKey': sas.GetDefaultDomainProxySSLKeyPath()
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
        'deltaIap': 1
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
      domain_proxy_objects.append(test_harness_objects.DomainProxy(self, domain_proxy['cert'],\
                                                                   domain_proxy['key'],
                                                                   ))
    # Step 1 : Load DPAs
    self._sas_admin.TriggerLoadDpas()

    # STEP 2 : ESC informs SAS about inactive DPA
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
      # Execute steps for single iteration
      self.executeSingleMCPIteration(test_type, iteration_content, sas_test_harness_objects, 
                                     domain_proxy_objects)
    
    # Stopping Test harness servers
    for test_harness in sas_test_harness_objects:
      test_harness.shutdown()
      del test_harness

  def performIapAndAggregateInterferenceCheck(self, protection_entities, sas_uut,
                                      sas_th_fad_objects, cbsd_list):
    """Compare the interference calculated using iap and aggregate reference models.

    Args:
      protection_entities : List of entity records needed to be protected 
      sas_uut : FAD object from SAS UUT
      sas_th_fad_objects : a list of FAD objects from SAS Test Harness
      cbsd_list : List of new cbsds registered to the SAS.

    Returns:
      True or False based on the comparison of Aggregate Interference values
      against the two reference models
    """
    
    # Calculate and compare the interference value for PPA protection entity 
    if 'ppaRecords' in protection_entities:
      for ppa_record in protection_entities['ppaRecords']:
        pal_records = protection_entities['palRecords']
        pool = Pool(processes=min(multiprocessing.cpu_count(), NUM_OF_PROCESS))
        # Call iap reference model for ppa
        ppa_ap_iap_ref_values = iap.\
             performIapForPpa(ppa_record, sas_uut, sas_th_fad_objects, pal_records, pool)
        # Call aggregate interference reference model for ppa
        ppa_aggr_interference = aggregate_interference.\
             calculateAggregateInterferenceForPpa(ppa_record, pal_records, cbsd_list, pool)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(ppa_ap_iap_ref_values, ppa_aggr_interference, 'area')

    # Calculate and compare the interference value for GWPZ protection entity
    if 'gwpzRecords' in protection_entities:
      for gwpz_record in protection_entities['gwpzRecords']:
        pool = Pool(processes=min(multiprocessing.cpu_count(), NUM_OF_PROCESS))
        # Call iap reference model for gwpz
        gwpz_ap_iap_ref_values = iap.\
            performIapForGwpz(gwpz_record, sas_uut, sas_th_fad_objects)
        # Call aggregate interference reference model for gwpz
        gwpz_aggr_interference = aggregate_interference.\
            calculateAggregateInterferenceForGwpz(gwpz_record, cbsd_list, pool)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(gwpz_ap_iap_ref_values, gwpz_aggr_interference, 'area')

    # Calculate and compare the interference value for FSS protection point
    if 'fssRecords' in protection_entities:
      for fss_record in protection_entities['fssRecords']:
        fss_freq_range = fss_record['record']['deploymentParam'][0]\
            ['operationParam']['operationFrequencyRange']
        fss_low_freq = fss_freq_range['lowFrequency']
        fss_high_freq = fss_freq_range['highFrequency']
        fss_ttc_flag = fss_record['ttc']
        if (fss_low_freq >= interference.FSS_LOW_FREQ_HZ and 
                fss_low_freq < interference.CBRS_HIGH_FREQ_HZ):
          # Call IAP for FSS blocking and FSS cochannel
          fss_cochannel_ap_iap_ref_values = iap.\
              performIapForFssCochannel(fss_record, sas_uut, sas_th_fad_objects)
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, sas_uut, sas_th_fad_objects)
          # Call Aggregate interference for FSS blocking ad FSS cochannel
          fss_cochannel_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssCochannel(fss_record, cbsd_list)
          fss_blocking_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssBlocking(fss_record, cbsd_list)
          # Check and compare interference for FSS entity
          self.compareIapAndAggregateResults(fss_cochannel_ap_iap_ref_values, fss_cochannel_aggr_interference,'point')
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values, fss_blocking_aggr_interference,'point')
        elif (fss_low_freq >= interference.FSS_TTC_LOW_FREQ_HZ and 
                 fss_high_freq <= interference.FSS_TTC_HIGH_FREQ_HZ and 
                 fss_ttc_flag is True):
          # Call iap reference model for FSS blocking
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, sas_uut, sas_th_fad_objects)
          # Call aggregate interference model for FSS blocking
          fss_blocking_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssBlocking(fss_record, cbsd_list)
          # Compare the interference values calculated from both models
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values,\
              fss_blocking_aggr_interference, 'point')

    # Calculate and compare the interference value for ESC protection point 
    if 'escRecords' in protection_entities:
      for esc_record in protection_entities['escRecords']:
        # Call iap reference model for esc
        esc_ap_iap_ref_values = iap.\
            performIapForEsc(esc_record, sas_uut, sas_th_fad_objects)
        # Call aggregate interference model for esc 
        esc_aggr_interference = aggregate_interference.\
            calculateAggregateInterferenceForEsc(esc_record, cbsd_list)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(esc_ap_iap_ref_values, esc_aggr_interference, 'point')
      
  def compareIapAndAggregateResults(self, ap_iap_ref_values, aggr_interference, entity_type):
    """Verify aggregate interference is less than or equal to ap_iap_ref value calculated 
    by IAP model plus a delta for each FSS and ESC sensor protection point, and for at
    least 95% of the protection points of each PPA and GWPZ.

    Args:
      ap_iap_ref_values : Aggregate interference output calculated from IAP 
                             reference model 
      aggr_interference : Aggregate interference output calculated from Aggregate
                          Inteference reference model 
      entity_type : To identify its a point protection or area protection entity 

    Returns:
       Pass or Fail based on the comparison of the values within range
    """
    iter_count = 0 # Variable to count the number of interference entries
    match_count = 0 # Variable to count the number of matching interference entries
    
    for lat_dict in ap_iap_ref_values:
      long_dict = ap_iap_ref_values[lat_dict]
      long_dict_aggr = aggr_interference[lat_dict]
      for interf in long_dict:
        index = 0 
        for interf_iap in long_dict[interf]:
          # The aggregate interference should be less than 
          # or equal to the iap interference + iap margin threshold
          if long_dict_aggr[interf][index] <= \
                interf_iap+interference.dbToLinear(IAP_MARGIN):
            match_count+=1
            index+=1
          iter_count+=1

    if entity_type is 'area':
      # For protection areas the match of toltal interefrence values 
      # should be greater than or equal to 95 percentile
      self.assertGreaterEqual( (match_count/iter_count)*100.0, 95) 
    else:
      # For Protection points the comparison match should be 100 percentile
      self.assertEqual(((match_count/iter_count)*100), 100)

  def executeSingleMCPIteration(self, test_type, iteration_content, sas_test_harness_objects,
                                                          domain_proxy_objects):
    """Executes the steps from Step1 to Step22 for MCP and XPR testcases

    Args:
      test_type: A string which indicates the testcase type
      iteration_content: A dictionary with multiple key-value pairs that contain iteration data
      sas_test_harness_objects: SAS Test Harnesses objects
      domain_proxy_objects: Domain proxy objects
    """

    protected_entity_records = iteration_content['protectedEntities']
    if 'fssRecords' in protected_entity_records:
      for fss_record in protected_entity_records['fssRecords']:
        try:
          self._sas_admin.InjectFss({'record': fss_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e

    if 'gwpzRecords' in protected_entity_records:
      for gwpz_record in protected_entity_records['gwpzRecords']:
        try:
          self._sas_admin.InjectWisp({'record': gwpz_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e


    if 'escRecords' in protected_entity_records:
      for esc_record in protected_entity_records['escRecords']:
<<<<<<< HEAD
        try:
          self._sas_admin.InjectEscSensorDataRecord({'record': esc_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e


=======
        self._sas_admin.InjectEscSensorDataRecord({'record': esc_record})
     
>>>>>>> MCP.1 integration
    if 'ppaRecords' in protected_entity_records:
      for ppa_record in protected_entity_records['ppaRecords']:
        try:
          self._sas_admin.InjectZoneData({'record': ppa_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e

    # Step 6,7 : Creating FAD Object and Pull FAD records from SAS UUT
    fad_test_harnesses_objects = []
    if iteration_content['sasTestHarnessData']:
      fad_uut_object = getFullActivityDumpSasUut(self._sas,
                                                 self._sas_admin)

      # Pull FAD from SAS Test Harnesses and fad objects are created for each SAS Test Harnesses
      for test_harness in sas_test_harness_objects:
        fad_test_harnesses_objects.append(getFullActivityDumpSasTestHarness(
                                          test_harness.getSasTestHarnessInterface()))

    # Step 8 : Trigger CPAS and wait until completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 10 : DP Test Harness Register N(2,k)CBSDs with SAS UUT
    # Use DP objects to register CBSDs
    cbsds=[] #contain all CBSDs with authorized grants 
    
    for domain_proxy_object, cbsdRequestsWithDomainProxy in zip(domain_proxy_objects,
                                                                iteration_content['cbsdRequestsWithDomainProxies']):
      registration_requests = cbsdRequestsWithDomainProxy['registrationRequests']
      grant_requests = cbsdRequestsWithDomainProxy['grantRequests']

      #  Initiation of Registration and Grant procedures for the configured records
      domain_proxy_object.registerCbsdsAndRequestGrants(registration_requests, grant_requests)

    # Register individual Cbsds(Domain Proxy with single CBSD)
    for cbsd_record in iteration_content['cbsdRecords']:
      proxy = test_harness_objects.DomainProxy(self, cbsd_record['clientCert'], cbsd_record['clientKey'])
      proxy.registerCbsdsAndRequestGrants([cbsd_record['registration']], [cbsd_record['grants']])
      domain_proxy_objects.append(proxy)

    # Step 11 : Send heartbeat request managed by SAS UUT
    for domain_proxy_object in domain_proxy_objects:
      domain_proxy_object.heartbeatForAllActiveGrants()
      cbsds.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    cbsd_records = getFullActivityDumpSasTestHarness(cbsds).getCbsdRecords()
  
    # Call Pre IAP model
    pre_iap_filtering.preIapReferenceModel(protected_entity_records, 
                                    fad_uut_object, fad_test_harnesses_objects)

    # Step 12 : Invoke IAP model and Aggregate Interference Model
    # Check MCP.1
    # For the set of protection entity the interference value is calculated 
    # using both iap and aggregate interference reference models, checked against
    # the comparison value 
    self.performIapAndAggregateInterferenceCheck(protected_entity_records,
              fad_uut_object, fad_test_harnesses_objects, cbsd_records)

    # Step 13 : Configure SAS Harness with FAD,trigger FAD generation
    for test_harness, test_harness_data in zip(sas_test_harness_objects, iteration_content['sasTestHarnessData']):
      sas_test_harness_dump_records = [test_harness_data['cbsdRecords']]
      test_harness.writeFadRecords(sas_test_harness_dump_records)

    # Step 14,15 : Trigger Full Activty Dump and Pull FAD records from SAS UUT
    fad_uut_object = getFullActivityDumpSasUut(self._sas,
                                               self._sas_admin)

    # Step 16 : Trigger CPAS and wait for its completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 18,19,20 and 21 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
    cbsds_with_domain_proxies = []
    for domain_proxy_object in domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()
      cbsds_with_domain_proxies.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    # Step 22: Calculating the Aggregate interface and IAP reference model invoke. 
    cbsd_records = getFullActivityDumpSasTestHarness(cbsds_with_domain_proxies).getCbsdRecords()

    # Call Pre IAP model
    pre_iap_filtering.preIapReferenceModel(protected_entity_records,
                                      fad_uut_object, fad_test_harnesses_objects)
    # For the set of protection entity the interference value is calculated
    # using both iap and aggregate interference reference models, checked against
    # the comparison value
    self.performIapAndAggregateInterferenceCheck(protected_entity_records,
                fad_uut_object, fad_test_harnesses_objects, cbsd_records)
   
    # Execute from Step23 to Step30 only for MCP testcase
    if test_type == 'MCP':
      self.executeMCPOnlyTestSteps(iteration_content, domain_proxy_objects)


  def executeMCPOnlyTestSteps(self, iteration_content, domain_proxy_objects):
    """Executes the steps from Step23 to Step30 for MCP testcase

    Args:
      iteration_content: A dictionary with multiple key-value pairs that contain iteration data
      domain_proxy_objects: Domain proxy objects
    """
    cbsds = []  #contain all CBSDs with authorized grants
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

    protected_entity_records = iteration_content['protectedEntities']
    # Creating FAD Object and Pull FAD records from SAS UUT
    fad_test_harnesses_objects = []
    sas_test_harness_objects = []
    if iteration_content['sasTestHarnessData']:
      fad_uut_object = getFullActivityDumpSasUut(self._sas,
                                              self._sas_admin)
    # Pull FAD from SAS Test Harnesses and fad objects are created for each SAS Test Harnesses
    for test_harness in sas_test_harness_objects:
      fad_test_harnesses_objects.append(getFullActivityDumpSasTestHarness(
                           test_harness.getSasTestHarnessInterface()))

    # Step 25,26,27 and 28 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
    for domain_proxy_object in domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()
      cbsds.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    cbsd_records = getFullActivityDumpSasTestHarness(cbsds).getCbsdRecords()
    # Call Pre IAP model
    pre_iap_filtering.preIapReferenceModel(protected_entity_records,
                                       fad_uut_object, fad_test_harnesses_objects)
    # For the set of protection entity the interference value is calculated
    # using both iap and aggregate interference reference models, checked against
    # the comparison value
    self.performIapAndAggregateInterferenceCheck(protected_entity_records,
              fad_uut_object, fad_test_harnesses_objects, cbsd_records)

   # check MCP.1 DPA
   # TODO: need to invoke the DPA checkperformHeartbeatAndUpdateGrants

