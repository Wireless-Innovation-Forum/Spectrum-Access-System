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

import hashlib
import json
import os
import sas
import sas_testcase
from reference_models.geo import vincenty
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generateCbsdReferenceId, generatePpaRecords

from util import configurable_testcase, writeConfig, loadConfig \
  , getCertificateFingerprint, getRandomLatLongInPolygon, makePpaAndPalRecordsConsistent \
      , compareDictWithUnorderedLists,winnforum_testcase

class FullActivityDumpTestcase(sas_testcase.SasTestCase):
  """ This class contains all FAD related tests mentioned in SAS TS  """

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass
      
  def assertEqualToDeviceOrPreloadedConditionalParamOrDefaultValue(self, attr_name, record,\
                preloaded_conditionals, registration_request, default_value):
      """ this function checks the optional parameter of dump with
        the parameter of the registered Cbsd
        Args:
        attr_name: string represent the attribute name, we want to compare.
        record: the parent attribute that should contain the compared attribute in the dump record.
        preloaded_conditionals:the parent attribute that should contain the compared attribute in the preloaded conditional parameters.
        registration_request: the parent attribute that should contain the compared attribute in the registration request.
        default_value : a default value of attribute type to be compared with.

      Behavior:this function asserts that the value in dump record is equal to the value in 
        preloaded conditional parameters or
        registration request or a default value (the priority is for the registration request value,
        then preloaded conditional parameters)
      """  
      attr_value = registration_request[attr_name] if attr_name in registration_request\
        else (preloaded_conditionals[attr_name] if attr_name in \
            preloaded_conditionals else default_value)
      attr_value_in_record = record[attr_name] if attr_name in record else  None 
      self.assertEqual(attr_value, attr_value_in_record)
    
  def assertEqualToDeviceOrPreloadedConditionalParam(self, attr_name, record,\
                preloaded_conditionals, registration_request):
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
          reg_conditional_device_data_list = [reg['registrationData'] for reg in \
              reg_conditional_data if reg['fccId'] == device['fccId'] and \
              reg['cbsdSerialNumber'] == device['cbsdSerialNumber'] ]
          reg_conditional_device_data = {}
          if any(reg_conditional_device_data_list):
            self.assertEqual(reg_conditional_device_data_list, 1)
            reg_conditional_device_data = reg_conditional_device_data_list[0]
          if 'installationParam' not in reg_conditional_device_data:
              reg_conditional_device_data['installationParam'] = None
          record_id = 'cbsd/'+ device['fccId']+'/'+ hashlib.sha1(device['cbsdSerialNumber']).hexdigest()
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
            
          self.assertEqualToDeviceOrPreloadedCondtionalParam('latitude', \
            device['installationParam'], reg_conditional_device_data\
            ['installationParam'], cbsd_record[0]['installationParam'])
            
          self.assertEqualToDeviceOrPreloadedCondtionalParam('longitude', \
            device['installationParam'], reg_conditional_device_data\
            ['installationParam'], cbsd_record[0]['installationParam'])
            
          self.assertEqualToDeviceOrPreloadedCondtionalParam('height', \
            device['installationParam'], reg_conditional_device_data\
            ['installationParam'], cbsd_record[0]['installationParam'])

          self.assertEqualToDeviceOrPreloadedCondtionalParam('heightType', \
            device['installationParam'], reg_conditional_device_data\
            ['installationParam'], cbsd_record[0]['installationParam'])
            
          self.assertEqualToDeviceOrPreloadedCondtionalParam('antennaGain', \
            device['installationParam'], reg_conditional_device_data\
            ['installationParam'], cbsd_record[0]['installationParam'])                   
            
            # parameters should exist in record if exist in device,\        
          self.assertEqualToDeviceOrPreloadedCondtionalParam('indoorDeployment', \
              device['installationParam'], reg_conditional_device_data['installationParam'],\
                cbsd_record[0]['installationParam'])
          #  parameters should equal to device or to default value            
          self.assertEqualToDeviceOrPreloadedConditionalParamOrDefaultValue('antennaAzimuth', \
              device['installationParam'], reg_conditional_device_data['installationParam'],\
                cbsd_record[0]['installationParam'], 0)
                
          self.assertEqualToDeviceOrPreloadedConditionalParamOrDefaultValue('antennaBeamwidth', \
              device['installationParam'], reg_conditional_device_data['installationParam'],\
                cbsd_record[0]['installationParam'], 360)
            
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
          grants_of_cbsd = [cbsd['grants'] for cbsd in cbsd_dump_data if cbsd['id'] == record_id]
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
      device_a = json.load(
          open(os.path.join('testcases', 'testdata', 'device_a.json')))
      device_b = json.load(
          open(os.path.join('testcases', 'testdata', 'device_b.json')))
      device_c = json.load(
          open(os.path.join('testcases', 'testdata', 'device_c.json')))
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
          grants.append(json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json'))))
      # PPAs and PALs
      ppas = []
      pals = []
      pal_low_frequency = 3550000000.0
      pal_high_frequency = 3560000000.0
      pal_record = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
      ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
      ppa, pal = makePpaAndPalRecordsConsistent(ppa_record,
                                                              [pal_record],
                                                              pal_low_frequency,
                                                              pal_high_frequency,
                                                              device_a['userId'])
      ppas.append(ppa)
      pals.extend(pal)
      # ESC senosrs
      esc_sensors = []
      esc_sensors.append(json.load(
            open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json'))))
      # SAS test harness configuration
      sas_harness_config = {
          'sasTestHarnessName': 'SAS-TH-2',
          'hostName': 'localhost',
          'port': 9002,
          'serverCert': "certs/sas.cert",
          'serverKey': "certs/sas.key",
          'caCert': "certs/ca.cert"
      }
      config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'grantRequests': grants,
        'ppaRecords': ppas,
        'palRecords': pals,
        'escSensorRecords' : esc_sensors,
        'sasTestHarnessConfig': sas_harness_config
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
        
      # inject FCC IDs and User IDs of CBSDs   
      for device in config['registrationRequests']:
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
      # inject PALs and N2 PPAs
      ppa_ids = []       
      for pal in config['palRecords']:
          self._sas_admin.InjectPalDatabaseRecord(pal)
                       
      for ppa in config['ppaRecords']:
          ppa_ids.append(self._sas_admin.InjectZoneData({'record': ppa}))          
      # inject N3 Esc sensor
      for esc_sensor in config['escSensorRecords']:
          self._sas_admin.InjectEscSensorDataRecord({'record': esc_sensor})
      # step 7
      # Notify the SAS UUT about the SAS Test Harness
      sas_th_config = config['sasTestHarnessConfig']		
      certificate_hash = getCertificateFingerprint(sas_th_config['serverCert'])
      self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                  'url': sas_th_config['url']})

      response = self.TriggerFullActivityDumpAndWaitUntilComplete(sas_th_config['serverCert'], sas_th_config['serverKey'])
      # check dump message format
      self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
      # an array for each record type
      cbsd_dump_data = []
      ppa_dump_data = []
      esc_sensor_dump_data = []
        
      # step 8 and check   
      # download dump files and fill corresponding arrays
      for dump_file in response['files']:
          self.assertContainsRequiredFields("ActivityDumpFile.schema.json",
                                              dump_file)
          downloaded_file = None
          if dump_file['recordType'] != 'CoordinationEvent':                
              downloaded_file = self._sas.DownloadFile(dump_file['url'],\
				  sas_th_config['serverCert'], sas_th_config['serverKey'])
          if dump_file['recordType'] ==  'cbsd':
              cbsd_dump_data.extend(downloaded_file['recordData'])   
          elif dump_file['recordType'] ==  'esc_sensor':
              esc_sensor_dump_data.extend(downloaded_file['recordData'])
          elif dump_file['recordType'] ==  'zone':
              ppa_dump_data.extend(downloaded_file['recordData'])
          else:
              self.assertEqual('CoordinationEvent', dump_file['recordType'])
        
      # verify the length of records equal to the inserted ones
      self.assertEqual(len(config['registrationRequests']), len(cbsd_dump_data))
      self.assertEqual(len(config['ppas']), len(ppa_dump_data))
      self.assertEqual(len(config['escSensors']), len(esc_sensor_dump_data))
      # verify the schema of record and first two parts of PPA record Id  
      for ppa_record in ppa_dump_data:
          self.assertContainsRequiredFields("ZoneData.schema.json", ppa_record)              
          self.assertEqual(ppa_record['id'].split("/")[0], 'zone')
          self.assertEqual(ppa_record['id'].split("/")[1], 'ppa')
          self.assertEqual(ppa_record['id'].split("/")[2], self._sas._sas_admin_id)
          del ppa_record['id']
      # verify that the injected ppas exist in the dump files
		  # TODO: check that the PPAs overlap nearly entirely, rather than requiring exactly the same vertices.
      # and we should check the order of the points of PPA contour in the dump to be CCW 
      for index, ppa in enumerate(config['ppas']):
        del ppa['id']
        exist_in_dump = False
        for ppa_record in ppa_dump_data:			           
          exist_in_dump = exist_in_dump or compareDictWithUnorderedLists(ppa_record, ppa)
        self.assertTrue(exist_in_dump)        
      # verify the schema of record and two first parts of esc sensor record  Id
      for esc_record in esc_sensor_dump_data:                    
        self.assertContainsRequiredFields("EscSensorRecord.schema.json", esc_record)
        self.assertEqual(esc_record['id'].split("/")[0], 'esc_sensor')
        self.assertEqual(esc_record['id'].split("/")[1], self._sas._sas_admin_id)
        del esc_record['id'] 
      # verify that all the injected Esc sensors exist in the dump files                 
      for esc in config['escSensors']:
        exist_in_dump = False
        del esc['id'] 
        for esc_record in esc_sensor_dump_data:
            exist_in_dump = exist_in_dump or compareDictWithUnorderedLists(esc_record, esc)
        self.assertTrue(exist_in_dump)
      # verify that retrieved cbsd dump files have correct schema
      for cbsd_record in cbsd_dump_data:
          self.assertContainsRequiredFields("CbsdData.schema.json", cbsd_record)
          self.assertFalse("cbsdInfo" in cbsd_record)
            
      # verify all the previous activities on CBSDs and Grants exist in the dump files
      self.assertCbsdRecord(config['registrationRequests'], grants, grant_responses, cbsd_dump_data, config['conditionalRegistrationData'])

  def generate_FAD_2_default_config(self, filename):
    """Generates the WinnForum configuration for FAD_2"""
    # Create the actual config for FAD_2

    # Load the esc sensor in SAS Test Harness
    esc_sensor = json.load(open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))

    # Load the device_c1 with registration in SAS Test Harness
    device_c1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Get a latitude and longitude within 40 kms from ESC.
    latitude, longitude, _ = vincenty.GeodesicPoint(esc_sensor['installationParam']['latitude'],
                                                    esc_sensor['installationParam']['longitude'],
                                                    15,
                                                    30)  # distance of 15 kms from ESC at 30 degrees

    # Load the device_c1 in the neighborhood area of the ESC sensor
    device_c1['installationParam']['latitude'] = latitude
    device_c1['installationParam']['longitude'] = longitude

    # Load grant request for device_c1
    grant_g1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g1['operationParam']['maxEirp'] = 20

    # Load one ppa in SAS Test Harness
    pal_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    ppa_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))

    ppa_record_a, pal_records = makePpaAndPalRecordsConsistent(ppa_record_0,
                                                                [pal_record_0],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                'test_user_1')

    # Load device_c3 in SAS Test Harness
    device_c3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Load the device_c3 in the neighborhood area of the PPA
    device_c3['installationParam']['latitude'] = 38.821322
    device_c3['installationParam']['longitude'] = -97.282813

    # Load grant request for device_c3 in SAS Test Harness
    grant_g3 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g3['operationParam']['maxEirp'] = 20

    # Update grant_g3 frequency to overlap with PPA zone frequency for C3 device
    grant_g3['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3555000000
    }

    # Load the device_c2 with registration to SAS UUT
    device_c2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Get a latitude and longitude within 40 kms from ESC.
    latitude, longitude, _ = vincenty.GeodesicPoint(esc_sensor['installationParam']['latitude'],
                                         esc_sensor['installationParam']['longitude'], 20,
                                         30)  # distance of 20 kms from ESC at 30 degrees

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
    grant_g2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g2['operationParam']['maxEirp'] = 30

    # Load the device_c4 with registration to SAS UUT.
    device_c4 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))

    # Move device_c4 in the neighborhood area of the PPA
    device_c4['installationParam']['latitude'] = 38.805335
    device_c4['installationParam']['longitude'] = -97.307623

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
    grant_g4 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
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
        'hostName': 'localhost',
        'port': 9001,
        'serverCert': "certs/server.cert",
        'serverKey': "certs/server.key",
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
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_c2, device_c4],
                                                          [grant_g2, grant_g4])

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
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

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