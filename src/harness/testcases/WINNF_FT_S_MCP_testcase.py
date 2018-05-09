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
import logging
import sas
import sas_testcase
import test_harness_objects
from full_activity_dump import FullActivityDump
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
import common_strings
from util import winnforum_testcase, configurable_testcase, getCertificateFingerprint, writeConfig, \
        loadConfig, makePpaAndPalRecordsConsistent
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
        generatePpaRecords, generateCbsdReferenceId
from reference_models.dpa import dpa_mgr
from reference_models.common import data
from reference_models.pre_iap_filtering import pre_iap_filtering
from reference_models.iap import iap
from reference_models.interference import aggregate_interference, interference


DELTA_IAP = 1 # Threshold value in dBm
ONE_MHZ = 1000000

class McpXprCommonTestcase(sas_testcase.SasTestCase):

  def executeMcpTestSteps(self, config, test_type):
    """Execute all teststeps for MCP testcase and for xPR testcases till Step22

    Args:
      config: Testcase configuration
      test_type: A string which indicates the type of testcase to be invoked("MCP"/"XPR")
    """
    # Initialize test-wide variables, and state variables.
    self.config = config
    self.active_dpas = []
    self.test_type = test_type
    self.sas_test_harness_objects = []
    self.domain_proxy_objects = []
    self.protected_entity_records = []
    self.num_peer_sases = len(config['sasTestHarnessConfigs'])

    for domain_proxy in config['domainProxyConfigs']:
      self.domain_proxy_objects.append(test_harness_objects.DomainProxy(
          self,
          domain_proxy['cert'],
          domain_proxy['key']))
    # Step 1 : Load DPAs
    self._sas_admin.TriggerLoadDpas()

    # STEP 2 : ESC informs SAS about inactive DPA
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Step 3 : creates multiple SAS TH, and Load predefined FAD,CBSD
    if self.num_peer_sases:
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

        # Initialize content of test harness.
        if 'initialFad' in test_harness:
          sas_test_harness_object.writeFadRecords(test_harness['initialFad'])

        # informing SAS UUT about SAS Test Harnesses
        certificate_hash = getCertificateFingerprint(test_harness['serverCert'])
        self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                       'url': sas_test_harness_object.getBaseUrl()})

        self.sas_test_harness_objects.append(sas_test_harness_object)

      # Set the cert/key to use when requesting FADs from SAS UUT.
      self.fad_cert = config['sasTestHarnessConfigs'][0]['serverCert']
      self.fad_key = config['sasTestHarnessConfigs'][0]['serverKey']

    # Step 4: Complete each iteration of the testcase.
    for iteration_content in config['iterationData']:
      # Execute steps for single iteration
      self.executeSingleMCPIteration(iteration_content)

    # Stopping Test harness servers
    for test_harness in self.sas_test_harness_objects:
      test_harness.shutdown()
      del test_harness

  def executeSingleMCPIteration(self, iteration_content):
    """Executes the steps from Step1 to Step22 for MCP and XPR testcases

    Args:
      iteration_content: A dictionary with multiple key-value pairs that contain iteration data
    """
    # Step 5 : Inject IAP protected entities into UUT
    for key in self.iteration_content['protectedEntities']:
      if not key in self.protected_entity_records:
        self.protected_entity_records[key] = iteration_content['protectedEntities'][key]
      else:
        self.protected_entity_records[key].extend(iteration_content['protectedEntities'][key])
    self.protected_entity_records.extend(iteration_content['protectedEntities'])
    if 'fssRecords' in self.protected_entity_records:
      for fss_record in self.protected_entity_records['fssRecords']:
        try:
          self._sas_admin.InjectFss({'record': fss_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e

    if 'gwpzRecords' in self.protected_entity_records:
      for gwpz_record in self.protected_entity_records['gwpzRecords']:
        try:
          self._sas_admin.InjectWisp({'record': gwpz_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e
        # TODO: calculate and store the land category of the GWPZ

    if 'escRecords' in self.protected_entity_records:
      for esc_record in self.protected_entity_records['escRecords']:
        try:
          self._sas_admin.InjectEscSensorDataRecord({'record': esc_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e

    if 'palRecords' in self.protected_entity_records:
      for pal_record in self.protected_entity_records['palRecords']:
        try:
          self._sas_admin.InjectPalDatabaseRecord({'record': pal_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e


    if 'ppaRecords' in self.protected_entity_records:
      for ppa_record in self.protected_entity_records['ppaRecords']:
        try:
          self._sas_admin.InjectZoneData({'record': ppa_record})
        except Exception as e:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise e

    # Step 6,7 : Creating FAD Object and Pull FAD records from SAS UUT
    if self.num_peer_sases:
      self.sas_uut_fad = getFullActivityDumpSasUut(self._sas,
                                                 self._sas_admin,
                                                 self.fad_cert,
                                                 self.fad_key)

      # Pull FAD from SAS Test Harnesses and fad objects are created for each SAS Test Harnesses
      self.test_harness_fads = []
      for test_harness in self.sas_test_harness_objects:
        self.test_harness_fads.append(getFullActivityDumpSasTestHarness(
                                          test_harness.getSasTestHarnessInterface()))

    # Step 8 : Trigger CPAS and wait until completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    if self.num_peer_sases:
      # Step 9 : Invoke IAP reference model
      pre_iap_filtering.preIapReferenceModel(self.protected_entity_records,
                                     self.sas_uut_fad, self.test_harness_fads)
      self.performIap()
    # Step 10 : DP Test Harness Register N(2,k)CBSDs with SAS UUT

    for domain_proxy_object, cbsdRequestsWithDomainProxy in zip(self.domain_proxy_objects,
                                                                iteration_content['cbsdRequestsWithDomainProxies']):
      registration_requests = cbsdRequestsWithDomainProxy['registrationRequests']
      grant_requests = cbsdRequestsWithDomainProxy['grantRequests']
      conditional_registration_data = cbsdRequestsWithDomainProxy['conditionalRegistrationData']

      #  Initiation of Registration and Grant procedures for the configured records
      domain_proxy_object.registerCbsdsAndRequestGrants(registration_requests, grant_requests, conditional_registration_data=conditional_registration_data)

    # Register individual Cbsds(Domain Proxy with single CBSD)
    for cbsd_record in iteration_content['cbsdRecords']:
      proxy = test_harness_objects.DomainProxy(self, cbsd_record['clientCert'], cbsd_record['clientKey'])
      conditionalRegistrationData = [cbsd_record['conditionalRegistrationData']] if 'conditionalRegistrationData' in cbsd_record else []
      proxy.registerCbsdsAndRequestGrants([cbsd_record['registrationRequest']], [cbsd_record['grantRequest']], conditionalRegistrationData)
      self.domain_proxy_objects.append(proxy)

    # Step 11 : Send heartbeat request managed by SAS UUT
    for domain_proxy_object in self.domain_proxy_objects:
      domain_proxy_object.heartbeatForAllActiveGrants()

    # Step 12 : Invoke IAP model and Aggregate Interference Model
    # Check MCP.1
    # For the set of protected entity the interference value is calculated
    # using both iap and aggregate interference reference models, checked against
    # the comparison value
    self.performAggregateInterferenceCheck()

    if self.num_peer_sases:
      # Step 13 : Configure SAS Harness with FAD
      for test_harness, test_harness_data in zip(self.sas_test_harness_objects, iteration_content['sasTestHarnessData']):
        test_harness.writeFadRecords([test_harness_data['cbsdRecords']])

      # Step 14,15 : Trigger Full Activty Dump and Pull FAD records from SAS UUT
      self.sas_uut_fad = getFullActivityDumpSasUut(self._sas,
                                              self._sas_admin,
                                              self.fad_cert,
                                              self.fad_key)
      # Pull FAD from SAS Test Harnesses and fad objects are created for each SAS Test Harnesses
      self.test_harness_fads = []
      for test_harness in self.sas_test_harness_objects:
        self.test_harness_fads.append(getFullActivityDumpSasTestHarness(
                                          test_harness.getSasTestHarnessInterface()))

    # Step 16 : Trigger CPAS and wait for its completion
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    if self.num_peer_sases:
      # Step 17 : Call IAP reference model
      pre_iap_filtering.preIapReferenceModel(self.protected_entity_records,
                                     self.sas_uut_fad, self.test_harness_fads)
      self.performIap()

    # Step 18,19,20 and 21 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
    for domain_proxy_object in self.domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()

    # Step 22: Calculating the Aggregate interface and IAP reference model invoke.

    # For the set of protected entity the interference value is calculated
    # using both iap and aggregate interference reference models, checked against
    # the comparison value
    self.performAggregateInterferenceCheck()

    # Execute from Step23 to Step30 only for MCP testcase
    if self.test_type == 'MCP':
      self.executeMCPOnlyTestSteps(iteration_content)

  def executeMCPOnlyTestSteps(self, iteration_content):
    """Executes the steps from Step23 to Step30 for MCP testcase

    Args:
      iteration_content: A dictionary with multiple key-value pairs that contain iteration data
    """
    # Step 23: ESC Test harness enables DPA activations
    # deactivated the dpaDeactivationList DPA IDs
    for dpa in iteration_content['dpaActivationList']:
      self._sas_admin.TriggerDpaDeactivation(dpa)
      self.active_dpas.append(dpa)

    # activated the dpaActivationList DPA IDs
    # step 24: wait for 240 sec if DPA is activated in step 23 else 15 sec
    for dpa in iteration_content['dpaActivationList']:
      self._sas_admin.TriggerDpaActivation(dpa)
      self.active_dpas.remove(dpa)
    if iteration_content['dpaActivationList']:
      time.sleep(240)
    else:
      time.sleep(15)

    # Step 25,26,27 and 28 :
    # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grants
    for domain_proxy_object in self.domain_proxy_objects:
      domain_proxy_object.performHeartbeatAndUpdateGrants()

    # Step 29: Check DPA movelist.
    # Get list of authorized grants, in the format required from DPA movelist checking.
    grant_info = data.getAuthorizedGrantsFromDomainProxies(self.domain_proxy_objects)
    # Calculate DPA movelist.
    for active_dpa in self.active_dpas:
      dpa_config = self.config['dpas'][active_dpa['dpaId']]
      dpa = dpa_mgr.BuildDpa(active_dpa['dpaId'], dpa_config['points_builder'])
      dpa.SetGrantsFromFad(self.sas_uut_fad, self.test_harness_fads)
      dpa.ComputeMoveLists()
      # Check SAS UUT authorized grants do not exceed allowed threshold as calculated by the DPA reference model.
      low_freq_mhz = active_dpa['frequencyRange']['lowFrequency'] / ONE_MHZ
      high_freq_mhz = active_dpa['frequencyRange']['highFrequency'] / ONE_MHZ
      self.assertTrue(dpa.CheckInterference(
          sas_uut_active_grants=grant_info,
          margin_db=dpa_config['movelistMargin'],
          channel=(low_freq_mhz, high_freq_mhz),
          do_abs_check_single_uut=(self.num_peer_sases==0)))

    # Step 30: Check IAP interference.
    self.performAggregateInterferenceCheck()

  def performIap(self):
    self.ppa_ap_iap_ref_values_list = []
    self.gwpz_ap_iap_ref_values_list = []
    self.fss_blocking_ap_iap_ref_values_list = []
    self.fss_cochannel_ap_iap_ref_values_list = []
    self.esc_ap_iap_ref_values_list = []

    # Calculate and compare the interference value for PPA protected entity
    if 'ppaRecords' in self.protected_entity_records:
      for ppa_record in self.protected_entity_records['ppaRecords']:
        pal_records = self.protected_entity_records['palRecords']
        # Call iap reference model for ppa
        ppa_ap_iap_ref_values = iap.performIapForPpa(
            ppa_record,
            self.sas_uut_fad,
            self.test_harness_fads,
            pal_records)
        self.ppa_ap_iap_ref_values_list.append(ppa_ap_iap_ref_values)

    # Calculate and compare the interference value for GWPZ protected entity
    if 'gwpzRecords' in self.protected_entity_records:
      for gwpz_record in self.protected_entity_records['gwpzRecords']:
        # Call iap reference model for gwpz
        gwpz_ap_iap_ref_values = iap.performIapForGwpz(
            gwpz_record,
            self.sas_uut_fad,
            self.test_harness_fads)
        # Storing the iap results for future comparison
        self.gwpz_ap_iap_ref_values_list.append(gwpz_ap_iap_ref_values)

    # Calculate and compare the interference value for FSS protected point
    if 'fssRecords' in self.protected_entity_records:
      for fss_record in self.protected_entity_records['fssRecords']:
        fss_freq_range = fss_record['record']['deploymentParam'][0]\
            ['operationParam']['operationFrequencyRange']
        fss_low_freq = fss_freq_range['lowFrequency']
        fss_high_freq = fss_freq_range['highFrequency']
        fss_ttc_flag = fss_record['ttc']
        if (fss_low_freq >= interference.FSS_LOW_FREQ_HZ and
                fss_low_freq < interference.CBRS_HIGH_FREQ_HZ):
          # Call IAP for FSS blocking and FSS cochannel
          fss_cochannel_ap_iap_ref_values = iap.\
              performIapForFssCochannel(fss_record, self.sas_uut_fad, self.test_harness_fads)
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, self.sas_uut_fad, self.test_harness_fads)
          # Storing the iap results for future comparison
          self.fss_cochannel_ap_iap_ref_values_list.append(fss_cochannel_ap_iap_ref_values)
          self.fss_blocking_ap_iap_ref_values_list.append(fss_blocking_ap_iap_ref_values)
        elif (fss_low_freq >= interference.FSS_TTC_LOW_FREQ_HZ and
                 fss_high_freq <= interference.FSS_TTC_HIGH_FREQ_HZ and
                 fss_ttc_flag is True):
          # Call iap reference model for FSS blocking
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, self.sas_uut_fad, self.test_harness_fads)
          # Storing the iap results for future comparison
          self.fss_cochannel_ap_iap_ref_values_list.append(None)
          self.fss_blocking_ap_iap_ref_values_list.append(fss_blocking_ap_iap_ref_values)

    # Calculate and compare the interference value for ESC protected point
    if 'escRecords' in self.protected_entity_records:
      for esc_record in self.protected_entity_records['escRecords']:
        # Call iap reference model for esc
        esc_ap_iap_ref_values = iap.performIapForEsc(
          esc_record,
          self.sas_uut_fad,
          self.test_harness_fads)
        # Storing the iap results for future comparison
        self.esc_ap_iap_ref_values_list.append(esc_ap_iap_ref_values)

  def performAggregateInterferenceCheck(self):
    authorized_grants = data.getAuthorizedGrantsFromDomainProxies(self.domain_proxy_objects)

    # Calculate and compare the interference value for PPA protected entity
    if 'ppaRecords' in self.protected_entity_records:
      for index, ppa_record in enumerate(self.protected_entity_records['ppaRecords']):
        pal_records = self.protected_entity_records['palRecords']
        # Call aggregate interference reference model for ppa
        ppa_aggr_interference = aggregate_interference.calculateAggregateInterferenceForPpa(
            ppa_record,
            pal_records,
            authorized_grants)
        ppa_ap_iap_ref_values = None
        if self.num_peer_sases > 0:
          ppa_ap_iap_ref_values = self.ppa_ap_iap_ref_values_list[index]
        else:
          ppa_ap_iap_ref_values = [interference.dbToLinear(iap.THRESH_PPA_DBM_PER_RBW)] * len(ppa_aggr_interference)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(ppa_ap_iap_ref_values, ppa_aggr_interference, 'area')


    # Calculate and compare the interference value for GWPZ protected entity
    if 'gwpzRecords' in self.protected_entity_records:
      for index, gwpz_record in enumerate(self.protected_entity_records['gwpzRecords']):
        # Call aggregate interference reference model for gwpz
        gwpz_aggr_interference = aggregate_interference.calculateAggregateInterferenceForGwpz(
            gwpz_record,
            authorized_grants)
        gwpz_ap_iap_ref_values = None
        if self.num_peer_sases > 0:
          gwpz_ap_iap_ref_values = self.gwpz_ap_iap_ref_values_list[index]
        else:
          gwpz_ap_iap_ref_values = [interference.dbToLinear(iap.THRESH_GWPZ_DBM_PER_RBW)] * len(gwpz_aggr_interference)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(gwpz_ap_iap_ref_values, gwpz_aggr_interference, 'area')

    # Calculate and compare the interference value for FSS protected point
    if 'fssRecords' in self.protected_entity_records:
      for index, fss_record in enumerate(self.protected_entity_records['fssRecords']):
        fss_freq_range = fss_record['record']['deploymentParam'][0]\
            ['operationParam']['operationFrequencyRange']
        fss_low_freq = fss_freq_range['lowFrequency']
        fss_high_freq = fss_freq_range['highFrequency']
        fss_ttc_flag = fss_record['ttc']
        if (fss_low_freq >= interference.FSS_LOW_FREQ_HZ and
                fss_low_freq < interference.CBRS_HIGH_FREQ_HZ):
          # Call Aggregate interference for FSS blocking ad FSS cochannel
          fss_cochannel_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssCochannel(fss_record, authorized_grants)
          fss_blocking_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssBlocking(fss_record, authorized_grants)
          fss_cochannel_ap_iap_ref_values = None
          fss_blocking_ap_iap_ref_values = None
          if self.num_peer_sases > 0:
            fss_cochannel_ap_iap_ref_values = self.fss_cochannel_ap_iap_ref_values_list[index]
            fss_blocking_ap_iap_ref_values = self.fss_blocking_ap_iap_ref_values_list[index]
          else:
            fss_cochannel_ap_iap_ref_values = [interference.dbToLinear(iap.THRESH_FSS_CO_CHANNEL_DBM_PER_RBW)] * len(fss_cochannel_aggr_interference)
            fss_blocking_ap_iap_ref_values = [interference.dbToLinear(iap.THRESH_FSS_BLOCKING_DBM_PER_RBW)] * len(fss_blocking_aggr_interference)
          # Check and compare interference for FSS entity
          self.compareIapAndAggregateResults(fss_cochannel_ap_iap_ref_values, fss_cochannel_aggr_interference,'point')
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values, fss_blocking_aggr_interference,'point')
        elif (fss_low_freq >= interference.FSS_TTC_LOW_FREQ_HZ and
                 fss_high_freq <= interference.FSS_TTC_HIGH_FREQ_HZ and
                 fss_ttc_flag is True):
          # Call aggregate interference model for FSS blocking
          fss_blocking_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssBlocking(fss_record, authorized_grants)
          fss_blocking_ap_iap_ref_values = None
          if self.num_peer_sases > 0:
            fss_blocking_ap_iap_ref_values = self.fss_blocking_ap_iap_ref_values_list[index]
          else:
            fss_blocking_ap_iap_ref_values = [interference.dbToLinear(iap.THRESH_FSS_BLOCKING_DBM_PER_RBW)] * len(fss_blocking_aggr_interference)
          # Compare the interference values calculated from both models
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values,\
              fss_blocking_aggr_interference, 'point')

    # Calculate and compare the interference value for ESC protected point
    if 'escRecords' in self.protected_entity_records:
      for index, esc_record in enumerate(self.protected_entity_records['escRecords']):
        # Call aggregate interference model for esc
        esc_aggr_interference = aggregate_interference.\
            calculateAggregateInterferenceForEsc(esc_record, authorized_grants)
        esc_ap_iap_ref_values = None
        if self.num_peer_sases > 0:
            esc_ap_iap_ref_values = self.esc_ap_iap_ref_values_list[index]
        else:
          esc_ap_iap_ref_values = [interference.dbToLinear(iap.THRESH_ESC_DBM_PER_RBW)] * len(esc_aggr_interference)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(esc_ap_iap_ref_values, esc_aggr_interference, 'point')

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

    for lat_val, lat_dict in aggregate_interference.iteritems():
      for long_val, interf_list in lat_dict.iteritems():
        ref_interf_list = ap_iap_ref_values[lat_val][long_val]
        self.assertEqual(len(interf_list), len(ref_interf_list))
        for interf, ref_interf in zip(interf_list, ref_interf_list):
          iter_cnt += 1
          logging.info('IAP aggregate interference comparison: interf=%s ref_interf=%s' % (interf, ref_interf))
          if interf <= ref_interf * iap_margin_lin:
            match_cnt += 1

    if entity_type == 'area':
      # For protected areas the match of total interference values
      # should be greater than or equal to 95 percentile
      self.assertGreaterEqual((100.0 * match_cnt) / iter_cnt, 95)
    else:
      # For Protection points the comparison match should be 100 percentile
      self.assertEqual(match_cnt, iter_cnt)

class MultiConstraintProtectionTestcase(McpXprCommonTestcase):

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

    # Load PPA and PAL record
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
    dpa_generic = {
      'east_dpa_4': {
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
      },
      'east_dpa_5': {
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
      },
      'east_dpa_6': {
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
      }
    }

    # Registration and grant records for multiple iterations
    cbsd_records_iteration_0_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2],
        'grantRequests': [grant_request_1, grant_request_2],
        'conditionalRegistrationData': [conditionals_device_2]
    }
    cbsd_records_iteration_0_domain_proxy_1 = {
        'registrationRequests': [device_3],
        'grantRequests': [grant_request_3],
        'conditionalRegistrationData': []
    }
    cbsd_records_iteration_1_domain_proxy_0 = {
        'registrationRequests': [device_4],
        'grantRequests': [grant_request_4],
        'conditionalRegistrationData': [conditionals_device_4]
    }
    cbsd_records_iteration_1_domain_proxy_1 = {
        'registrationRequests': [device_5, device_6],
        'grantRequests': [grant_request_5, grant_request_6],
        'conditionalRegistrationData': []
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

    # Generate Cbsd FAD Records for SAS Test Harness 0, initial data.
    cbsd_fad_records_iteration_initial_sas_test_harness_0 = generateCbsdRecords([sas_test_harness_device_1], [[grant_request_1]])

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
        'caCert': os.path.join('certs', 'ca.cert'),
        'initialFad': [cbsd_fad_records_iteration_initial_sas_test_harness_0]
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
            'registrationRequest': device_8,
            'grantRequest': grant_request_8,
            'conditionalRegistrationData': conditionals_device_8,
            'clientCert': sas.GetDefaultDomainProxySSLCertPath(),
            'clientKey': sas.GetDefaultDomainProxySSLKeyPath()
        }],
        'protectedEntities': protected_entities_iteration_1,
        'dpaActivationList': [dpa_3],
        'dpaDeactivationList': [dpa_1],
        'sasTestHarnessData': [dump_records_iteration_1_sas_test_harness_0, dump_records_iteration_1_sas_test_harness_1]
    }
    config = {
        'iterationData': [iteration0_config, iteration1_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': os.path.join('certs', 'domain_proxy.cert'),
                                'key': os.path.join('certs', 'domain_proxy.key')},
                               {'cert': os.path.join('certs', 'domain_proxy_1.cert'),
                                'key': os.path.join('certs', 'domain_proxy_1.key')}],
        'dpas': dpa_generic
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_MCP_1_default_config)
  def test_WINNF_FT_S_MCP_1(self, config_filename):
    """SAS manages a mix of GAA and PAL Grants in 3550 MHz
       to 3700 MHz to protect configurable IAP-protected entities and DPAs
    """
    config = loadConfig(config_filename)
    # Invoke MCP test steps
    self.executeMcpTestSteps(config, 'MCP')
