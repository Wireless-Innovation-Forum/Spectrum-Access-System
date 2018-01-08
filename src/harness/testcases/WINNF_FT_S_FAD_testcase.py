from datetime import datetime
import json
import os
import sas
import sas_testcase
from util import winnforum_testcase
class FullActivityDumpTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @classmethod
  def setUpClass(self):
    self._sas_server = sas.GetServer()
    self._sas_server.StartServer()

  @classmethod
  def tearDownClass(self):
    self._sas_server.StopServer()

  @winnforum_testcase
  def test_WINNF_FT_S_FAD_2(self):
    # Load the Config file
    config = loadConfig('testcases/configs/test_WINNF_FT_S_FAD_2/default.config')
    # Load the esc sensor in SAS Test Harness
    esc_sensor = json.load(
          open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
    # Load the device_a with registration in SAS Test Harness
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Load grant request for device_a
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = device_a['userId']
    grant_0['operationParam']['maxEirp'] = config['grant']['maxEirp']
    # Whitelist the FCCID and UserID for the device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})

    # Load the device_b with registration to SAS UUT
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id_b = response['cbsdId']
    # Check registration response of device_b
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Load grant request for device_b to SAS UUT
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = device_b['userId']
    grant_0['operationParam']['maxEirp'] = config['grant']['maxEirp']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    grant_id_b = response['grantId']
    # Check grant response of device_b
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Load one ppa in SAS Test Harness
    ppa_a = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    # Load device_c within the PPA in SAS Test Harness
    device_c = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c['installationParam']['latitude'] = config['device_c']['latitude']
    device_c['installationParam']['longitude'] = config['device_c']['longitude']
    # Load grant request for device_c in SAS Test Harness
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = device_c['userId']
    grant_0['operationParam']['maxEirp'] = config['grant']['maxEirp']
    # Load device_d within the PPA to SAS UUT
    device_d = json.load(
      open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_d['installationParam']['latitude'] = config['device_d']['latitude']
    device_d['installationParam']['longitude'] = config['device_d']['longitude']
    self._sas_admin.InjectFccId({'fccId': device_d['fccId']})
    self._sas_admin.InjectUserId({'userId': device_d['userId']})
    request = {'registrationRequest': [device_d]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id_d = response['cbsdId']
    # Check registration response of device_d of SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Load grant request for device_d to SAS UUT
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = device_d['userId']
    grant_0['operationParam']['maxEirp'] = config['grant']['maxEirp']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    grant_id_d = response['grantId']
    # Check grant response of device_d to SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Send the Heatbeat request for the device_b to SAS UUT
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
    # Send the Heatbeat request for the device_d to SAS UUT
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
    dump_file_a = {}
    dump_file_c = {}
    end_time = datetime.now()
    time_delta = datetime.timedelta(hours=-24)
    start_time = end_time + time_delta
    end_time = str(end_time.replace(microsecond=0).isoformat()) + 'Z'
    start_time = str(start_time.replace(microsecond=0).isoformat()) + 'Z'
    time_delta1 = datetime.timedelta(hours=24)
    grant_expire = end_time + time_delta1
    grant_expire = str(grant_expire.replace(microsecond=0).isoformat()) + 'Z'
    dump_file_a['startTime'] = start_time
    dump_file_a['endTime'] = end_time
    dump_file_a['recordData'] = []
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
        'operationParam': grant_0['operationParam'],
        'channelType': 'GAA',
        'grantExpireTime': grant_expire,
        'terminated': False}]}
    dump_file_a['recordData'].append(internal_data_a)
    device_a_id = dump_file_a['recordData'][0]['id']

    dump_file_c['startTime'] = start_time
    dump_file_c['endTime'] = end_time
    dump_file_c['recordData'] = []
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
        'id': 'SAMPLE_ID_12345',
        'operationParam': grant_0['operationParam'],
        'channelType': 'GAA',
        'grantExpireTime': grant_expire,
        'terminated': False}]}
    dump_file_c['recordData'].append(internal_data_c)
    device_c_id = dump_file_a['recordData'][0]['id']

    expected_path_device_a = '/activity_dump_file/%s' % device_a_id
    expected_path_device_c = '/activity_dump_file/%s' % device_c_id
    # Setup the Server with response body and expected path from SAS Under Test
    response_a = self._sas_server.setupServer({'responseBody': dump_file_a, 'expectedPath': expected_path_device_a})
    response_c = self._sas_server.setupServer({'responseBody': dump_file_c, 'expectedPath': expected_path_device_c})

    activity_dump_file_a = {}
    activity_dump_file_a['url'] = 'https://' + config['dump_config_1']['url'] + '/activity_dump_file/%s' % device_a_id
    activity_dump_file_a['checksum'] = config['dump_config_1']['checksum']
    activity_dump_file_a['size'] = config['dump_config_1']['size']
    activity_dump_file_a['version'] = config['dump_config_1']['version']

    activity_dump_file_c = {}
    activity_dump_file_c['url'] = 'https://' + config['dump_config_2']['url'] + '/activity_dump_file/%s' % device_c_id
    activity_dump_file_c['checksum'] = config['dump_config_2']['checksum']
    activity_dump_file_c['size'] = config['dump_config_2']['size']
    activity_dump_file_c['version'] = config['dump_config_2']['version']

    full_activity_dump = {}
    full_activity_dump['files'] = [activity_dump_file_a, activity_dump_file_c]
    full_activity_dump['generationDateTime'] = end_time
    full_activity_dump['description'] = 'Load SAS Test Harness with one cbsd registration and grant'
    expected_path_dump = '/full_activity_dump_message/test'
    # Setup the Server with response body and expected path from SAS Under Test
    response_dump = self._sas_server.setupServer(
      {'responseBody': full_activity_dump, 'expectedPath': expected_path_dump})
    # Notify the SAS UUT about the SAS Test Harness
    self._sas_admin.InjectPeerSas({'certificateHash': 'certificateHash',
                                    'url': 'https://' + config['dump_config_1']['url'] + '/full_activity_dump_message/test'})

    # Trigger SAS UUT to send the pull request to the SAS Test Harness for activity dump
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    # Get Path and Body from the response
    path, body = response_dump
    # Check the Path of the Pull Command
    self.assertEqual(path, expected_path_dump)

    # Send the Heatbeat request again for the device_b to SAS UUT
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
    # Send the Heatbeat request again for the device_d to SAS UUT
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_id_d,
        'grantId': grant_id_d,
        'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    self.assertEqual(response['response']['responseCode'] in (103, 500))
