from datetime import datetime
import json
import os
import sas
import sas_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, loadConfig, startServer, stopServer
class FullActivityDumpTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_FAD_2_default_config(self, filename):
    # Load the extra config file
    config = loadConfig('testcases/configs/test_WINNF_FT_S_FAD_2/extra.config')
    url = config['sas_testharness_url']
    # Load the esc sensor in SAS Test Harness
    esc_sensor = json.load(open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
    # Load the device_a with registration in SAS Test Harness
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Load grant request for device_a
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_a['cbsdId'] = device_a['userId']
    grant_a['operationParam']['maxEirp'] = config['grant']['maxEirp']
    # Load the device_b with registration to SAS UUT
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Load grant request for device_b to SAS UUT
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_b['cbsdId'] = device_b['userId']
    grant_b['operationParam']['maxEirp'] = config['grant']['maxEirp']
    # Load one ppa in SAS Test Harness
    ppa_a = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    # Load device_c within the PPA in SAS Test Harness
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c['installationParam']['latitude'] = config['device_c']['latitude']
    device_c['installationParam']['longitude'] = config['device_c']['longitude']
    # Load grant request for device_c in SAS Test Harness
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c['cbsdId'] = device_c['userId']
    grant_c['operationParam']['maxEirp'] = config['grant']['maxEirp']
    # Load device_d within the PPA to SAS UUT
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_d['installationParam']['latitude'] = config['device_d']['latitude']
    device_d['installationParam']['longitude'] = config['device_d']['longitude']
    # Load grant request for device_d to SAS UUT
    grant_d = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_d['cbsdId'] = device_d['userId']
    grant_d['operationParam']['maxEirp'] = config['grant']['maxEirp']
    config = {

                'url': url,
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
                'dump_config_cbsd_1': config['dump_config_cbsd_1'],
                'dump_config_cbsd_2': config['dump_config_cbsd_2'],
                'dump_config_ppa': config['dump_config_ppa'],
                'dump_config_esc': config['dump_config_esc'],
                'certificateHash': config['certificateHash'],
                'ca_cart': config['ca_cart']
                }
    writeConfig(filename, config)

  @configurable_testcase(generate_FAD_2_default_config)
  def test_WINNF_FT_S_FAD_2(self, config_filename):
    config = loadConfig(config_filename)
    url = config['url']
    ca_cart = config['ca_cart']
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
    self._sas_server = startServer(url, ca_cart)

    # Whitelist the FCCID and UserID for the device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})

    # Load the device_b with registration to SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id_b = response['cbsdId']
    # Check registration response of device_b
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    request = {'grantRequest': [grant_b]}
    response = self._sas.Grant(request)['grantResponse'][0]
    grant_id_b = response['grantId']
    # Check grant response of device_b
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    self._sas_admin.InjectFccId({'fccId': device_d['fccId']})
    self._sas_admin.InjectUserId({'userId': device_d['userId']})
    request = {'registrationRequest': [device_d]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    cbsd_id_d = response['cbsdId']
    # Check registration response of device_d of SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    request = {'grantRequest': [grant_d]}
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
    self._sas_server.setupCbsdActivity( device_a['userId'],cbsd_file_a)
    self._sas_server.setupCbsdActivity(device_c['userId'], cbsd_file_c)
    # Setup the PPA Activity for SAS Under Test
    self._sas_server.setupPPAActivity(ppa_a['name'],ppa_a)
    # Setup the ESC Activity for SAS Under Test
    self._sas_server.setupEscActivity(esc_sensor['id'],esc_sensor)

    activity_dump_file_a = {}
    activity_dump_file_a['url'] = 'https://' + url + '/cbsd_activity/%s' % device_a_id
    activity_dump_file_a['checksum'] = config['dump_config_cbsd_1']['checksum']
    activity_dump_file_a['size'] = config['dump_config_cbsd_1']['size']
    activity_dump_file_a['version'] = config['dump_config_cbsd_1']['version']

    activity_dump_file_c = {}
    activity_dump_file_c['url'] = 'https://' + url + '/cbsd_activity/%s' % device_c_id
    activity_dump_file_c['checksum'] = config['dump_config_cbsd_2']['checksum']
    activity_dump_file_c['size'] = config['dump_config_cbsd_2']['size']
    activity_dump_file_c['version'] = config['dump_config_cbsd_2']['version']

    activity_dump_ppa = {}
    activity_dump_ppa['url'] = 'https://' + url + '/ppa_activity/%s' % ppa_a['name']
    activity_dump_ppa['checksum'] = config['dump_config_ppa']['checksum']
    activity_dump_ppa['size'] = config['dump_config_ppa']['size']
    activity_dump_ppa['version'] = config['dump_config_ppa']['version']

    activity_dump_esc = {}
    activity_dump_esc['url'] = 'https://' + url + '/esc_activity/%s' % esc_sensor['id']
    activity_dump_esc['checksum'] = config['dump_config_esc']['checksum']
    activity_dump_esc['size'] = config['dump_config_esc']['size']
    activity_dump_esc['version'] = config['dump_config_esc']['version']


    full_activity_dump = {}
    full_activity_dump['files'] = [activity_dump_file_a, activity_dump_file_c, activity_dump_ppa, activity_dump_esc]
    full_activity_dump['generationDateTime'] = end_time
    full_activity_dump['description'] = 'Load SAS Test Harness to SAS UUT'
    # Setup the Full Activity response for SAS Under Test
    self._sas_server.setupFullActivity(full_activity_dump)
    # Notify the SAS UUT about the SAS Test Harness
    self._sas_admin.InjectPeerSas({'certificateHash': config['certificateHash'],
                                    'url': 'https://' + url + '/dump'})

    # Trigger SAS UUT to send the pull request to the SAS Test Harness for activity dump
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

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
    # shutdown the server
    stopServer(self._sas_server)
