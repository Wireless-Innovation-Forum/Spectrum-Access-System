from datetime import datetime
import json
import os
import sys
import sas
import sas_testcase
from sas_test_harness import SasTestHarness, GetSasTestHarnessUrl
from util import configurable_testcase, writeConfig, loadConfig

class FullActivityDumpTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()
    self._sas_server = SasTestHarness()

  def tearDown(self):
    if hasattr(self, '_sas_server'):
      self._sas_server.stopServer()

  def generate_FAD_2_activity_dump(self, sas_th_url, device_a, grant_a, device_c, grant_c, ppa_a, esc_sensor):
    # Create an activity dump in SAS Test Harness in local
    cbsd_file_a = {}
    cbsd_file_c = {}
    end_time = datetime.now()
    time_delta = datetime.timedelta(hours=-24)
    start_time = end_time + time_delta
    end_time = str(end_time.replace(microsecond=0).isoformat()) + 'Z'
    start_time = str(start_time.replace(microsecond=0).isoformat()) + 'Z'
    time_delta1 = datetime.timedelta(hours=24)
    grant_expire = end_time + time_delta1
    grant_expire = str(grant_expire.replace(microsecond=0).isoformat()) + 'Z'
    cbsd_file_a['startTime'] = start_time
    cbsd_file_a['endTime'] = end_time
    cbsd_file_a['recordData'] = []
    internal_data_a = {
      'id': 'device_a_id',
      'registration': {
        'fccId': device_a['fccId'],
        'cbsdCategory': device_a['cbsdCategory'],
        'callSign': device_a['callSign'],
        'userId': device_a['userId'],
        'airInterface': device_a['airInterface'],
        'measCapability': device_a['measCapability'],
        'installationParam': device_a['installationParam'],
        'groupingParam': [
          {
            'groupId': 'exampleGroup',
            'groupType': 'INTERFERENCE_COORDINATION'
          }]},
      'grants': [{
        'id': 'SAMPLE_ID_12345',
        'operationParam': grant_a['operationParam'],
        'channelType': 'GAA',
        'grantExpireTime': grant_expire,
        'terminated': False}]}
    cbsd_file_a['recordData'].append(internal_data_a)
    device_a_id = cbsd_file_a['recordData'][0]['id']

    cbsd_file_c['startTime'] = start_time
    cbsd_file_c['endTime'] = end_time
    cbsd_file_c['recordData'] = []
    internal_data_c = {
      'id': 'device_c_id',
      'registration': {
        'fccId': device_c['fccId'],
        'cbsdCategory': device_c['cbsdCategory'],
        'callSign': device_c['callSign'],
        'userId': device_c['userId'],
        'airInterface': device_c['airInterface'],
        'measCapability': device_c['measCapability'],
        'installationParam': device_c['installationParam'],
        'groupingParam': [
          {
            'groupId': 'exampleGroup',
            'groupType': 'INTERFERENCE_COORDINATION'
          }]},
      'grants': [{
        'id': 'SAMPLE_ID_6789',
        'operationParam': grant_c['operationParam'],
        'channelType': 'GAA',
        'grantExpireTime': grant_expire,
        'terminated': False}]}
    cbsd_file_c['recordData'].append(internal_data_c)
    device_c_id = cbsd_file_c['recordData'][0]['id']

    # Setup the Cbsd Activity for SAS Under Test
    self._sas_server.setupCbsdActivity(device_a['userId'], cbsd_file_a)
    self._sas_server.setupCbsdActivity(device_c['userId'], cbsd_file_c)
    # Setup the PPA Activity for SAS Under Test
    self._sas_server.setupPpaActivity(ppa_a['name'], ppa_a)
    # Setup the ESC Activity for SAS Under Test
    self._sas_server.setupEscActivity(esc_sensor['id'], esc_sensor)

    activity_dump_file_a = {}
    activity_dump_file_a['url'] = 'https://' + sas_th_url + '/cbsd_activity/%s' % device_a_id
    activity_dump_file_a['checksum'] = "For the future calculating"
    activity_dump_file_a['size'] = sys.getsizeof(cbsd_file_a)
    activity_dump_file_a['version'] = "v1.2"

    activity_dump_file_c = {}
    activity_dump_file_c['url'] = 'https://' + sas_th_url + '/cbsd_activity/%s' % device_c_id
    activity_dump_file_c['checksum'] = "For the future calculating"
    activity_dump_file_c['size'] = sys.getsizeof(cbsd_file_c)
    activity_dump_file_c['version'] = "v1.2"

    activity_dump_ppa = {}
    activity_dump_ppa['url'] = 'https://' + sas_th_url + '/ppa_activity/%s' % ppa_a['name']
    activity_dump_ppa['checksum'] = sys.getsizeof(ppa_a)
    activity_dump_ppa['size'] = "For the future calculating"
    activity_dump_ppa['version'] = "v1.2"

    activity_dump_esc = {}
    activity_dump_esc['url'] = 'https://' + sas_th_url + '/esc_activity/%s' % esc_sensor['id']
    activity_dump_esc['checksum'] = "For the future calculating"
    activity_dump_esc['size'] = sys.getsizeof(esc_sensor)
    activity_dump_esc['version'] = "v1.2"

    full_activity_dump = {}
    full_activity_dump['files'] = [activity_dump_file_a, activity_dump_file_c, activity_dump_ppa, activity_dump_esc]
    full_activity_dump['generationDateTime'] = end_time
    full_activity_dump['description'] = 'Load SAS Test Harness to SAS UUT'

    # Setup the Full Activity response for SAS Under Test
    self._sas_server.setupFullActivity(full_activity_dump)


  def generate_FAD_2_default_config(self, filename):
    # Step 1: Load the esc sensor in SAS Test Harness
    esc_sensor = json.load(open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
    # Step 2: Load the device_a with registration in SAS Test Harness
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Step 2: Load grant request for device_a
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_a['cbsdId'] = device_a['userId']
    grant_a['operationParam']['maxEirp'] = 20
    # Load the device_b with registration to SAS UUT
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Load grant request for device_b to SAS UUT
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_b['cbsdId'] = device_b['userId']
    grant_b['operationParam']['maxEirp'] = 20
    # Load one ppa in SAS Test Harness
    ppa_a = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    # Load device_c within the PPA in SAS Test Harness
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c['installationParam']['latitude'] = 38.7790
    device_c['installationParam']['longitude'] = -97.2263
    # Load grant request for device_c in SAS Test Harness
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c['cbsdId'] = device_c['userId']
    grant_c['operationParam']['maxEirp'] = 20
    # Load device_d within the PPA to SAS UUT
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_d['installationParam']['latitude'] = 38.7790
    device_d['installationParam']['longitude'] = -97.2263
    # Load grant request for device_d to SAS UUT
    grant_d = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_d['cbsdId'] = device_d['userId']
    grant_d['operationParam']['maxEirp'] = 20
    url = GetSasTestHarnessUrl()
    config = {  'url' : url,
                'device_a': device_a,
                'device_b': device_b,
                'device_c': device_c,
                'device_d': device_d,
                'grant_a': grant_a,
                'grant_b': grant_b,
                'grant_c': grant_c,
                'grant_d': grant_d,
                'ppa_a': ppa_a,
                'esc_sensor': esc_sensor,
                'certificateHash': "will provide in the future"

                }
    writeConfig(filename, config)

  @configurable_testcase(generate_FAD_2_default_config)
  def test_WINNF_FT_S_FAD_2(self, config_filename):
    config = loadConfig(config_filename)
    sas_th_url = config['url']
    device_a = config['device_a']
    device_b = config['device_b']
    device_c = config['device_c']
    device_d = config['device_d']
    grant_a = config['grant_a']
    grant_b = config['grant_b']
    grant_c = config['grant_c']
    grant_d = config['grant_d']
    ppa_a = config['ppa_a']
    esc_sensor = config['esc_sensor']
    # Start the server
    self._sas_server.startServer()

    # Step 3: Whitelist the FCCID and UserID for the device_b in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})

    # Step 4: load the device_b with registration to SAS UUT
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id_b = response['cbsdId']
    # Check registration response of device_b
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 5: Load the device_b with grant to SAS UUT
    request = {'grantRequest': [grant_b]}
    response = self._sas.Grant(request)['grantResponse'][0]
    grant_id_b = response['grantId']
    # Check grant response of device_b
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Whitelist the FCCID and UserID for the device_d in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_d['fccId']})
    self._sas_admin.InjectUserId({'userId': device_d['userId']})
    # Step 8: Load the device_d with registration to SAS UUT
    request = {'registrationRequest': [device_d]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id_d = response['cbsdId']
    # Check registration response of device_d of SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 9: Load the device_d with grant to SAS UUT
    request = {'grantRequest': [grant_d]}
    response = self._sas.Grant(request)['grantResponse'][0]
    grant_id_d = response['grantId']
    # Check grant response of device_d to SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 10: Send the Heatbeat request for the device_b to SAS UUT
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_id_b,
        'grantId': grant_id_b,
        'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 10: Send the Heatbeat request for the device_d to SAS UUT
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_id_d,
        'grantId': grant_id_d,
        'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    self.assertEqual(response['response']['responseCode'], 0)
    # Create an activity dump in SAS Test Harness in local
    self.generate_FAD_2_activity_dump( sas_th_url, device_a, grant_a, device_c, grant_c, ppa_a, esc_sensor)
    # Start server
    self._sas_server.startServer()
    # Step 11: Notify the SAS UUT about the SAS Test Harness
    self._sas_admin.InjectPeerSas({'certificateHash': config['certificateHash'],
                                    'url': 'https://' + sas_th_url + '/dump'})

    # Step 12: Trigger SAS UUT to send the pull request to the SAS Test Harness for activity dump
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 13: Send the Heatbeat request again for the device_b to SAS UUT
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_id_b,
        'grantId': grant_id_b,
        'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    self.assertEqual(response['response']['responseCode'] in (103, 500))
    del request, response
    # Step 13: Send the Heatbeat request again for the device_d to SAS UUT
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_id_d,
        'grantId': grant_id_d,
        'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    self.assertEqual(response['response']['responseCode'] in (103, 500))
