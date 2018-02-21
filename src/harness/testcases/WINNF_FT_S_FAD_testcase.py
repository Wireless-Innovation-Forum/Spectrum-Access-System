#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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
import sas
from  util import winnforum_testcase, makePpaAndPalRecordsConsistent,\
 configurable_testcase, writeConfig, loadConfig
import sas_testcase
import hashlib
from datetime import datetime, timedelta

class FullActivityDumpMessageTestcase(sas_testcase.SasTestCase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()

    def tearDown(self):
        pass
    
    def assertEqualToIfExistDeviceOrPreloadedCondtionalParam(self, attr_name, record,\
                 preloaded_condtionals, registration_request):
        attr_value = registration_request[attr_name] if attr_name in registration_request\
         else (preloaded_condtionals[attr_name] if attr_name in \
              preloaded_condtionals else None)
        if attr_value != None: 
            self.assertEqual(attr_value, record[attr_name])
        else :
            self.assertFalse(attr_name in record)
    
    def assertEqualToDeviceOrPreloadedCondtionalParam(self, attr_name, record,\
                 preloaded_condtionals, registration_request):
        attr_value = registration_request[attr_name] if attr_name in registration_request\
         else preloaded_condtionals[attr_name]      
        self.assertEqual(attr_value, record[attr_name])        
        
    
    def assertCbsdRecord(self, registration_request, grant_request, grant_response, cbsd_dump_data, reg_conditional_data):
        for index, device in enumerate(registration_request):
            reg_conditional_device_data_list = [reg['registrationData'] for reg in \
                reg_conditional_data if reg['fccId'] == device['fccId'] and \
                reg['cbsdSerialNumber'] == device['cbsdSerialNumber'] ]
            reg_conditional_device_data = {}
            if any(reg_conditional_device_data_list):
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
            
            self.assertEqualToDeviceOrPreloadedCondtionalParam('cbsdCategory', \
             device, reg_conditional_device_data, cbsd_record[0])
                
            self.assertEqualToDeviceOrPreloadedCondtionalParam('meas_capability', \
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
            self.assertEqualToIfExistDeviceOrPreloadedCondtionalParam('indoorDeployment', \
                device['installationParam'], reg_conditional_device_data['installationParam'],\
                 cbsd_record[0]['installationParam'])
            
            
            self.assertEqualToIfExistDeviceOrPreloadedCondtionalParam('antennaAzimuth', \
                device['installationParam'], reg_conditional_device_data['installationParam'],\
                 cbsd_record[0]['installationParam'])
            
            self.assertEqualToIfExistDeviceOrPreloadedCondtionalParam('antennaDowntilt', \
               device['installationParam'], reg_conditional_device_data['installationParam'],\
                 cbsd_record[0]['installationParam'])
            
            self.assertEqualToIfExistDeviceOrPreloadedCondtionalParam('antennaBeamwidth', \
               device['installationParam'], reg_conditional_device_data['installationParam'],\
                 cbsd_record[0]['installationParam'])
            
            # if callSign exist, it should have the same value as registered
            if 'callSign' in cbsd_record[0]:
                self.assertEqual(device['callSign'], cbsd_record[0]['callSign'])
            max_eirp_by_MHz = 37;           
            # if eirpCapability in the record, it should be the same as device or in accepted limits
            if 'eirpCapability' in cbsd_record[0]:
                if 'eirpCapability' in device:
                    self.assertEqual(device['eirpCapability'], cbsd_record[0]['eirpCapability'])
                    max_eirp_by_MHz = cbsd_record[0]['eirpCapability'] - 10
                else:
                    self.assertLessEqual(cbsd_record[0]['eirpCapability'], 47)
                    self.assertGreaterEqual(cbsd_record[0]['eirpCapability'], -127)
            # antennaModel if exists in device should exist with same value in record                
            self.assertEqualToIfExistDeviceOrPreloadedCondtionalParam('antennaModel', \
               device['installationParam'], reg_conditional_device_data['installationParam'],\
                 cbsd_record[0]['installationParam'])
            
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
            if grants_of_cbsd[0]['requestedOperationParam'] is not None :
                self.assertLessEqual(grants_of_cbsd[0]['requestedOperationParam']['maxEirp'],\
                             max_eirp_by_MHz)
                self.assertGreaterEqual(grants_of_cbsd[0]['requestedOperationParam']['maxEirp'],\
                             -137)
                self.assertGreaterEqual(grants_of_cbsd[0]['requestedOperationParam']['operationFrequencyRange']\
                                 ['lowFrequency'], 3550000000)
                self.assertLessEqual(grants_of_cbsd[0]['requestedOperationParam']\
                                     ['operationFrequencyRange']['lowFrequency'] % 5000000, 0)
                self.assertLessEqual( grants_of_cbsd[0]['requestedOperationParam']\
                                 ['operationFrequencyRange']['highFrequency'], 3700000000)
                self.assertEqual( grants_of_cbsd[0]['requestedOperationParam']\
                                 ['operationFrequencyRange']['highFrequency'] % 5000000, 0)     
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
        pals.append(pal)
        # ESC senosrs
        esc_sensors = []
        esc_sensors.append(json.load(
              open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json'))))
        config = {
            'registrationRequests': devices,
            'conditionalRegistrationData': conditionals,
            'grantRequests': grants,
            'ppas': ppas,
            'pals': pals,
            'escSensors' : esc_sensors
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
        grants = config['grantRequests']
        self.assertEqual(len(responses), len(config['registrationRequests']))
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
        for pal in config['pals']:
            self._sas_admin.InjectPalDatabaseRecord(pal)
                       
        for ppa in config['ppas']:
            ppa_ids.append(self._sas_admin.InjectZoneData({'record': ppa}))          
        # inject N3 Esc sensor
        for esc_sensor in config['escSensors']:
            self._sas_admin.InjectEscSensorDataRecord({'record': esc_sensor})   
            
        # STEP 3
        response = self.TriggerFullActivityDumpAndWaitUntilComplete()
        # STEP 5
        # check dump message format
        self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
        # an array for each record type
        cbsd_dump_data = []
        ppa_dump_data = []
        esc_sensor_dump_data = []
        
        # step 6 and check   
        # download dump files and fill corresponding arrays
        for dump_file in response['files']:
            self.assertContainsRequiredFields("ActivityDumpFile.schema.json",
                                               dump_file[0])
            downloaded_file = None
            if dump_file['recordType'] != 'CoordinationEvent':                
                downloaded_file = self._sas.DownloadFile(dump_file['url'])
                datetime.strptime(downloaded_file['startTime'],\
                                                     '%Y-%m-%dT%H:%M:%SZ')
                datetime.strptime(downloaded_file['endTime'],\
                                                     '%Y-%m-%dT%H:%M:%SZ')
            if dump_file['recordType'] ==  'cbsd':
                cbsd_dump_data.append(downloaded_file['recordData'])   
            elif dump_file['recordType'] ==  'esc_sensor':
                esc_sensor_dump_data.append(downloaded_file['recordData'])
            elif dump_file['recordType'] ==  'zone':
                ppa_dump_data.append(downloaded_file['recordData'])
            else:
                self.assertEqual('CoordinationEvent', dump_file['recordType'])
        
        # verify the length of records equal to the inserted ones
        self.assertEqual(len(config['registrationRequests']), len(cbsd_dump_data))
        self.assertEqual(len(config['ppas']), len(ppa_dump_data))
        self.assertEqual(len(config['escSensors']), len(esc_sensor_dump_data))
        # verify the schema of record and first two parts of PPA record Id  
        for ppa_record in ppa_dump_data:
            self.assertContainsRequiredFields("zoneData.schema.json", ppa_record)              
            self.assertEqual(ppa_record['id'].split("/")[0], 'zone')
            self.assertEqual(ppa_record['id'].split("/")[1], self._sas._sas_admin)
            del ppa_record['id']
        # verify that the injected ppas exist in the dump files
        for index, ppa in enumerate(config['ppas']):
            del ppa['id']
            exist_in_dump = False
            for ppa_record in ppa_dump_data:
                shared_items = set(ppa_record.items()) & set(ppa.items())               
                if  len(shared_items) == len(ppa):
                     exist_in_dump = True
            self.assertTrue(exist_in_dump)
            
        # verify the schema of record and two first parts of esc sensor record  Id
        for esc_record in esc_sensor_dump_data:                    
            self.assertContainsRequiredFields("EscSensorRecord.schema.json", esc_record)
            self.assertEqual(esc_record['id'].split("/")[0], 'esc_sensor')
            self.assertEqual(esc_record['id'].split("/")[1], self._sas._sas_admin)
            del esc_record['id'] 
        # verify that all the injected Esc sensors exist in the dump files                 
        for esc in config['escSensors']:
            exist_in_dump = False
            del esc['id'] 
            for esc_record in esc_sensor_dump_data:
                self.assertDictEqual(esc, esc_record)
                shared_items = set(esc_record.items()) & set(esc.items())               
                if  len(shared_items) == len(esc):
                    exist_in_dump = True
            self.assertTrue(exist_in_dump)
        # verify that retrieved cbsd dump files have correct schema
        for cbsd_record in cbsd_dump_data:
            self.assertContainsRequiredFields("CbsdData.schema.json", cbsd_record)
            self.assertFalse("cbsdInfo" in cbsd_record)
            
        # verify all the previous activities on CBSDs and Grants exist in the dump files
        self.assertCbsdRecord(config['registrationRequests'], grants, grant_responses, cbsd_dump_data, config['conditionalRegistrationData'])