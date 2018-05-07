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
import time
import os
from reference_models.common import mpool
from functools import partial
import sas
import sas_testcase
import test_harness_objects
from full_activity_dump import FullActivityDump
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
from util import winnforum_testcase, configurable_testcase, getCertificateFingerprint, writeConfig, \
        loadConfig, makePpaAndPalRecordsConsistent
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
        generatePpaRecords
from reference_models.pre_iap_filtering import pre_iap_filtering
from reference_models.iap import iap
from reference_models.interference import aggregate_interference, interference


DELTA_IAP = 1 # Threshold value in dBm

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
    # Load GWPZ Record
    gwpz_record_1 = json.load(
      open(os.path.join('testcases', 'mcp_testdata', 'gwpz_record_0.json')))

    # Load FSS record
    fss_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))

    # Load ESC record
    esc_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))

    esc_record_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'esc_sensor_record_1.json')))
    # Load PPA and PAL record
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
        'fssRecords': [fss_record_1],
        'escRecords': [esc_record_2]
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
    
    sas_config = {
        'serverCert': os.path.join('certs', 'server.cert'),
        'serverKey': os.path.join('certs', 'server.key')}

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
        'sasConfig': sas_config,
        'iterationData': [iteration0_config, iteration1_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': os.path.join('certs', 'domain_proxy.cert'),
                                'key': os.path.join('certs', 'domain_proxy.key')},
                               {'cert': os.path.join('certs', 'domain_proxy_1.cert'),
                                'key': os.path.join('certs', 'domain_proxy_1.key')}]
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
   
    sas_info = config['sasConfig']

    # Load conditionals
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    for domain_proxy in config['domainProxyConfigs']:
      domain_proxy_objects.append(test_harness_objects.DomainProxy(self, domain_proxy['cert'],\
                                                                   domain_proxy['key']
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
      self.executeSingleMCPIteration(test_type, iteration_content, sas_info, sas_test_harness_objects, 
                                     domain_proxy_objects)
    
    # Stopping Test harness servers
    for test_harness in sas_test_harness_objects:
      test_harness.shutdown()
      del test_harness

  def performIapAndAggregateInterferenceCheck(self, protected_entities, sas_uut_fad_object,
                                      sas_th_fad_objects, dp_records):
    """Compare the interference calculated using iap and aggregate reference models.

    Args:
      protected_entities : List of entity records needed to be protected 
      sas_uut_fad_object : FAD object from SAS UUT
      sas_th_fad_objects : a list of FAD objects from SAS Test Harness
      dp_objects : List of DP objects registered to the SAS.

    Returns:
      True or False based on the comparison of Aggregate Interference values
      against the two reference models
    """
    ppa_ap_iap_ref_values_list = []
    gwpz_ap_iap_ref_values_list = []
    fss_blocking_ap_iap_ref_values_list = []
    fss_cochannel_ap_iap_ref_values_list = []
    esc_ap_iap_ref_values_list = []
  
    # Calculate and compare the interference value for PPA protected entity 
    if 'ppaRecords' in protected_entities:
      for ppa_record in protected_entities['ppaRecords']:
        pal_records = protected_entities['palRecords']
        # Call iap reference model for ppa
        ppa_ap_iap_ref_values = iap.\
             performIapForPpa(ppa_record, sas_uut_fad_object, sas_th_fad_objects, pal_records)
        # Call aggregate interference reference model for ppa
        ppa_aggr_interference = aggregate_interference.\
             calculateAggregateInterferenceForPpa(ppa_record, pal_records, dp_records)
        # Storing the iap results for future comparison 
        ppa_result = {ppa_record['id']:ppa_ap_iap_ref_values}
        ppa_ap_iap_ref_values_list.append(ppa_result)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(ppa_ap_iap_ref_values, ppa_aggr_interference, 'area')

    # Calculate and compare the interference value for GWPZ protected entity
    if 'gwpzRecords' in protected_entities:
      for gwpz_record in protected_entities['gwpzRecords']:
        # Call iap reference model for gwpz
        gwpz_ap_iap_ref_values = iap.\
            performIapForGwpz(gwpz_record, sas_uut_fad_object, sas_th_fad_objects)
        # Call aggregate interference reference model for gwpz
        gwpz_aggr_interference = aggregate_interference.\
            calculateAggregateInterferenceForGwpz(gwpz_record, dp_records)
        # Storing the iap results for future comparison
        gwpz_result = {gwpz_record['id']:gwpz_ap_iap_ref_values}
        gwpz_ap_iap_ref_values_list.append(gwpz_result)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(gwpz_ap_iap_ref_values, gwpz_aggr_interference, 'area')
    
    # Calculate and compare the interference value for FSS protected point
    if 'fssRecords' in protected_entities:
      for fss_record in protected_entities['fssRecords']:
        fss_freq_range = fss_record['record']['deploymentParam'][0]\
            ['operationParam']['operationFrequencyRange']
        fss_low_freq = fss_freq_range['lowFrequency']
        fss_high_freq = fss_freq_range['highFrequency']
        fss_ttc_flag = fss_record['ttc']
        if (fss_low_freq >= interference.FSS_LOW_FREQ_HZ and 
                fss_low_freq < interference.CBRS_HIGH_FREQ_HZ):
          # Call IAP for FSS blocking and FSS cochannel
          fss_cochannel_ap_iap_ref_values = iap.\
              performIapForFssCochannel(fss_record, sas_uut_fad_object, sas_th_fad_objects)
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, sas_uut_fad_object, sas_th_fad_objects)
          # Call Aggregate interference for FSS blocking ad FSS cochannel
          fss_cochannel_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssCochannel(fss_record, dp_records)
          fss_blocking_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssBlocking(fss_record, dp_records)
          # Storing the iap results for future comparison
          fss_cochannel_result = {fss_record['record']['id']: fss_cochannel_ap_iap_ref_values}
          fss_blocking_result = {fss_record['record']['id']: fss_blocking_ap_iap_ref_values}
          fss_cochannel_ap_iap_ref_values_list.append(fss_cochannel_result)
          fss_blocking_ap_iap_ref_values_list.append(fss_blocking_result)
          # Check and compare interference for FSS entity
          self.compareIapAndAggregateResults(fss_cochannel_ap_iap_ref_values, fss_cochannel_aggr_interference,'point')
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values, fss_blocking_aggr_interference,'point')
        elif (fss_low_freq >= interference.FSS_TTC_LOW_FREQ_HZ and 
                 fss_high_freq <= interference.FSS_TTC_HIGH_FREQ_HZ and 
                 fss_ttc_flag is True):
          # Call iap reference model for FSS blocking
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, sas_uut_fad_object, sas_th_fad_objects)
          # Call aggregate interference model for FSS blocking
          fss_blocking_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssBlocking(fss_record, dp_records)
          # Storing the iap results for future comparison 
          fss_blocking_result = {fss_record['id']: fss_blocking_ap_iap_ref_values}
          fss_blocking_ap_iap_ref_values_list.append(fss_blocking_result)
          # Compare the interference values calculated from both models
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values,\
              fss_blocking_aggr_interference, 'point')
    
    # Calculate and compare the interference value for ESC protected point 
    if 'escRecords' in protected_entities:
      for esc_record in protected_entities['escRecords']:
        # Call iap reference model for esc
        esc_ap_iap_ref_values = iap.\
            performIapForEsc(esc_record, sas_uut_fad_object, sas_th_fad_objects)
        # Call aggregate interference model for esc 
        esc_aggr_interference = aggregate_interference.\
            calculateAggregateInterferenceForEsc(esc_record, dp_records)
        # Storing the iap results for future comparison
        esc_result = {esc_record['id']:esc_ap_iap_ref_values}
        esc_ap_iap_ref_values_list.append(esc_result)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(esc_ap_iap_ref_values, esc_aggr_interference, 'point')
     
    iap_results = [{'ppaRecords':ppa_ap_iap_ref_values_list}, {'gwpzRecords':gwpz_ap_iap_ref_values_list},
                {'fssRecords':[{'fss_blocking':fss_blocking_ap_iap_ref_values_list},
                {'fss_cochannel' : fss_cochannel_ap_iap_ref_values_list}]},
                {'escRecords':esc_ap_iap_ref_values_list}]
    return iap_results


  def compareIapAndAggregateResults(self, ap_iap_ref_values, aggr_interference, entity_type):
    """Verify aggregate interference is less than or equal to ap_iap_ref value calculated 
    by IAP model plus a delta for each FSS and ESC sensor protected point, and for at
    least 95% of the protected points of each PPA and GWPZ.

    Args:
      ap_iap_ref_values : Aggregate interference output calculated from IAP 
                             reference model 
      aggr_interference : Aggregate interference output calculated from Aggregate
                          Inteference reference model 
      entity_type : To identify its a point protected or area protected entity 

    Returns:
       Pass or Fail based on the comparison of the values within range
    """
    iter_cnt = 0 # Variable to count the number of interference entries
    match_cnt = 0 # Variable to count the number of matching interference entries
    iap_margin_lin = interference.dbToLinear(DELTA_IAP)  

    for lat_dict in ap_iap_ref_values:
      long_dict = ap_iap_ref_values[lat_dict]
      long_dict_aggr = aggr_interference[lat_dict]
      self.assertEqual(len(long_dict), len(long_dict_aggr))
      for interf in long_dict:
        for interf_iap, aggr in zip(long_dict[interf], long_dict_aggr[interf]):
          iter_cnt += 1
          # The aggregate interference should be less than 
          # or equal to the iap interference + iap margin threshold
          if aggr <= interf_iap * iap_margin_lin:
            match_cnt += 1
       
    if entity_type == 'area':
      # For protected areas the match of total interference values 
      # should be greater than or equal to 95 percentile
      self.assertGreaterEqual((100.0 * match_cnt) / iter_cnt, 95) 
    else:
      # For Protection points the comparison match should be 100 percentile
      self.assertEqual((100.0 * match_cnt) / iter_cnt, 100)


  def objectsToRecords(self, cbsd_objects):
    """Converts the cbsd FAD objects directly to the records

    Args:
      cbsd_objects : List of cbsd_objects 

    Returns:
      A list of CBSD_records by getting the registration and grant details 
    """

    cbsd_records = []
    # converting the object to records 
    for cbsds in cbsd_objects:
      if type(cbsds) == list:
        for cbsd in cbsds:
          # Get the registration details of the cbsd 
          cbsd_record = cbsd.getRegistrationRequest()
          # Get the grant objects present in the respective cbsds
          grant_list = cbsd.getAuthorizedGrants()
          if type(grant_list) == list:
            for grant in grant_list:
              grant_records = []
              # Get the grant request details using the grant objects
              grant_record = grant.getGrantRequest()
              grant_records.append(grant_record)
              # create the record using the registration and grant details
              cbsd_records.append({
                'registration':cbsd_record,
                'grants': grant_records
                })
          else:
             grant_record = grant.getGrantRequest()
          # create the record using the registration and grant details
          cbsd_records.append({
             'registration':cbsd_record,
             'grants': grant_records
               })
      else:
        cbsd_record = cbsd.getRegistrationRequest()
        grant_record = grant.getGrantRequest()
      # append all the cbsd records created from the objects 
      cbsd_records.append({
        'registration':cbsd_record,
        'grants': grant_records
        })
    return cbsd_records

  def executeSingleMCPIteration(self, test_type, iteration_content, sas_info, sas_test_harness_objects,
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
        self._sas_admin.InjectFss({'record': fss_record})

    if 'gwpzRecords' in protected_entity_records:
      for gwpz_record in protected_entity_records['gwpzRecords']:
        self._sas_admin.InjectWisp({'record': gwpz_record})

    if 'escRecords' in protected_entity_records:
      for esc_record in protected_entity_records['escRecords']:
        self._sas_admin.InjectEscSensorDataRecord({'record': esc_record})
    if 'palRecords' in protected_entity_records:
      for pal_record in protected_entity_records['palRecords']:
        self._sas_admin.InjectPalDatabaseRecord({'record': pal_record})

    if 'ppaRecords' in protected_entity_records:
      for ppa_record in protected_entity_records['ppaRecords']:
        self._sas_admin.InjectZoneData({'record': ppa_record})


    # Step 6,7 : Creating FAD Object and Pull FAD records from SAS UUT
    fad_test_harnesses_objects = []
    
    if iteration_content['sasTestHarnessData']:
      fad_uut_object = getFullActivityDumpSasUut(self._sas,
                                                 self._sas_admin,
                                                 sas_info['serverCert'],
                                                 sas_info['serverKey'])

      # Pull FAD from SAS Test Harnesses and fad objects are created for each SAS Test Harnesses
      for test_harness in sas_test_harness_objects:
        fad_test_harnesses_objects.append(getFullActivityDumpSasTestHarness(
                                          test_harness.getSasTestHarnessInterface()))

    # Step 8 : Trigger CPAS and wait until completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9 : Invoke IAP reference model - The IAP calculation will be done as a part of Step 12
    # Step 10 : DP Test Harness Register N(2,k)CBSDs with SAS UUT
    # Use DP objects to register CBSDs
    dp_objects=[] #contain all CBSDs with authorized grants 
    
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
      dp_objects.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())
    
    dp_records = self.objectsToRecords(dp_objects)
   
    # Call Pre IAP model
    pre_iap_filtering.preIapReferenceModel(protected_entity_records, 
                                   fad_uut_object, fad_test_harnesses_objects)

    # Step 12 : Invoke IAP model and Aggregate Interference Model
    # Check MCP.1
    # For the set of protected entity the interference value is calculated 
    # using both iap and aggregate interference reference models, checked against
    # the comparison value 

   
    self.performIapAndAggregateInterferenceCheck(protected_entity_records,
              fad_uut_object, fad_test_harnesses_objects, dp_records)
    

    # Step 13 : Configure SAS Harness with FAD,trigger FAD generation
    for test_harness, test_harness_data in zip(sas_test_harness_objects, iteration_content['sasTestHarnessData']):
      sas_test_harness_dump_records = [test_harness_data['cbsdRecords']]
      test_harness.writeFadRecords(sas_test_harness_dump_records)
    
    # Step 14,15 : Trigger Full Activty Dump and Pull FAD records from SAS UUT
    fad_uut_object = getFullActivityDumpSasUut(self._sas, 
                                            self._sas_admin,
                                            sas_info['serverCert'],
                                            sas_info['serverKey'])

    # Step 16 : Trigger CPAS and wait for its completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    # Step 17 : Call IAP reference model - IAP calculations will be done as a part of Step 22

    # Step 18,19,20 and 21 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
    cbsds_with_domain_proxies = []
    for domain_proxy_object in domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()
      cbsds_with_domain_proxies.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    # Step 22: Calculating the Aggregate interface and IAP reference model invoke. 
    dp_records = self.objectsToRecords(cbsds_with_domain_proxies)

    # Call Pre IAP model
    pre_iap_filtering.preIapReferenceModel(protected_entity_records,
                                      fad_uut_object, fad_test_harnesses_objects)
    # For the set of protected entity the interference value is calculated
    # using both iap and aggregate interference reference models, checked against
    # the comparison value 
    
    iap_results = self.performIapAndAggregateInterferenceCheck(protected_entity_records,
                fad_uut_object, fad_test_harnesses_objects, dp_records)
   
    # Execute from Step23 to Step30 only for MCP testcase
    if test_type == 'MCP':
      self.executeMCPOnlyTestSteps(iteration_content, domain_proxy_objects, iap_results)



  def executeMCPOnlyTestSteps(self, iteration_content, domain_proxy_objects, iap_results):
    """Executes the steps from Step23 to Step30 for MCP testcase

    Args:
      iteration_content: A dictionary with multiple key-value pairs that contain iteration data
      domain_proxy_objects: Domain proxy objects
    """
    dp_objects = []  #contain all DPs with authorized grants
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

    # Step 25,26,27 and 28 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grants 
    for domain_proxy_object in domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()
      dp_objects.append(domain_proxy_object.getCbsdsWithAtLeastOneAuthorizedGrant())

    dp_records = self.objectsToRecords(dp_objects)

    # For the set of protected entity the interference value is calculated
    # using aggregate interference reference model and checked against
    # stored iap reference model results
   
   
    for protected_entity in protected_entity_records:
      # For ppa entity calculate the aggregate interference and compare it against the 
      # iap reference model values stored in previous iteration 
      if 'ppaRecords' in protected_entity:
        pal_records = protected_entity_records['palRecords']
        for ppa_record in protected_entity_records['ppaRecords']:
          ppa_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForPpa(ppa_record, pal_records, dp_records)
          for entity in iap_results:
            if 'ppaRecords' in entity:
              for record in entity['ppaRecords']:
                # Compare the stored iap_ref and calculated aggregate interference values
                self.compareIapAndAggregateResults(record[str(ppa_record['id'])],
                                                  ppa_aggr_interference,'area')

      if 'gwpzRecords' in protected_entity:
        # For gwpz  entity calculate the aggregate interference and compare it against the 
        # iap reference model values stored in previous iteration
        for gwpz_record in protected_entity_records['gwpzRecords']:
          gwpz_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForGwpz(gwpz_record, dp_records)
          for entity in iap_results:
            if 'gwpzRecords' in entity:
              for record in entity['gwpzRecords']:
                # Compare the stored iap_ref and calculated aggregate interference values
                self.compareIapAndAggregateResults(record[str(gwpz_record['id'])],
                                                 gwpz_aggr_interference, 'area')
     
      if 'fssRecords' in protected_entity:
        # For FSS  entity calculate the aggregate interference and compare it against the 
        # iap reference model values stored in previous iteration
        for fss_record in protected_entity_records['fssRecords']:
          fss_freq_range = fss_record['record']['deploymentParam'][0]\
              ['operationParam']['operationFrequencyRange']
          fss_low_freq = fss_freq_range['lowFrequency']
          fss_high_freq = fss_freq_range['highFrequency']
          fss_ttc_flag = fss_record['ttc']
          if (fss_low_freq >= interference.FSS_LOW_FREQ_HZ and 
              fss_low_freq < interference.CBRS_HIGH_FREQ_HZ):
            # Call aggregate for FSS blocking and FSS cochannel 
            fss_cochannel_aggr_interference = aggregate_interference.\
                calculateAggregateInterferenceForFssCochannel(fss_record, dp_records)
            fss_blocking_aggr_interference = aggregate_interference.\
                calculateAggregateInterferenceForFssBlocking(fss_record, dp_records)
            for entity in iap_results:
              if 'fssRecords' in entity:
                for types in entity['fssRecords']:
                  if 'fss_blocking' in types:
                    for record in types['fss_blocking']:
                      # Compare the stored iap_ref and calculated aggregate interference values
                      self.compareIapAndAggregateResults(record[str(fss_record['record']['id'])],
                                               fss_blocking_aggr_interference, 'point')
                  if 'fss_cochannel' in types:
                    for record in types['fss_cochannel']:
                      self.compareIapAndAggregateResults(record[str(fss_record['record']['id'])],
                                               fss_cochannel_aggr_interference, 'point')
          elif (fss_low_freq >= interference.FSS_TTC_LOW_FREQ_HZ and 
              fss_high_freq <= interference.FSS_TTC_HIGH_FREQ_HZ and 
              fss_ttc_flag is True):
            fss_blocking_aggr_interference = aggregate_interference.\
                calculateAggregateInterferenceForFssBlocking(fss_record, dp_records)
            for entity in iap_results:
              if 'fssRecords' in entity:
                for types in entity['fssRecords']:
                  if 'fss_blocking' in types:
                    for record in types['fss_blocking']:
                      # Compare the stored iap_ref and calculated aggregate interference values
                      self.compareIapAndAggregateResults(record[str(fss_record['record']['id'])],
                                                     fss_blocking_aggr_interference, 'point')

      if 'escRecords' in protected_entity:
        # For ESC entity calculate the aggregate interference and compare it against the
        # iap reference model values stored in previous iteration
        for esc_record in protected_entity_records['escRecords']:
          esc_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForEsc(esc_record, dp_records)
          for entity in iap_results:
            if 'escRecords' in entity:
              for record in entity['escRecords']:
                # Compare the stored iap_ref and calculated aggregate interference values
                self.compareIapAndAggregateResults(record[str(esc_record['id'])],
                                                 esc_aggr_interference, 'point')

   # check MCP.1 DPA
   # TODO: need to invoke the DPA checkperformHeartbeatAndUpdateGrants

