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

from concurrent.futures import ThreadPoolExecutor
import json
import numbers
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
        loadConfig, makePpaAndPalRecordsConsistent, getFqdnLocalhost, \
        getUnusedPort, getCertFilename
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
        generatePpaRecords, generateCbsdReferenceId
from reference_models.dpa import dpa_mgr
from reference_models.common import data
from reference_models.pre_iap_filtering import pre_iap_filtering
from reference_models.iap import iap
from reference_models.interference import aggregate_interference, interference
from reference_models.geo import utils as geoutils
from reference_models.geo import drive


DELTA_IAP = 1 # Threshold value in dBm
ONE_MHZ = 1000000


class McpXprCommonTestcase(sas_testcase.SasTestCase):

  def getEmptyCbsdRequestsWithDomainProxies(self, number_of_elements):
    empty_cbsd_records_domain_proxy = {
        'registrationRequests': [],
        'grantRequests': [],
        'conditionalRegistrationData': []
    }
    return [empty_cbsd_records_domain_proxy] * number_of_elements

  def checkMcpConfig(self, config, test_type):
    self.assertIn(test_type, ('MCP', 'xPR1', 'xPR2'))

    def checkFadConfiguration(fad_config):
      self.assertValidConfig(fad_config, {
          'cbsdRecords': list
      })

    self.assertValidConfig(
        config, {
            'initialCbsdRequestsWithDomainProxies': list,
            'initialCbsdRecords': list,
            'iterationData': list,
            'sasTestHarnessConfigs': list,
            'domainProxyConfigs': list
        }, {'dpas': dict})

    # Check each iteration's data.
    for iteration_data in config['iterationData']:
      self.assertValidConfig(
          iteration_data, {
              'cbsdRequestsWithDomainProxies': list,
              'cbsdRecords': list,
              'protectedEntities': dict,
              'dpaActivationList': list,
              'dpaDeactivationList': list,
              'sasTestHarnessData': list
          })

      self.assertEqual(
          len(iteration_data['cbsdRequestsWithDomainProxies']),
          len(config['domainProxyConfigs']),
          'Mismatch in the number of domain proxies and the configuration for this iteration: %s.'
          % str(iteration_data))
      self.assertEqual(
          len(config['initialCbsdRequestsWithDomainProxies']),
          len(config['domainProxyConfigs']),
          'Mismatch in the number of domain proxies and the configuration of initial CbsdRequests')
      for domain_proxy in iteration_data['cbsdRequestsWithDomainProxies']:
        self.assertValidConfig(
            domain_proxy, {
                'registrationRequests': list,
                'grantRequests': list,
                'conditionalRegistrationData': list
            })

      for cbsd_record in iteration_data['cbsdRecords']:
        self.assertValidConfig(
            cbsd_record, {
                'registrationRequest': dict,
                'grantRequest': dict,
                'clientCert': basestring,
                'clientKey': basestring
            }, {'conditionalRegistrationData': dict})
        if 'conditionalRegistrationData' in cbsd_record:
          self.assertIn('fccId', cbsd_record['conditionalRegistrationData'])
          self.assertIn('cbsdSerialNumber',
                        cbsd_record['conditionalRegistrationData'])

      self.assertValidConfig(
          iteration_data['protectedEntities'],
          {},
          {
              # All fields are optional.
              'palRecords': list,
              'ppaRecords': list,
              'escRecords': list,
              'gwpzRecords': list,
              'gwblRecords': list,
              'fssRecords': list,
          })
      if 'dpas' in config:
        for dpa in iteration_data['dpaActivationList'] + iteration_data['dpaDeactivationList']:
          self.assertValidConfig(dpa, {
              'dpaId': basestring,
              'frequencyRange': dict
          })

      self.assertEqual(
          len(iteration_data['sasTestHarnessData']),
          len(config['sasTestHarnessConfigs']),
          'Mismatch in the number of SAS test harnesses and the configuration for this iteration: %s.'
          % str(iteration_data))
      for sas_test_harness_data in iteration_data['sasTestHarnessData']:
        checkFadConfiguration(sas_test_harness_data)

    # Check SAS test harnesses.
    for sas_test_harness_config in config['sasTestHarnessConfigs']:
      self.assertValidConfig(
          sas_test_harness_config, {
              'sasTestHarnessName': basestring,
              'hostName': basestring,
              'port': int,
              'serverCert': basestring,
              'serverKey': basestring,
              'caCert': basestring
          })

    # Check domain proxies.
    for domain_proxy_config in config['domainProxyConfigs']:
      self.assertValidConfig(domain_proxy_config, {
          'cert': basestring,
          'key': basestring
      })

    # Special xPR-only checks.
    if test_type == 'MCP':
      return

    # Max. 1 iteration.
    self.assertEqual(
        len(config['iterationData']), 1,
        'XPR test cases only have one iteration.')

    # No DPAs.
    if 'dpas' in config:
      self.assertEqual(
          len(config['dpas']), 0,
          'XPR does not permit the use of DPAs.')

    # Max. one protected entity.
    protected_entities = config['iterationData'][0]['protectedEntities']
    if 'ppaRecords' in protected_entities:
      self.assertTrue('palRecords' in protected_entities,
                      'Must define PAL records if a PPA is to be injected.')
      self.assertEqual(len(protected_entities.keys()), 2)
    else:
      self.assertEqual(
          len(protected_entities.keys()), 1,
          'Must define only one protected entity for an xPR test case.')

    if test_type == 'xPR1':
      # No SAS test harnesses.
      self.assertEqual(
          len(config['sasTestHarnessConfigs']), 0,
          'xPR.1 does not permit the use of SAS Test Harnesses.')

  def executeMcpTestSteps(self, config, test_type):
    """Execute all teststeps for MCP testcase and for xPR testcases till Step22

    Args:
      config: Testcase configuration
      test_type: A string which indicates the type of testcase to be invoked("MCP"/"xPR1"/"xPR2")
    """
    self.checkMcpConfig(config, test_type)

    # Initialize test-wide variables, and state variables.
    self.config = config
    self.active_dpas = []
    self.test_type = test_type
    self.sas_test_harness_objects = []
    self.domain_proxy_objects = []
    self.protected_entity_records = {}
    self.num_peer_sases = len(config['sasTestHarnessConfigs'])
    self.cpas_executor = ThreadPoolExecutor(max_workers=1)
    self.agg_interf_check_executor = ThreadPoolExecutor(max_workers=1)
    logging.info('Running test type "%s" with %d SAS test harnesses.',
                 self.test_type, self.num_peer_sases)
    self.sas_uut_fad = None
    self.test_harness_fads = []

    logging.info('Creating domain proxies.')
    for domain_proxy in config['domainProxyConfigs']:
      self.domain_proxy_objects.append(test_harness_objects.DomainProxy(
          self,
          domain_proxy['cert'],
          domain_proxy['key']))

    if test_type == 'MCP':
      # Step 1: Load DPAs
      logging.info('Step 1: load DPAs')
      self._sas_admin.TriggerLoadDpas()

      # Step 2: ESC informs SAS about inactive DPAs
      logging.info('Step 2: deactivate all DPAs')
      self._sas_admin.TriggerBulkDpaActivation({'activate': False})
    else:
      logging.info('Skipping steps 1 and 2 because this is an xPR test.')

    # Step 3: creates multiple SAS THs.
    logging.info('Step 3: create %d SAS test harnesses' % self.num_peer_sases)
    if self.num_peer_sases:
      for test_harness in config['sasTestHarnessConfigs']:
        logging.info('Creating SAS TH with config %s', test_harness)

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

        self.sas_test_harness_objects.append(sas_test_harness_object)

      # Set the cert/key to use when requesting FADs from SAS UUT.
      self.fad_cert = config['sasTestHarnessConfigs'][0]['serverCert']
      self.fad_key = config['sasTestHarnessConfigs'][0]['serverKey']

    # Step 4: Register + Grant.
    logging.info('Step 4: Register + Grant initial CBSDs.')
    self.registerAndGrantCbsds(config['initialCbsdRequestsWithDomainProxies'],
                               config['initialCbsdRecords'])

    # Step 5: Complete each iteration of the testcase.
    for iteration_number, iteration_content in enumerate(config['iterationData']):
      logging.info('Step 5: execute iteration number %d', iteration_number)
      # Execute steps for single iteration
      self.executeSingleMCPIteration(iteration_content)

    # Stop test harness servers.
    for test_harness in self.sas_test_harness_objects:
      test_harness.shutdown()
      del test_harness

    self.cpas_executor.shutdown()
    self.agg_interf_check_executor.shutdown()

  def executeSingleMCPIteration(self, iteration_content):
    """Executes the steps from Step 6 to [end] for MCP and XPR testcases

    Args:
      iteration_content: A dictionary with multiple key-value pairs that contain iteration data
    """
    # Step 6: Inject protected entities into UUT
    logging.info('Step 6: inject new protected entities into SAS UUT')
    if 'fssRecords' in iteration_content['protectedEntities']:
      logging.info('Injecting FSS records.')
      for index, fss_record in enumerate(iteration_content['protectedEntities']['fssRecords']):
        try:
          logging.info('Injecting FSS record #%d', index)
          self._sas_admin.InjectFss(fss_record)
        except Exception:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise

    if 'gwblRecords' in iteration_content['protectedEntities']:
      logging.info('Injecting GWBL records.')
      for index, gwbl_record in enumerate(iteration_content['protectedEntities']):
        try:
          logging.info('Injecting GWBL record #%d', index)
          self._sas_admin.InjectWisp(gwbl_record)
        except Exception:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise

    if 'gwpzRecords' in iteration_content['protectedEntities']:
      logging.info('Injecting GWPZ records.')
      for index, gwpz_record in enumerate(iteration_content['protectedEntities']['gwpzRecords']):
        try:
          logging.info('Injecting GWPZ record #%d', index)
          self._sas_admin.InjectWisp(gwpz_record)
        except Exception:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise
        grid_points = geoutils.GridPolygon(
            gwpz_record['zone']['features'][0]['geometry'], res_arcsec=1)
        gwpz_record['landCategory'] = drive.nlcd_driver.RegionNlcdVote(
            [(pt[1], pt[0]) for pt in grid_points])
        logging.info('Land category: %s', gwpz_record['landCategory'])

    if 'escRecords' in iteration_content['protectedEntities']:
      logging.info('Injecting ESC records.')
      for index, esc_record in enumerate(iteration_content['protectedEntities']['escRecords']):
        try:
          logging.info('Injecting ESC record #%d', index)
          self._sas_admin.InjectEscSensorDataRecord({'record': esc_record})
        except Exception:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise

    if 'palRecords' in iteration_content['protectedEntities']:
      logging.info('Injecting PAL records.')
      for index, pal_record in enumerate(iteration_content['protectedEntities']['palRecords']):
        try:
          logging.info('Injecting PAL record #%d', index)
          self._sas_admin.InjectPalDatabaseRecord(pal_record)
        except Exception:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise

    if 'ppaRecords' in iteration_content['protectedEntities']:
      logging.info('Injecting PPA records.')
      for index, ppa_record in enumerate(iteration_content['protectedEntities']['ppaRecords']):
        try:
          logging.info('Injecting PPA record #%d', index)
          self._sas_admin.InjectZoneData({'record': ppa_record})
        except Exception:
          logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
          raise

    for key in iteration_content['protectedEntities']:
      if not key in self.protected_entity_records:
        self.protected_entity_records[key] = iteration_content[
            'protectedEntities'][key]
      else:
        self.protected_entity_records[key].extend(
            iteration_content['protectedEntities'][key])

    # Steps 7, 8: Creating FAD Object and Pull FAD records from SAS UUT
    logging.info('Steps 7 + 8: retrieve FAD from SAS UUT.')
    if self.num_peer_sases:
      logging.info('Retrieving SAS UUT FAD.')
      self.sas_uut_fad = getFullActivityDumpSasUut(self._sas,
                                                 self._sas_admin,
                                                 self.fad_cert,
                                                 self.fad_key)
    # Step 9: load SAS test harnesses and have the main test harness retrieve
    # those FADs for use in the reference models.
    if self.num_peer_sases:
      # Configure SAS Test Harnesses with new FAD information.
      logging.info('Step 9: re-configuring SAS test harnesses.')
      for test_harness, test_harness_data in zip(
          self.sas_test_harness_objects,
          iteration_content['sasTestHarnessData']):
        test_harness.writeFadRecords([test_harness_data['cbsdRecords']])
        for cbsdIndex in range(len(test_harness_data['cbsdRecords'])):
            logging.info('Step 9a: adding PeerSAS fccIds to SAS UUT whitelisted fccIds.' + test_harness_data['cbsdRecords'][cbsdIndex]["registration"]["fccId"])
            self._sas_admin.InjectFccId({'fccId': test_harness_data['cbsdRecords'][cbsdIndex]["registration"]["fccId"]})

      # Pull FAD from SAS Test Harnesses; a FAD object is created for each SAS Test Harness.
      logging.info('Collecting SAS TH FADs.')
      self.test_harness_fads = []
      for test_harness in self.sas_test_harness_objects:
        self.test_harness_fads.append(
            getFullActivityDumpSasTestHarness(
                test_harness.getSasTestHarnessInterface()))

    # Step 10: Trigger CPAS and wait until completion.
    logging.info('Step 10: Triggering CPAS.')
    self.cpas = self.cpas_executor.submit(self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete)

    if self.num_peer_sases:
      # Step 11: Invoke IAP reference model
      logging.info('Step 11: Performing pre-IAP filtering.')
      pre_iap_filtering.preIapReferenceModel(self.protected_entity_records,
                                     self.sas_uut_fad, self.test_harness_fads)
      logging.info('Step 11: Performing IAP.')
      self.performIap()

    # Step 12: Invoke DPA ML reference model for currently-active and
    # will-be-active DPAs.
    logging.info('Step 12: invoke the DPA ML reference model.')
    self.dpa_managers = {}
    self.dpa_margins = {}
    for active_dpa in self.active_dpas + iteration_content['dpaActivationList']:
      dpa_config = self.config['dpas'][active_dpa['dpaId']]
      dpa = dpa_mgr.BuildDpa(active_dpa['dpaId'], dpa_config['points_builder'])
      low_freq_mhz = active_dpa['frequencyRange']['lowFrequency'] / ONE_MHZ
      high_freq_mhz = active_dpa['frequencyRange']['highFrequency'] / ONE_MHZ
      dpa.ResetFreqRange([(low_freq_mhz, high_freq_mhz)])
      if self.num_peer_sases:
        logging.info('Calculating  move list for DPA: %s', active_dpa)
        dpa.SetGrantsFromFad(self.sas_uut_fad, self.test_harness_fads)
        dpa.ComputeMoveLists()

      dpa_combined_id = '%s,%s,%s' % (
          active_dpa['dpaId'], active_dpa['frequencyRange']['lowFrequency'],
          active_dpa['frequencyRange']['highFrequency'])
      self.dpa_managers[dpa_combined_id] = dpa
      self.dpa_margins[dpa_combined_id] = dpa_config['movelistMargin']

    logging.info('Waiting for CPAS to complete (Started in step 10).')
    self.cpas.result()
    logging.info('CPAS started in step 10 complete.')

    # Steps 13, 14, 15, and 16: send heartbeat request for the grants,
    # relinquish the grant, grant request and heartbeat for new grants.
    logging.info('Steps 13 - 16: heartbeat, relinquish, grant, heartbeat.')
    for index, domain_proxy_object in enumerate(self.domain_proxy_objects):
      logging.info('Working on domain proxy %d.', index)
      domain_proxy_object.performHeartbeatAndUpdateGrants()

    # Steps 17, 18, and CHECK
    logging.info('Steps 17, 18, and CHECK: calculating reference DPA move list,'
                 ' performing DPA aggregate interference check and performing'
                 ' aggregate interference check.')
    self.performIapAndDpaChecks()

    # Step 19: DP Test Harnesses register N(2,k) CBSDs with SAS UUT.
    logging.info('Step 19: registering and granting new CBSDs.')
    self.registerAndGrantCbsds(
        iteration_content['cbsdRequestsWithDomainProxies'],
        iteration_content['cbsdRecords'])

    # Step 20: Send heartbeat request for all CBSDs managed by SAS UUT.
    logging.info('Step 20: heartbeating all CBSDs.')
    for index, domain_proxy_object in enumerate(self.domain_proxy_objects):
      logging.info('Heartbeating for domain proxy %d.', index)
      domain_proxy_object.heartbeatForAllActiveGrants()

    # Step 21: ESC Test harness deactivates previously-activated DPAs.
    logging.info('Step 21: activating and deactivating DPAs.')
    for dpa in iteration_content['dpaActivationList']:
      if dpa in self.active_dpas:
        logging.warning('DPA is already active, skipping activation: %s', dpa)
        continue
      logging.info('Activating: %s', dpa)
      self._sas_admin.TriggerDpaActivation(dpa)
      self.active_dpas.append(dpa)
    for dpa in iteration_content['dpaDeactivationList']:
      logging.info('Deactivating: %s', dpa)
      self._sas_admin.TriggerDpaDeactivation(dpa)
      self.active_dpas.remove(dpa)

    # Step 22: wait for 240 sec if any DPA is activated in Step 21, else 15 sec.
    logging.info('Step 22: waiting.')
    if iteration_content['dpaActivationList']:
      time.sleep(240)
    else:
      time.sleep(15)

    # Step 23: Send heartbeat request for all CBSDs managed by SAS UUT.
    logging.info('Step 23: heartbeating all CBSDs.')
    for index, domain_proxy_object in enumerate(self.domain_proxy_objects):
      logging.info('Heartbeating for domain proxy %d.', index)
      domain_proxy_object.heartbeatForAllActiveGrants()

    # Steps 24, 25, and CHECK
    logging.info('Steps 24, 25, and CHECK: calculating reference DPA move list,'
                 ' performing DPA aggregate interference check and performing'
                 ' aggregate interference check.')
    self.performIapAndDpaChecks()

  def performIapAndDpaChecks(self):
    """Checks aggregate interference to all protected entities and active DPAs.
    """
    # Check DPA movelist + Check IAP interference (can happen in parallel).
    self.aggregate_interference_check = self.agg_interf_check_executor.submit(self.performAggregateInterferenceCheck)
    # Get list of authorized grants, in the format required from DPA movelist checking.
    grant_info = data.getAuthorizedGrantsFromDomainProxies(self.domain_proxy_objects)
    # Calculate DPA movelist.
    for active_dpa in self.active_dpas:
      # Check SAS UUT authorized grants do not exceed allowed threshold as calculated by the DPA reference model.
      logging.info('CHECK: DPA aggregate interference check for DPA %s.',
                   active_dpa['dpaId'])
      dpa_combined_id = '%s,%s,%s' % (
          active_dpa['dpaId'], active_dpa['frequencyRange']['lowFrequency'],
          active_dpa['frequencyRange']['highFrequency'])
      dpa = self.dpa_managers[dpa_combined_id]
      self.assertTrue(dpa.CheckInterference(
          sas_uut_active_grants=grant_info,
          margin_db=self.dpa_margins[dpa_combined_id],
          do_abs_check_single_uut=(self.num_peer_sases==0)))
    logging.info('Waiting for aggregate interference check to complete')
    self.aggregate_interference_check.result()
    logging.info('Aggregate interference check is now COMPLETE.')

  def performIap(self):
    self.ppa_ap_iap_ref_values_list = []
    self.gwpz_ap_iap_ref_values_list = []
    self.fss_blocking_ap_iap_ref_values_list = []
    self.fss_cochannel_ap_iap_ref_values_list = []
    self.esc_ap_iap_ref_values_list = []

    # Calculate the interference value for all PPAs.
    if 'ppaRecords' in self.protected_entity_records:
      for ppa_record in self.protected_entity_records['ppaRecords']:
        pal_records = self.protected_entity_records['palRecords']
        # Call IAP reference model for PPA.
        logging.info('Calling the IAP reference model for PPA (%s) with PAL records (%s)', ppa_record, pal_records)
        ppa_ap_iap_ref_values = iap.performIapForPpa(
            ppa_record,
            self.sas_uut_fad,
            self.test_harness_fads,
            pal_records)
        # Store the IAP results for future comparison.
        logging.debug('IAP reference model results: %s' % str(ppa_ap_iap_ref_values))
        self.ppa_ap_iap_ref_values_list.append(ppa_ap_iap_ref_values)

    # Calculate the interference value for all GWPZs.
    if 'gwpzRecords' in self.protected_entity_records:
      for gwpz_record in self.protected_entity_records['gwpzRecords']:
        # Call IAP reference model for GWPZ.
        logging.info('Calling the IAP reference model for GWPZ (%s).', gwpz_record)
        gwpz_ap_iap_ref_values = iap.performIapForGwpz(
            gwpz_record,
            self.sas_uut_fad,
            self.test_harness_fads)
        # Store the IAP results for future comparison.
        logging.debug('IAP reference model results: %s' % str(gwpz_ap_iap_ref_values))
        self.gwpz_ap_iap_ref_values_list.append(gwpz_ap_iap_ref_values)

    # Calculate the interference value for all FSS sites.
    if 'fssRecords' in self.protected_entity_records:
      for fss_record in self.protected_entity_records['fssRecords']:
        fss_freq_range = fss_record['record']['deploymentParam'][0]\
            ['operationParam']['operationFrequencyRange']
        fss_low_freq = fss_freq_range['lowFrequency']
        fss_high_freq = fss_freq_range['highFrequency']
        fss_ttc_flag = fss_record['ttc']
        if (fss_low_freq >= interference.FSS_LOW_FREQ_HZ and
                fss_low_freq < interference.CBRS_HIGH_FREQ_HZ):
          # Call IAP for FSS blocking and FSS cochannel.
          logging.info('Calling the cochannel IAP reference model for FSS (%s).', fss_record)
          fss_cochannel_ap_iap_ref_values = iap.\
              performIapForFssCochannel(fss_record, self.sas_uut_fad, self.test_harness_fads)
          logging.debug('IAP reference model results: %s' % str(fss_cochannel_ap_iap_ref_values))
          logging.info('Calling the blocking IAP reference model for FSS (%s).', fss_record)
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, self.sas_uut_fad, self.test_harness_fads)
          logging.debug('IAP reference model results: %s' % str(fss_blocking_ap_iap_ref_values))
          # Store the IAP results for future comparison.
          self.fss_cochannel_ap_iap_ref_values_list.append(fss_cochannel_ap_iap_ref_values)
          self.fss_blocking_ap_iap_ref_values_list.append(fss_blocking_ap_iap_ref_values)
        elif (fss_low_freq >= interference.FSS_TTC_LOW_FREQ_HZ and
                 fss_high_freq <= interference.FSS_TTC_HIGH_FREQ_HZ and
                 fss_ttc_flag is True):
          # Call IAP reference model for FSS blocking.
          logging.info('Calling the blocking IAP reference model for FSS (%s).', fss_record)
          fss_blocking_ap_iap_ref_values = iap.\
              performIapForFssBlocking(fss_record, self.sas_uut_fad, self.test_harness_fads)
          logging.debug('IAP reference model results: %s' % str(fss_blocking_ap_iap_ref_values))
          # Store the IAP results for future comparison.
          self.fss_cochannel_ap_iap_ref_values_list.append(None)
          self.fss_blocking_ap_iap_ref_values_list.append(fss_blocking_ap_iap_ref_values)

    # Calculate the interference value for all ESCs.
    if 'escRecords' in self.protected_entity_records:
      for esc_record in self.protected_entity_records['escRecords']:
        # Call IAP reference model for ESC.
        logging.info('Calling the IAP reference model for ESC (%s).' % str(esc_record))
        esc_ap_iap_ref_values = iap.performIapForEsc(
          esc_record,
          self.sas_uut_fad,
          self.test_harness_fads)
        # Store the IAP results for future comparison.
        logging.debug('IAP reference model results: %s' % str(esc_ap_iap_ref_values))
        self.esc_ap_iap_ref_values_list.append(esc_ap_iap_ref_values)

  def performAggregateInterferenceCheck(self):
    authorized_grants = None
    if any(key in self.protected_entity_records
           for key in ['gwpzRecords', 'fssRecords', 'escRecords']):
      # Get Grant info for all CBSDs with grants from SAS UUT.
      authorized_grants = data.getAuthorizedGrantsFromDomainProxies(
          self.domain_proxy_objects)

    # Calculate and compare the interference value for PPA protected entity
    if 'ppaRecords' in self.protected_entity_records:
      for index, ppa_record in enumerate(self.protected_entity_records['ppaRecords']):
        pal_records = self.protected_entity_records['palRecords']
        # Get Grant info for all CBSDs with grants from SAS UUT that are not
        # part of the current ppa.
        logging.info('Checking aggregate interference for PPA (%s) with PAL records (%s)', ppa_record, pal_records)

        ppa_authorized_grants = data.getAuthorizedGrantsFromDomainProxies(
            self.domain_proxy_objects, ppa_record=ppa_record)
        # Call aggregate interference reference model for ppa
        ppa_aggr_interference = aggregate_interference.calculateAggregateInterferenceForPpa(
            ppa_record, pal_records, ppa_authorized_grants)
        ppa_ap_iap_ref_values = None
        if self.num_peer_sases > 0:
          ppa_ap_iap_ref_values = self.ppa_ap_iap_ref_values_list[index]
        else:
          ppa_ap_iap_ref_values = interference.dbToLinear(iap.THRESH_PPA_DBM_PER_IAPBW)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(ppa_ap_iap_ref_values, ppa_aggr_interference, 'area')


    # Calculate and compare the interference value for GWPZ protected entity
    if 'gwpzRecords' in self.protected_entity_records:
      for index, gwpz_record in enumerate(self.protected_entity_records['gwpzRecords']):
        logging.info('Checking aggregate interference for GWPZ (%s).', gwpz_record)
        # Call aggregate interference reference model for GWPZ.
        gwpz_aggr_interference = aggregate_interference.calculateAggregateInterferenceForGwpz(
            gwpz_record,
            authorized_grants)
        gwpz_ap_iap_ref_values = None
        if self.num_peer_sases > 0:
          gwpz_ap_iap_ref_values = self.gwpz_ap_iap_ref_values_list[index]
        else:
          gwpz_ap_iap_ref_values = interference.dbToLinear(iap.THRESH_GWPZ_DBM_PER_IAPBW)
        # Compare the interference values calculated from both models
        self.compareIapAndAggregateResults(gwpz_ap_iap_ref_values, gwpz_aggr_interference, 'area')

    # Calculate and compare the interference value for FSS site.
    if 'fssRecords' in self.protected_entity_records:
      for index, fss_record in enumerate(self.protected_entity_records['fssRecords']):
        logging.info('Checking aggregate interference for FSS (%s).', fss_record)
        fss_freq_range = fss_record['record']['deploymentParam'][0]\
            ['operationParam']['operationFrequencyRange']
        fss_low_freq = fss_freq_range['lowFrequency']
        fss_high_freq = fss_freq_range['highFrequency']
        fss_ttc_flag = fss_record['ttc']
        if (fss_low_freq >= interference.FSS_LOW_FREQ_HZ and
                fss_low_freq < interference.CBRS_HIGH_FREQ_HZ):
          # Call aggregate interference for FSS blocking ad FSS cochannel.
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
            fss_cochannel_ap_iap_ref_values = interference.dbToLinear(iap.THRESH_FSS_CO_CHANNEL_DBM_PER_IAPBW)
            fss_blocking_ap_iap_ref_values = interference.dbToLinear(iap.THRESH_FSS_BLOCKING_DBM_PER_RBW)
          # Check and compare interference for FSS entity
          logging.info('Checking cochannel.')
          self.compareIapAndAggregateResults(fss_cochannel_ap_iap_ref_values, fss_cochannel_aggr_interference,'point')
          logging.info('Checking blocking.')
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values, fss_blocking_aggr_interference,'point')
        elif (fss_low_freq >= interference.FSS_TTC_LOW_FREQ_HZ and
                 fss_high_freq <= interference.FSS_TTC_HIGH_FREQ_HZ and
                 fss_ttc_flag is True):
          # Call aggregate interference model for FSS blocking.
          fss_blocking_aggr_interference = aggregate_interference.\
              calculateAggregateInterferenceForFssBlocking(fss_record, authorized_grants)
          fss_blocking_ap_iap_ref_values = None
          if self.num_peer_sases > 0:
            fss_blocking_ap_iap_ref_values = self.fss_blocking_ap_iap_ref_values_list[index]
          else:
            fss_blocking_ap_iap_ref_values = interference.dbToLinear(iap.THRESH_FSS_BLOCKING_DBM_PER_RBW)
          # Compare the interference values calculated from both models
          logging.info('Checking blocking.')
          self.compareIapAndAggregateResults(fss_blocking_ap_iap_ref_values,\
              fss_blocking_aggr_interference, 'point')

    # Calculate and compare the interference value for ESC.
    if 'escRecords' in self.protected_entity_records:
      for index, esc_record in enumerate(self.protected_entity_records['escRecords']):
        logging.info('Checking aggregate interference for ESC (%s).', esc_record)
        # Call aggregate interference model for ESC.
        esc_aggr_interference = aggregate_interference.\
            calculateAggregateInterferenceForEsc(esc_record, authorized_grants)
        esc_ap_iap_ref_values = None
        if self.num_peer_sases > 0:
          esc_ap_iap_ref_values = self.esc_ap_iap_ref_values_list[index]
        else:
          esc_ap_iap_ref_values = interference.dbToLinear(iap.THRESH_ESC_DBM_PER_IAPBW)
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

    scalar = isinstance(ap_iap_ref_values, numbers.Number)

    logging.info('IAP aggr interference checking - Entity: %s Thresh: %s',
                 entity_type, str(ap_iap_ref_values) if scalar else 'from IAP')

    for lat_val, lat_dict in aggr_interference.iteritems():
      for long_val, interf_list in lat_dict.iteritems():
        if scalar:
          # iter produces a infinite generator of the scalar, as zip iterates
          # till one of the passed iterators is empty this will produce the same
          # result as a list of len(interf_list) with the scalar in every field,
          # but without having to construct the list.
          ref_interf_list = iter((lambda : ap_iap_ref_values), 1)
        else:
          ref_interf_list = ap_iap_ref_values[lat_val][long_val]
          self.assertEqual(len(interf_list), len(ref_interf_list))
        if entity_type == 'area':
          # Area entities must check that each point is entirely not interfered
          # with above the allowed threshold.
          iter_cnt += 1
          below_threshold = True
          list_index = 0
          logging.debug('Check lat %s long %s: %s',
                        lat_val, long_val, zip(interf_list, ref_interf_list))
          for interf, ref_interf in zip(interf_list, ref_interf_list):
            list_index += 1
            if interf > ref_interf * iap_margin_lin:
              below_threshold = False
              logging.info('Threshold exceeded for chan %d: interf=%s ref_interf=%s',
                           list_index, interf, ref_interf)
          if below_threshold:
            match_cnt += 1
        else:
          list_index = 0
          logging.debug('Check lat %s long %s: %s',
                        lat_val, long_val, zip(interf_list, ref_interf_list))
          for interf, ref_interf in zip(interf_list, ref_interf_list):
            iter_cnt += 1
            list_index += 1
            if interf <= ref_interf * iap_margin_lin:
              match_cnt += 1
            else:
              logging.info('Threshold exceeded for chan %d: interf=%s ref_interf=%s',
                           list_index, interf, ref_interf)

    # All types of protection must have at least one point.
    self.assertGreater(iter_cnt, 0, msg=common_strings.CONFIG_ERROR_SUSPECTED)
    logging.info('Protection type: "%s"; point count: %d; match count: %d.' % (entity_type, iter_cnt, match_cnt))

    if entity_type == 'area':
      # For protected areas the match of total interference values
      # should be greater than or equal to 95 percent.
      match_percentage = (100.0 * match_cnt) / iter_cnt
      self.assertGreaterEqual(
          match_percentage, 95,
          'Expected 95 percent of locations to be below the threshold but only %2.3f percent were.'
          % match_percentage)
    else:
      # For Protection points the comparison match should be 100 percent.
      self.assertEqual(
          match_cnt, iter_cnt,
          'Expected all constraints to be below the threshold but %d were not.' %
          (iter_cnt - match_cnt))

  def registerAndGrantCbsds(self, cbsd_requests_with_domain_proxy,
                            individual_cbsd_records):
    """Registers new CBSDs with existing domain proxies and new individual
       CBSDs. Sends a Grant request for each.
    """
    dp_index = 0
    for domain_proxy_object, cbsdRequestsWithDomainProxy in zip(
        self.domain_proxy_objects, cbsd_requests_with_domain_proxy):
      registration_requests = cbsdRequestsWithDomainProxy[
          'registrationRequests']
      grant_requests = cbsdRequestsWithDomainProxy['grantRequests']
      conditional_registration_data = cbsdRequestsWithDomainProxy[
          'conditionalRegistrationData']

      #  Initiation of Registration and Grant procedures for the CBSDs using domain proxies.
      logging.info('Registering and Granting CBSDs which use domain proxy %d.',
                   dp_index)
      dp_index += 1
      domain_proxy_object.registerCbsdsAndRequestGrants(
          registration_requests,
          grant_requests,
          conditional_registration_data=conditional_registration_data)

    # Register individual Cbsds(Domain Proxy with single CBSD)
    for cbsd_index, cbsd_record in enumerate(individual_cbsd_records):
      logging.info('Registering and Granting CBSD %d.', cbsd_index)
      proxy = test_harness_objects.DomainProxy(self, cbsd_record['clientCert'],
                                               cbsd_record['clientKey'])
      conditionalRegistrationData = [
          cbsd_record['conditionalRegistrationData']
      ] if 'conditionalRegistrationData' in cbsd_record else []
      proxy.registerCbsdsAndRequestGrants([cbsd_record['registrationRequest']],
                                          [cbsd_record['grantRequest']],
                                          conditionalRegistrationData)
      self.domain_proxy_objects.append(proxy)


