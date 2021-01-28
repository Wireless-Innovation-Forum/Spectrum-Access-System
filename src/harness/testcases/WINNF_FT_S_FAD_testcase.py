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
""" Implementation of FAD test cases """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import hashlib
import json
import os
import logging

import six

import common_strings
import sas
import sas_testcase
from reference_models.geo import vincenty, utils
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generateCbsdReferenceId, generatePpaRecords
from util import configurable_testcase, writeConfig, loadConfig, \
  getCertificateFingerprint, getRandomLatLongInPolygon, makePpaAndPalRecordsConsistent, \
  compareDictWithUnorderedLists, winnforum_testcase, areTwoPpasEqual, \
  getFqdnLocalhost, getUnusedPort, getCertFilename, json_load

class FullActivityDumpTestcase(sas_testcase.SasTestCase):
  """ This class contains all FAD related tests mentioned in SAS TS  """

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    self.ShutdownServers()

  def assertEqualToDeviceOrPreloadedConditionalParam(self, attr_name, registration_request,\
                                                     preloaded_conditionals, record):
    """ this function checks the required parameter of dump with
        the required parameter of the registered Cbsd
        Args:
        attr_name: string represent the attribute name, we want to compare.
        record: the parent attribute that should contain the compared attribute in the dump record.
        preloaded_conditionals:the parent attribute that should contain the compared attribute in the preloaded conditional parameters.
        registration_request: the parent attribute that should contain the compared attribute in the registration request.

      Behavior: this function assert that the value in dump record equals to the value in
        preloaded conditional parameters or
        registration request(the priority is for the registration request value)
      """
    attr_value = registration_request[attr_name] if attr_name in registration_request\
      else preloaded_conditionals[attr_name]
    if attr_name in ['latitude', 'longitude']:
      self.assertTrue(abs(attr_value-record[attr_name])<1e-6)
    else:
      self.assertEqual(attr_value, record[attr_name])


  def assertCbsdRecord(self, registration_request, grant_request, grant_response, cbsd_dump_data, reg_conditional_data):
    """ this function assert that cbsds in the dump and their grants are the same as the data in registration_requestn, reg_conditional_data, grant_request
        Args:
        attr_name: string represent the attribute name, we want to compare.
        record: the parent attribute that should contain the compared attribute in the dump record.


        registration_request: array of dictionaries of the Cbsd registration request data.
        grant_request:  array of dictionaries of the grant request data
        grant_response: array of dictionaries of the grant response data
        cbsd_dump_data : array of dictionaries of the Cbsd dump records data
        preloaded_conditionals: array of dictionaries of preloaded conditional parameters of the Cbsds.
      """
    for index, device in enumerate(registration_request):
      reg_conditional_device_data_list = [reg for reg in \
          reg_conditional_data['registrationData'] if reg['fccId'] == device['fccId'] and \
          reg['cbsdSerialNumber'] == device['cbsdSerialNumber'] ]
      reg_conditional_device_data = {}
      if any(reg_conditional_device_data_list):
        self.assertEqual(1, len(reg_conditional_device_data_list))
        reg_conditional_device_data = reg_conditional_device_data_list[0]
      if 'installationParam' not in reg_conditional_device_data:
        reg_conditional_device_data['installationParam'] = {}
      if 'installationParam' not in device:
        device['installationParam'] = {}
      record_id = 'cbsd/' + device['fccId'] + '/' + hashlib.sha1(
          six.ensure_binary(device['cbsdSerialNumber'])).hexdigest()
      cbsd_record = [record['registration'] for record in cbsd_dump_data if record['id'] == record_id]
      self.assertEqual(1, len(cbsd_record))
      # required parameters
      self.assertEqual(device['fccId'], cbsd_record[0]['fccId'])

      air_interface = device['airInterface'] if 'airInterface' in device else\
        reg_conditional_device_data['airInterface']
      self.assertDictEqual(air_interface, cbsd_record[0]['airInterface'])

      self.assertEqualToDeviceOrPreloadedConditionalParam('cbsdCategory', \
        device, reg_conditional_device_data, cbsd_record[0])

      self.assertEqualToDeviceOrPreloadedConditionalParam('measCapability', \
        device, reg_conditional_device_data, cbsd_record[0])

      self.assertEqualToDeviceOrPreloadedConditionalParam('latitude', \
        device['installationParam'], reg_conditional_device_data\
        ['installationParam'], cbsd_record[0]['installationParam'])

      self.assertEqualToDeviceOrPreloadedConditionalParam('longitude', \
        device['installationParam'], reg_conditional_device_data\
        ['installationParam'], cbsd_record[0]['installationParam'])

      self.assertEqualToDeviceOrPreloadedConditionalParam('height', \
        device['installationParam'], reg_conditional_device_data\
        ['installationParam'], cbsd_record[0]['installationParam'])

      self.assertEqualToDeviceOrPreloadedConditionalParam('heightType', \
        device['installationParam'], reg_conditional_device_data\
        ['installationParam'], cbsd_record[0]['installationParam'])

      self.assertEqualToDeviceOrPreloadedConditionalParam('antennaGain', \
        device['installationParam'], reg_conditional_device_data\
        ['installationParam'], cbsd_record[0]['installationParam'])

      # parameters should exist in record if exist in device,\
      self.assertEqualToDeviceOrPreloadedConditionalParam('indoorDeployment', \
          device['installationParam'], reg_conditional_device_data['installationParam'],\
            cbsd_record[0]['installationParam'])
      # parameters should equal to device or to default value
      registered_antenna_azimuth = device['installationParam']['antennaAzimuth'] \
        if 'antennaAzimuth' in device['installationParam'] \
        else reg_conditional_device_data['installationParam']['antennaAzimuth'] \
        if 'antennaAzimuth' in reg_conditional_device_data['installationParam'] else None
      registered_antenna_beamwidth = device['installationParam']['antennaBeamwidth'] \
        if 'antennaBeamwidth' in device['installationParam'] \
        else reg_conditional_device_data['installationParam']['antennaBeamwidth'] \
        if 'antennaBeamwidth' in reg_conditional_device_data['installationParam'] else None
      dump_antenna_beamwidth = cbsd_record[0]['installationParam']['antennaBeamwidth'] \
        if 'antennaBeamwidth' in cbsd_record[0]['installationParam'] else None
      dump_antenna_azimuth = cbsd_record[0]['installationParam']['antennaAzimuth'] \
        if 'antennaAzimuth' in cbsd_record[0]['installationParam'] else None
      is_default_dump_beamwidth = dump_antenna_beamwidth == 360
      # beamwidth should be equal to registered value or default value
      if registered_antenna_beamwidth is None:
        self.assertTrue(is_default_dump_beamwidth)
      else:
        self.assertEqual(registered_antenna_beamwidth, dump_antenna_beamwidth)
      # if azimuth is not registered then the beamwidth in the dump should be the values of omni directional antenna
      if registered_antenna_azimuth is None:
        self.assertTrue(is_default_dump_beamwidth)
      else:
        self.assertEqual(registered_antenna_azimuth, dump_antenna_azimuth)

      # if callSign exist, it should have the same value as registered
      if 'callSign' in cbsd_record[0]:
        self.assertEqual(device['callSign'], cbsd_record[0]['callSign'])
      max_eirp_by_MHz = 37;
      if 'eirpCapability' in cbsd_record[0]:
        max_eirp_by_MHz = cbsd_record[0]['eirpCapability'] - 10

      # groupingParam if exists in device should exist with same value in record
      if 'groupingParam' in device:
        self.assertDictEqual(device['groupingParam'], \
                          cbsd_record[0]['groupingParam'])
      else:
        self.assertFalse('groupingParam' in cbsd_record[0])

      # Get grants by cbsd_id
      grants_of_cbsd = [cbsd['grants'] for cbsd in cbsd_dump_data if cbsd['id'] == record_id][0]
      self.assertEqual(1, len(grants_of_cbsd))
      self.assertTrue('id' in grants_of_cbsd[0])
      # Verify the Grant Of the Cbsd
      # check grant requestedOperationParam
      self.assertLessEqual(grants_of_cbsd[0]['requestedOperationParam']['maxEirp'],\
                    max_eirp_by_MHz)
      self.assertGreaterEqual(grants_of_cbsd[0]['requestedOperationParam']['maxEirp'],\
                    -137)
      self.assertGreaterEqual(grants_of_cbsd[0]['requestedOperationParam']['operationFrequencyRange']\
                        ['lowFrequency'], 3550000000)
      self.assertEqual(grants_of_cbsd[0]['requestedOperationParam']\
                            ['operationFrequencyRange']['lowFrequency'] % 5000000, 0)
      self.assertLessEqual( grants_of_cbsd[0]['requestedOperationParam']\
                        ['operationFrequencyRange']['highFrequency'], 3700000000)
      self.assertEqual( grants_of_cbsd[0]['requestedOperationParam']\
                        ['operationFrequencyRange']['highFrequency'] % 5000000, 0)
      # check grant OperationParam
      self.assertDictEqual( grants_of_cbsd[0]['operationParam'], \
                            grant_request[index]['operationParam'])

      self.assertEqual(grants_of_cbsd[0]['channelType'], grant_response[index]['channelType'])
      self.assertEqual( grants_of_cbsd[0]['grantExpireTime'], grant_response[index]['grantExpireTime'])
      self.assertFalse(grants_of_cbsd[0]['terminated'])

  def generate_FAD_1_default_config(self, filename):
    """Generates the WinnForum configuration for FAD.1"""
    # Load device info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    # Device #2 is Category B
    # pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam']
    }
    conditionals = {'registrationData': [conditionals_b]}
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']
    devices = [device_a, device_b, device_c]
    # Grants
    grants = []
    for index in range(len(devices)):
      grants.append(json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json')))
    # PPAs and PALs
    ppas = []
    pals = []
    pal_low_frequency = 3550000000.0
    pal_high_frequency = 3560000000.0
    pal_record = json_load(
        os.path.join('testcases', 'testdata', 'pal_record_0.json'))
    ppa_record = json_load(
        os.path.join('testcases', 'testdata', 'ppa_record_0.json'))
    ppa, pal = makePpaAndPalRecordsConsistent(ppa_record,
                                                            [pal_record],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            device_a['userId'])

    device_a['installationParam']['latitude'], device_a['installationParam'][
      'longitude'] = getRandomLatLongInPolygon(ppa)
    # Devices inside and part of the claimed PPA.
    # Contains the index of devices in the devices list.
    ppas.append({
          'ppaRecord': ppa,
          'ppaClusterList': [0]})
    pals.extend(pal)
    # ESC senosrs
    esc_sensors = []
    esc_sensors.append(json_load(
        os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
    # SAS test harness configuration
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': "certs/ca.cert"
    }
    sas_test_harness_1_config = {
      'sasTestHarnessName': 'SAS-TH-2',
      'hostName': getFqdnLocalhost(),
      'port': getUnusedPort(),
      'serverCert': getCertFilename('sas_1.cert'),
      'serverKey': getCertFilename('sas_1.key'),
      'caCert': getCertFilename('ca.cert')
    }
    config = {
      'registrationRequests': devices,
      'conditionalRegistrationData': conditionals,
      'grantRequests': grants,
      'ppaRecords': ppas,
      'palRecords': pals,
      'escSensorRecords' : esc_sensors,
      'sasTestHarnessConfigs': [sas_test_harness_0_config,
                                sas_test_harness_1_config]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FAD_1_default_config)
  def test_WINNF_FT_S_FAD_1(self, config_filename):
    """ This test verifies that a SAS UUT can successfully respond to a full
            activity dump request from a SAS Test Harness

		  SAS UUT approves the request and responds,
		  with correct content and format for both dump message and files
      """
    # load config file
    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequests']),
                      len(config['grantRequests']))
    # check that the config file contains consistent PAL&PPA data
    for index, grant in enumerate(config['grantRequests']):
      grant_frequency_range = grant['operationParam']['operationFrequencyRange']
      for ppa in config['ppaRecords']:
        if index in ppa['ppaClusterList']:
          frequency_ranges_of_pals = [{'frequencyRange' : {'lowFrequency' : pal['channelAssignment']['primaryAssignment']['lowFrequency'],\
            'highFrequency' : pal['channelAssignment']['primaryAssignment']['highFrequency']}} \
            for pal in config['palRecords'] if pal['palId'] in ppa['ppaRecord']['ppaInfo']['palId']]
          self.assertLessEqual(1, len(frequency_ranges_of_pals), 'Empty list of Frequency Ranges in the PAL config')
          low_freq = min([freq_range['frequencyRange']['lowFrequency'] for freq_range in frequency_ranges_of_pals])
          high_freq = max([freq_range['frequencyRange']['highFrequency'] for freq_range in frequency_ranges_of_pals])
          self.assertChannelsContainFrequencyRange(frequency_ranges_of_pals, {'lowFrequency': low_freq, 'highFrequency': high_freq })
          # check that the grant in config file is not mixed of PAL and GAA channels
          if low_freq <= grant_frequency_range['lowFrequency'] <= high_freq:
            self.assertLessEqual(grant_frequency_range['highFrequency'], high_freq, 'incorrect high frequency of the grant with index {0}, makes it GAA&PAL Mixed Grant'.format(index))
          if low_freq <= grant_frequency_range['highFrequency'] <= high_freq:
            self.assertGreaterEqual(grant_frequency_range['lowFrequency'], low_freq, 'incorrect low frequency of the grant with index {0}, makes it a GAA&PAL Mixed Grant'.format(index))
    for index, device  in enumerate(config['registrationRequests']):
      # check azimuth in the CBSD config, if the beamwidth is not 0 or 360 and the azimuth is not provided, CBSD registration may be rejected
      reg_conditional_device_data_list = [reg for reg in \
            config['conditionalRegistrationData']['registrationData'] if reg['fccId'] == device['fccId'] and \
            reg['cbsdSerialNumber'] == device['cbsdSerialNumber'] ]
      if len(reg_conditional_device_data_list) == 1:
        reg_conditional_installation_param = reg_conditional_device_data_list[0]['installationParam']
      elif len(reg_conditional_device_data_list) > 1:
        self.fail('invalid conditional Registration Data, multi conditional Registration configs for the cbsd with index: {0} '.format(index))
      else:
        reg_conditional_installation_param = {}
      registeration_antenna_azimuth = device['installationParam']['antennaAzimuth'] \
          if 'installationParam' in device and 'antennaAzimuth' in device['installationParam'] \
          else reg_conditional_installation_param['antennaAzimuth'] \
          if 'antennaAzimuth' in reg_conditional_installation_param else None
      registeration_antenna_beamwidth = device['installationParam']['antennaBeamwidth'] \
          if  'installationParam' in device and 'antennaBeamwidth' in device['installationParam'] \
          else reg_conditional_installation_param['antennaBeamwidth'] \
          if 'antennaBeamwidth' in reg_conditional_installation_param else None
      if registeration_antenna_beamwidth != None and registeration_antenna_beamwidth not in [0, 360]\
        and registeration_antenna_azimuth is None:
        self.fail('invalid config, missing azimuth value for CBSD config with index: {0} '.format(index))
      # inject FCC ID and User ID of CBSD
      self._sas_admin.InjectFccId({
          'fccId': device['fccId'],
          'fccMaxEirp': 47
      })
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Pre-load conditional registration data for N3 CBSDs.
    self._sas_admin.PreloadRegistrationData(
        config['conditionalRegistrationData'])

    # Register N1 CBSDs.
    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']

    # Check registration responses and get cbsd Id
    self.assertEqual(len(responses), len(config['registrationRequests']))
    cbsd_ids = []
    for response in responses:
      self.assertEqual(response['response']['responseCode'], 0)
      cbsd_ids.append(response['cbsdId'])
    # inject PALs and N2 PPAs
    ppa_ids = []
    for pal in config['palRecords']:
      try:
        self._sas_admin.InjectPalDatabaseRecord(pal)
      except Exception:
        logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
        raise
    for ppa in config['ppaRecords']:
      # fill the PPA cbsdReferenceIds with values according to admin testing API spec
      ppa['ppaRecord']['ppaInfo']['cbsdReferenceId'] = []
      for index in ppa['ppaClusterList']:
        ppa['ppaRecord']['ppaInfo']['cbsdReferenceId'].append(cbsd_ids[index])
      try:
        ppa_ids.append(self._sas_admin.InjectZoneData({'record': ppa['ppaRecord']}))
      except Exception:
        logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
        raise
      # re-fill the PPA cbsdReferenceIds with the values expected in the dump according to SAS-SAS TS
      ppa['ppaRecord']['ppaInfo']['cbsdReferenceId'] = []
      for index in ppa['ppaClusterList']:
        cbsd = config['registrationRequests'][index]
        ppa['ppaRecord']['ppaInfo']['cbsdReferenceId'].append(generateCbsdReferenceId(cbsd['fccId'], cbsd['cbsdSerialNumber']))
    grants = config['grantRequests']
    for index, response in enumerate(responses):
      self.assertEqual(response['response']['responseCode'], 0)
      grants[index]['cbsdId'] = response['cbsdId']
    # send grant request with N1 grants
    del responses
    grant_responses = self._sas.Grant({'grantRequest': grants})['grantResponse']
    # check grant response
    self.assertEqual(len(grant_responses), len(config['grantRequests']))
    for grant_response in grant_responses:
      self.assertEqual(grant_response['response']['responseCode'], 0)
    # inject N3 Esc sensor
    for esc_sensor in config['escSensorRecords']:
      try:
        self._sas_admin.InjectEscSensorDataRecord({'record': esc_sensor})
      except Exception:
        logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
        raise
    # step 7
    # Notify the SAS UUT about the SAS Test Harness
    for sas_th in config['sasTestHarnessConfigs']:
      certificate_hash = getCertificateFingerprint(sas_th['serverCert'])
      url = 'https://' + sas_th['hostName'] + ':' + str(sas_th['port'])
      self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                  'url': url})
    sas_th_config = config['sasTestHarnessConfigs'][0]
    response = self.TriggerFullActivityDumpAndWaitUntilComplete(sas_th_config['serverCert'], sas_th_config['serverKey'])
    # verify that all the SASes get the same response :
    # check dump message format
    self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
    # an array for each record type
    cbsd_dump_data = []
    ppa_dump_data = []
    esc_sensor_dump_data = []
    # step 8 and check
    # download dump files and fill corresponding arrays
    downloaded_files = {}
    for dump_file in response['files']:
      self.assertContainsRequiredFields("ActivityDumpFile.schema.json",
                                          dump_file)
      downloaded_file = None
      if dump_file['recordType'] != 'coordination':
        downloaded_file = self._sas.DownloadFile(dump_file['url'],\
          sas_th_config['serverCert'], sas_th_config['serverKey'])
        # The downloaded_file is being modified in the assertions below,
        # and hence we need a deep copy to verify that dump files are the
        # same when requested by different SASs.
        downloaded_files[dump_file['url']] = copy.deepcopy(downloaded_file)
      if dump_file['recordType'] ==  'cbsd':
        cbsd_dump_data.extend(downloaded_file['recordData'])
      elif dump_file['recordType'] ==  'esc_sensor':
        esc_sensor_dump_data.extend(downloaded_file['recordData'])
      elif dump_file['recordType'] ==  'zone':
        ppa_dump_data.extend(downloaded_file['recordData'])
      else:
        self.assertEqual('coordination', dump_file['recordType'])
    # verify the length of records equal to the inserted ones
    self.assertEqual(len(config['registrationRequests']), len(cbsd_dump_data))
    self.assertEqual(len(config['ppaRecords']), len(ppa_dump_data))
    self.assertEqual(len(config['escSensorRecords']), len(esc_sensor_dump_data))
    # verify the schema of record and first two parts of PPA record Id
    for ppa_record in ppa_dump_data:
      self.assertContainsRequiredFields("ZoneData.schema.json", ppa_record)
      self.assertEqual(ppa_record['id'].split("/")[0], 'zone')
      self.assertEqual(ppa_record['id'].split("/")[1], 'ppa')
      self.assertEqual(ppa_record['id'].split("/")[2], self._sas._sas_admin_id)
      del ppa_record['id']
      # remove creator from value check
      del ppa_record['creator']
      # verify that the injected ppas exist in the dump files
      # check GeoJson Winding of PPA record
      utils.HasCorrectGeoJsonWinding(ppa_record['zone']['features'][0]['geometry'])
      exist_in_dump = False
      for ppa_conf in config['ppaRecords']:
        ppa = ppa_conf['ppaRecord']
        if 'id' in ppa:
          del ppa['id']
        # remove creator from value check
        if 'creator' in ppa:
          del ppa['creator']
        exist_in_dump = exist_in_dump or areTwoPpasEqual(ppa_record, ppa)
      if exist_in_dump:
        break
      self.assertTrue(exist_in_dump)
    # verify the schema of record and two first parts of esc sensor record  Id
    for esc_record in esc_sensor_dump_data:
      self.assertContainsRequiredFields("EscSensorRecord.schema.json", esc_record)
      self.assertEqual(esc_record['id'].split("/")[0], 'esc_sensor')
      self.assertEqual(esc_record['id'].split("/")[1], self._sas._sas_admin_id)
      del esc_record['id']
      # verify that all the injected Esc sensors exist in the dump files
      exist_in_dump = False
      for esc in config['escSensorRecords']:
        if 'id' in esc:
          del esc['id']
        exist_in_dump = exist_in_dump or compareDictWithUnorderedLists(esc_record, esc)
        if exist_in_dump:
          break
      self.assertTrue(exist_in_dump)

    # verify that retrieved cbsd dump files have correct schema
    for cbsd_record in cbsd_dump_data:
      self.assertContainsRequiredFields("CbsdData.schema.json", cbsd_record)
      self.assertFalse("cbsdInfo" in cbsd_record)
    # verify all the previous activities on CBSDs and Grants exist in the dump files
    self.assertCbsdRecord(config['registrationRequests'], grants, grant_responses, cbsd_dump_data, config['conditionalRegistrationData'])
    # step 10 check all SAS Test Harnesses retrieve all of the data in the Full Activity Dump from the SAS UUT
    for sas_th in config['sasTestHarnessConfigs'][1:]:
      dump_message = self._sas.GetFullActivityDump(sas_th['serverCert'], sas_th['serverKey'])
      # check that dump message is the same as the message retreived by the first SAS TH
      compareDictWithUnorderedLists(response, dump_message)
      # check that dump files are the same as the files retreived by the first SAS TH
      for dump_file in dump_message['files']:
        if dump_file['recordType'] != 'coordination':
          downloaded_file = self._sas.DownloadFile(dump_file['url'],\
            sas_th['serverCert'], sas_th['serverKey'])
          self.assertDictEqual(downloaded_files[dump_file['url']], downloaded_file)

  def generate_FAD_2_default_config(self, filename):
    """Generates the WinnForum configuration for FAD_2"""
    # Create the actual config for FAD_2

    # Load the esc sensor in SAS Test Harness
    esc_sensor = json_load(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json'))

    # Load the device_c1 with registration in SAS Test Harness
    device_c1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))

    # Get a latitude and longitude within 40 kms from ESC.
    latitude, longitude, _ = vincenty.GeodesicPoint(esc_sensor['installationParam']['latitude'],
                                                    esc_sensor['installationParam']['longitude'],
                                                    0.1,
                                                    30)  # distance of 0.1 km from ESC at 30 degrees

    # Load the device_c1 in the neighborhood area of the ESC sensor
    device_c1['installationParam']['latitude'] = latitude
    device_c1['installationParam']['longitude'] = longitude

    # Load grant request for device_c1
    grant_g1 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_g1['operationParam']['maxEirp'] = 20

    # Load one ppa in SAS Test Harness
    pal_record_0 = json_load(
        os.path.join('testcases', 'testdata', 'pal_record_0.json'))
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    ppa_record_0 = json_load(
        os.path.join('testcases', 'testdata', 'ppa_record_0.json'))

    ppa_record_a, pal_records = makePpaAndPalRecordsConsistent(ppa_record_0,
                                                                [pal_record_0],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                'test_user_1')

    # Load device_c3 in SAS Test Harness
    device_c3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))

    # Load the device_c3 in the neighborhood area of the PPA
    device_c3['installationParam']['latitude'] = 38.821322
    device_c3['installationParam']['longitude'] = -97.280040

    # Load grant request for device_c3 in SAS Test Harness
    grant_g3 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_g3['operationParam']['maxEirp'] = 20

    # Update grant_g3 frequency to overlap with PPA zone frequency for C3 device
    grant_g3['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3555000000
    }

    # Load the device_c2 with registration to SAS UUT
    device_c2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    # Get a latitude and longitude within 40 kms from ESC.
    latitude, longitude, _ = vincenty.GeodesicPoint(esc_sensor['installationParam']['latitude'],
                                         esc_sensor['installationParam']['longitude'], 0.1,
                                         30)  # distance of 0.1 km from ESC at 30 degrees

    device_c2['installationParam']['latitude'] = latitude
    device_c2['installationParam']['longitude'] = longitude

    # Creating conditionals for C2 and C4.
    self.assertEqual(device_c2['cbsdCategory'], 'B')
    conditional_parameters_c2 = {
        'cbsdCategory': device_c2['cbsdCategory'],
        'fccId': device_c2['fccId'],
        'cbsdSerialNumber': device_c2['cbsdSerialNumber'],
        'airInterface': device_c2['airInterface'],
        'installationParam': device_c2['installationParam'],
        'measCapability': device_c2['measCapability']
    }
    del device_c2['cbsdCategory']
    del device_c2['airInterface']
    del device_c2['installationParam']

    # Load grant request for device_c2 to SAS UUT
    grant_g2 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_g2['operationParam']['maxEirp'] = 30

    # Load the device_c4 with registration to SAS UUT.
    device_c4 = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))

    # Move device_c4 in the neighborhood area of the PPA
    device_c4['installationParam']['latitude'] = 38.8363
    device_c4['installationParam']['longitude'] = -97.2642
    device_c4['installationParam']['antennaBeamwidth'] = 0

    # Creating conditionals for Cat B devices.
    self.assertEqual(device_c4['cbsdCategory'], 'B')
    conditional_parameters_c4 = {
        'cbsdCategory': device_c4['cbsdCategory'],
        'fccId': device_c4['fccId'],
        'cbsdSerialNumber': device_c4['cbsdSerialNumber'],
        'airInterface': device_c4['airInterface'],
        'installationParam': device_c4['installationParam'],
        'measCapability': device_c4['measCapability']
    }
    del device_c4['cbsdCategory']
    del device_c4['airInterface']
    del device_c4['installationParam']

    # Load grant request for device_c4 to SAS UUT
    grant_g4 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_g4['operationParam']['maxEirp'] = 20

    #Update grant_g4 frequency to overlap with PPA zone frequency for C4 device
    grant_g4['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3555000000
    }

    conditionals = {
        'registrationData': [conditional_parameters_c2,
                             conditional_parameters_c4]
    }

    cbsd_records = [device_c1, device_c3]
    grant_record_list = [[grant_g1], [grant_g3]]
    ppa_records = [ppa_record_a]

    # Creating CBSD reference IDs of valid format
    cbsd_reference_id1 = generateCbsdReferenceId('test_fcc_id_x', 'test_serial_number_x')
    cbsd_reference_id2 = generateCbsdReferenceId('test_fcc_id_y', 'test_serial_number_y')
    cbsd_reference_ids = [[cbsd_reference_id1, cbsd_reference_id2]]

    # SAS test harness configuration
    sas_harness_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': "certs/ca.cert"
    }
    # Generate FAD Records for each record type like cbsd,zone and esc_sensor
    cbsd_fad_records = generateCbsdRecords(cbsd_records, grant_record_list)
    ppa_fad_records = generatePpaRecords(ppa_records, cbsd_reference_ids)
    esc_fad_records = [esc_sensor]

    sas_harness_dump_records = {
        'cbsdRecords': cbsd_fad_records,
        'ppaRecords': ppa_fad_records,
        'escSensorRecords': esc_fad_records
    }
    config = {
        'registrationRequestC2': device_c2,
        'registrationRequestC4': device_c4,
        'conditionalRegistrationData': conditionals,
        'grantRequestG2': grant_g2,
        'grantRequestG4': grant_g4,
        'palRecords': pal_records,
        'sasTestHarnessConfig': sas_harness_config,
        'sasTestHarnessDumpRecords': sas_harness_dump_records
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FAD_2_default_config)
  def test_WINNF_FT_S_FAD_2(self, config_filename):
    """Full Activity Dump Pull Command by SAS UUT.

    Checks SAS UUT can successfully request a Full Activity Dump and utilize
    the retrieved data.
    Checks SAS UUT responds with HeartbeatResponse either GRANT_TERMINATED or INVALID_VALUE,
    indicating a terminated Grant.

    """

    config = loadConfig(config_filename)

    device_c2 = config['registrationRequestC2']
    device_c4 = config['registrationRequestC4']
    grant_g2 = config['grantRequestG2']
    grant_g4 = config['grantRequestG4']
    sas_test_harness_dump_records = [config['sasTestHarnessDumpRecords']['cbsdRecords'],
                                     config['sasTestHarnessDumpRecords']['ppaRecords'],
                                     config['sasTestHarnessDumpRecords']['escSensorRecords']]

    # Initialize SAS Test Harness Server instance to dump FAD records
    sas_test_harness = SasTestHarnessServer(config['sasTestHarnessConfig']['sasTestHarnessName'],
                                            config['sasTestHarnessConfig']['hostName'],
                                            config['sasTestHarnessConfig']['port'],
                                            config['sasTestHarnessConfig']['serverCert'],
                                            config['sasTestHarnessConfig']['serverKey'],
                                            config['sasTestHarnessConfig']['caCert'])
    self.InjectTestHarnessFccIds(config['sasTestHarnessDumpRecords']['cbsdRecords'])
    sas_test_harness.writeFadRecords(sas_test_harness_dump_records)


    # Start the server
    sas_test_harness.start()

    # Whitelist the FCCID and UserID for CBSD C2 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c2['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c2['userId']})

    # Whitelist the FCCID and UserID for CBSD C4 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c4['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c4['userId']})

    # Whitelist the FCCID and UserID of the devices loaded to SAS-test_harness in SAS UUT
    for cbsdRecord in config['sasTestHarnessDumpRecords']['cbsdRecords']:
      self._sas_admin.InjectFccId({'fccId': cbsdRecord['registration']['fccId']})


    # Pre-load conditional registration data for C2 and C4 CBSDs.
    if ('conditionalRegistrationData' in config) and (
        config['conditionalRegistrationData']):
      self._sas_admin.PreloadRegistrationData(
          config['conditionalRegistrationData'])

    # Register devices C2 and C4, request grants G2 and G4 respectively with SAS UUT.
    # Ensure the registration and grant requests are successful.
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          [device_c2, device_c4], [grant_g2, grant_g4])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # Send the Heartbeat request for the Grant G2 and G4 of CBSD C2 and C4
    # respectively to SAS UUT.
    transmit_expire_times = self.assertHeartbeatsSuccessful(cbsd_ids, grant_ids,
                                                            ['GRANTED', 'GRANTED'])

    # Notify the SAS UUT about the SAS Test Harness
    certificate_hash = getCertificateFingerprint(config['sasTestHarnessConfig']['serverCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': sas_test_harness.getBaseUrl()})

    # Injecting the PAL Records of the PPA into SAS UUT.
    for pal_record in config['palRecords']:
      try:
        self._sas_admin.InjectPalDatabaseRecord(pal_record)
      except Exception:
        logging.error(common_strings.CONFIG_ERROR_SUSPECTED)
        raise

    # Trigger CPAS in the SAS UUT and wait until complete.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Send the Heartbeat request again for the G2 and G4 to SAS UUT
    request = {
        'heartbeatRequest': [
            {
                'cbsdId': cbsd_ids[0],
                'grantId': grant_ids[0],
                'operationState': 'GRANTED'
            },
            {
                'cbsdId': cbsd_ids[1],
                'grantId': grant_ids[1],
                'operationState': 'GRANTED'
            }
        ]}
    response = self._sas.Heartbeat(request)['heartbeatResponse']

    # Check the length of request and response match.
    self.assertEqual(len(request['heartbeatRequest']), len(response))

    # Check grant response, must be response code 0.
    for resp in response:
      self.assertTrue(resp['response']['responseCode'] in (103, 500))

    # As Python garbage collector is not very consistent, directory is not getting deleted.
    # Hence, explicitly stopping SAS Test Hanress and cleaning up
    sas_test_harness.shutdown()
    del sas_test_harness