class MultiConstraintProtectionTestcase(McpXprCommonTestcase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    self.ShutdownServers()

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
        'dpaId': 'East4',
        'frequencyRange': {'lowFrequency': 3550000000, 'highFrequency': 3650000000}
    }
    dpa_2 = {
        'dpaId': 'East5',
        'frequencyRange': {'lowFrequency': 3550000000, 'highFrequency': 3650000000}
    }
    dpa_3 = {
        'dpaId': 'East6',
        'frequencyRange': {'lowFrequency': 3550000000, 'highFrequency': 3650000000}
    }
    dpa_generic = {
      'East4': {
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
      },
      'East5': {
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
      },
      'East6': {
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
        'fssRecords': [fss_record_1]
    }

    # SAS Test Harnesses configurations,
    # Following configurations are for two SAS test harnesses for two iterations
    sas_test_harness_device_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    sas_test_harness_device_1['fccId'] = 'test_fcc_id_g'
    sas_test_harness_device_1['userId'] = 'test_user_id_g'

    sas_test_harness_device_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    sas_test_harness_device_2['fccId'] = 'test_fcc_id_h'
    sas_test_harness_device_2['userId'] = 'test_user_id_h'

    sas_test_harness_device_3 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    sas_test_harness_device_3['fccId'] = 'test_fcc_id_i'
    sas_test_harness_device_3['userId'] = 'test_user_id_i'

    sas_test_harness_device_4 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    sas_test_harness_device_4['fccId'] = 'test_fcc_id_j'
    sas_test_harness_device_4['userId'] = 'test_user_id_j'

    sas_test_harness_device_5 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_e.json')))
    sas_test_harness_device_5['fccId'] = 'test_fcc_id_k'
    sas_test_harness_device_5['userId'] = 'test_user_id_k'

    sas_test_harness_device_6 = json.load(
      open(os.path.join('testcases', 'testdata', 'device_f.json')))
    sas_test_harness_device_6['fccId'] = 'test_fcc_id_l'
    sas_test_harness_device_6['userId'] = 'test_user_id_l'

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

    # SAS Test Harnesses configuration
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert'),
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas_1.cert'),
        'serverKey': getCertFilename('sas_1.key'),
        'caCert': getCertFilename('ca.cert'),
    }

    # Create the actual config.
    iteration0_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_iteration_0_domain_proxy_0, cbsd_records_iteration_0_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_7,
            'grantRequest': grant_request_7,
            'clientCert': getCertFilename('device_g.cert'),
            'clientKey': getCertFilename('device_g.key')
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
            'clientCert': getCertFilename('device_h.cert'),
            'clientKey': getCertFilename('device_h.key')
        }],
        'protectedEntities': protected_entities_iteration_1,
        'dpaActivationList': [dpa_3],
        'dpaDeactivationList': [dpa_1],
        'sasTestHarnessData': [dump_records_iteration_1_sas_test_harness_0, dump_records_iteration_1_sas_test_harness_1]
    }
    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration0_config, iteration1_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': getCertFilename('domain_proxy.cert'),
                                'key': getCertFilename('domain_proxy.key')},
                               {'cert': getCertFilename('domain_proxy_1.cert'),
                                'key': getCertFilename('domain_proxy_1.key')}],
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
