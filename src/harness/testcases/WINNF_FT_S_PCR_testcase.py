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

# Some parts of this software was developed by employees of
# the National Institute of Standards and Technology (NIST),
# an agency of the Federal Government.
# Pursuant to title 17 United States Code Section 105, works of NIST employees
# are not subject to copyright protection in the United States and are
# considered to be in the public domain. Permission to freely use, copy,
# modify, and distribute this software and its documentation without fee
# is hereby granted, provided that this notice and disclaimer of warranty
# appears in all copies.

# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER
# EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY
# THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM
# INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE
# SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT
# SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT,
# INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM,
# OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON
# WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED
# BY PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED
# FROM, OR AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES
# PROVIDED HEREUNDER.

# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with the
# code in compliance with the conditions of those licenses.

from datetime import datetime
import json
import os
import sas
import sas_testcase
from reference_models.ppa_model.ppa_ref_model import ppa_creation_model_byList
from util import winnforum_testcase, configurable_testcase, writeConfig, loadConfig
from sas import _RequestGet
from shapely.geometry import Polygon

class PPACreationTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass


  def generate_PCR_1_default_config(self, filename):
    # Step 1: Load PAL Database Record
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record['channelAssign'] = {
      "primaryAssignmen": {
        "lowFrequency": 3550000000,
        "highFrequency": 3560000000
      },
      "secondaryAssignment": {
        "lowFrequency": 3580000000,
        "highFrequency": 3590000000
      }
    }
    pal_record['userId'] = "pal_user"
    pal_record['palId'] = "pal/10-2017/123456789/A"

    # Step 2: Load the device_a in DP Test Harness
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 39.0119
    device_a['installationParam']['longitude'] = -98.4842
    device_a['userId'] = pal_record['licensee']

    # Step 2: Load the device_b in DP Test Harness
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 39.139836
    device_b['installationParam']['longitude'] = -97.770094
    device_b['userId'] = pal_record['licensee']

    url = 'sas_testUUT_url will be provided in the future'

    config = {
        'url': url,
        'device_a': device_a,
        'device_b': device_b,
        'pal_record': pal_record
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_1_default_config)
  def test_WINNF_FT_S_PCR_1(self, config_filename):
    # Load the Config file
    config = loadConfig(config_filename)
    url = config['url']
    device_a = config['device_a']
    pal_record = config['pal_record']
    device_b = config['device_b']

    # Step 1: Inject PAL record
    self._sas_admin.InjectPalDatabaseRecord(pal_record)
    # Step 2: register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_a in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 2: register device_b in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_b in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 3: Triggers SAS UUT to create a PPA boundary
    cbsdIds = [device_a['cbsdSerialNumber'],device_b['cbsdSerialNumber']]
    palIds = [pal_record['palId']]
    response = self._sas_admin.TriggerPpaCreation(cbsdIds, palIds)
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertNotEqual(response['ppaId'], None)
    # Step 4: Triggers the SAS UUT to generate the Full Activity Dump
    self._sas_admin.TriggerCreateActivityDump()
    # Step 5: SAS Test Harness uses the SAS-SAS protocol to retrieve the PPA zone

    full_activity_dump = _RequestGet('https://%s' %
                (url + '/dump'))
    self.polygon_dump = _RequestGet('https://%s' %
                (full_activity_dump['url']))
    # Step 6: Using PPA Creation Reference Model to calculate the maximum PPA
    devices_list = [device_a, device_b]
    pal_record_list = [pal_record]
    pal_low_frequency = pal_record['channelAssign']['primaryAssignmen']['lowFrequency']
    pal_high_frequency = pal_record['channelAssign']['primaryAssignmen']['highFrequency']
    polygon_result = ppa_creation_model_byList(devices_list, pal_record_list, pal_record['userId'], pal_low_frequency, pal_high_frequency)
    polygon = polygon_result['features'][0]['geometry']['coordinates'][0]
    polygon = Polygon([tuple(i) for i in polygon])
    polygon_dump = Polygon([tuple(i) for i in self.polygon_dump])
    polygon_overlap = polygon.intersection(polygon_dump)
    self.assertGreaterEqual(polygon_overlap.area, polygon.area * 0.9)



  def generate_PCR_2_default_config(self, filename):
    # Step 1: Load PAL Database Record
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record['channelAssign'] = {
      "primaryAssignmen": {
        "lowFrequency": 3550000000,
        "highFrequency": 3560000000
      },
      "secondaryAssignment": {
        "lowFrequency": 3580000000,
        "highFrequency": 3590000000
      }
    }
    pal_record['userId'] = "pal_user"
    pal_record['palId'] = "pal/10-2017/123456789/A"

    # Step 2: Load the device_a in DP Test Harness
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 39.0119
    device_a['installationParam']['longitude'] = -98.4842
    device_a['userId'] = pal_record['licensee']

    # Step 2: Load the device_b in DP Test Harness
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 39.139836
    device_b['installationParam']['longitude'] = -97.770094
    device_b['userId'] = pal_record['licensee']

    url = 'sas_testUUT_url will be provided in the future'

    config = {
      'url': url,
      'device_a': device_a,
      'device_b': device_b,
      'pal_record': pal_record
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_2_default_config)
  def test_WINNF_FT_S_PCR_2(self, config_filename):
    # Load the Config file
    config = loadConfig(config_filename)
    url = config['url']
    device_a = config['device_a']
    pal_record = config['pal_record']
    device_b = config['device_b']

    # Step 1: Inject PAL record into SAS UUT
    self._sas_admin.InjectPalDatabaseRecord(pal_record)
    # Step 2: register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_a in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 2: register device_b in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_b in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 3: Triggers SAS UUT to create a PPA boundary
    cbsdIds = [device_a['cbsdSerialNumber'], device_b['cbsdSerialNumber']]
    palIds = [pal_record['palId']]
    response = self._sas_admin.TriggerPpaCreation(cbsdIds, palIds)
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertNotEqual(response['ppaId'], None)
    # Step 4: Triggers the SAS UUT to generate the Full Activity Dump
    self._sas_admin.TriggerCreateActivityDump()
    # Step 5: SAS Test Harness uses the SAS-SAS protocol to retrieve the PPA zone
    full_activity_dump = _RequestGet('https://%s' %
                                     (url + '/dump'))
    self.polygon_dump = _RequestGet('https://%s' %
                                    (full_activity_dump['url']))
    # Step 6: Using PPA Creation Reference Model to calculate the maximum PPA
    devices_list = [device_a, device_b]
    pal_record_list = [pal_record]
    pal_low_frequency = pal_record['channelAssign']['primaryAssignmen']['lowFrequency']
    pal_high_frequency = pal_record['channelAssign']['primaryAssignmen']['highFrequency']
    polygon_result = ppa_creation_model_byList(devices_list, pal_record_list, pal_record['userId'], pal_low_frequency,
                                         pal_high_frequency)
    polygon = polygon_result['features'][0]['geometry']['coordinates'][0]
    polygon = Polygon([tuple(i) for i in polygon])
    polygon_dump = Polygon([tuple(i) for i in self.polygon_dump])
    polygon_overlap = polygon.intersection(polygon_dump)
    self.assertGreaterEqual(polygon_overlap.area, polygon.area * 0.9)


  def generate_PCR_3_default_config(self, filename):
    # Step 1: Load PAL Database Record
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record['channelAssign'] = {
      "primaryAssignmen": {
        "lowFrequency": 3550000000,
        "highFrequency": 3560000000
      },
      "secondaryAssignment": {
        "lowFrequency": 3580000000,
        "highFrequency": 3590000000
      }
    }
    pal_record['userId'] = "pal_user"
    pal_record['palId'] = "pal/10-2017/123456789/A"

    # Step 2: Load the device_a in DP Test Harness
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 39.0119
    device_a['installationParam']['longitude'] = -98.4842
    device_a['userId'] = pal_record['licensee']

    # Step 2: Load the device_b in DP Test Harness
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 39.139836
    device_b['installationParam']['longitude'] = -97.770094
    device_b['userId'] = pal_record['licensee']

    url = 'sas_testUUT_url will be provided in the future'

    config = {
      'url': url,
      'device_a': device_a,
      'device_b': device_b,
      'pal_record': pal_record
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_3_default_config)
  def test_WINNF_FT_S_PCR_3(self, config_filename):
    # Load the Config file
    config = loadConfig(config_filename)
    url = config['url']
    device_a = config['device_a']
    pal_record = config['pal_record']
    device_b = config['device_b']

    # Step 1: Inject PAL record in SAS UUT
    self._sas_admin.InjectPalDatabaseRecord(pal_record)
    # Step 2: register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_a in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 2: register device_b in SAS UU
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_b in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 3: Triggers SAS UUT to create a PPA boundary
    cbsdIds = [device_a['cbsdSerialNumber'], device_b['cbsdSerialNumber']]
    palIds = [pal_record['palId']]
    # execute the pre-request PCR.1
    self.test_WINNF_FT_S_PCR_1('testcases/configs/test_WINNF_FT_S_PCR_1/default.config')
    response = self._sas_admin.TriggerPpaCreation(cbsdIds, palIds, self.polygon_dump)
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertNotEqual(response['ppaId'], None)
    # Step 4: Triggers the SAS UUT to generate the Full Activity Dump
    self._sas_admin.TriggerCreateActivityDump()
    # Step 5: SAS Test Harness uses the SAS-SAS protocol to retrieve the PPA zone
    full_activity_dump = _RequestGet('https://%s' %(url + '/dump'))
    polygon_dump = _RequestGet('https://%s' %(full_activity_dump['url']))
    polygon_PPA_SAS_UUT = Polygon([tuple(i) for i in polygon_dump])
    polygon_PPA_provided = Polygon([tuple(i) for i in self.polygon_dump])
    self.assertTrue(polygon_PPA_provided.equals(polygon_PPA_SAS_UUT))

  def generate_PCR_4_default_config(self, filename):
    # Step 1: Load PAL Database Record
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record['channelAssign'] = {
      "primaryAssignmen": {
        "lowFrequency": 3550000000,
        "highFrequency": 3560000000
      },
      "secondaryAssignment": {
        "lowFrequency": 3580000000,
        "highFrequency": 3590000000
      }
    }
    pal_record['userId'] = "pal_user"
    pal_record['palId'] = "pal/10-2017/123456789/A"

    # Step 2: Load the device_a in DP Test Harness
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 39.0119
    device_a['installationParam']['longitude'] = -98.4842
    device_a['userId'] = pal_record['licensee']

    # Step 2: Load the device_b in DP Test Harness
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 39.139836
    device_b['installationParam']['longitude'] = -97.770094
    device_b['userId'] = pal_record['licensee']


    config = {
      'device_a': device_a,
      'device_b': device_b,
      'pal_record': pal_record
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_4_default_config)
  def test_WINNF_FT_S_PCR_4(self, config_filename):
    # Load the Config file
    config = loadConfig(config_filename)
    device_a = config['device_a']
    pal_record = config['pal_record']
    device_b = config['device_b']

    # Step 1: Inject PAL record in SAS UUT
    self._sas_admin.InjectPalDatabaseRecord(pal_record)
    # Step 2: register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_a in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 2: register device_b in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_b in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 3: Triggers SAS UUT to create a PPA boundary
    cbsdIds = [device_a['cbsdSerialNumber'], device_b['cbsdSerialNumber']]
    palIds = [pal_record['palId']]
    response = self._sas_admin.TriggerPpaCreation(cbsdIds, palIds)
    self.assertEqual(response['response']['responseCode'], 103)


  def generate_PCR_5_default_config(self, filename):
    # Step 1: Load PAL Database Record
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record['channelAssign'] = {
      "primaryAssignmen": {
        "lowFrequency": 3550000000,
        "highFrequency": 3560000000
      },
      "secondaryAssignment": {
        "lowFrequency": 3580000000,
        "highFrequency": 3590000000
      }
    }
    pal_record['userId'] = "pal_user"
    pal_record['palId'] = "pal/10-2017/123456789/A"

    # Step 2: Load the device_a in DP Test Harness
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 39.0119
    device_a['installationParam']['longitude'] = -98.4842
    device_a['userId'] = pal_record['licensee']

    # Step 2: Load the device_b in DP Test Harness
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 39.139836
    device_b['installationParam']['longitude'] = -97.770094
    device_b['userId'] = pal_record['licensee']

    config = {
      'device_a': device_a,
      'device_b': device_b,
      'pal_record': pal_record
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_5_default_config)
  def test_WINNF_FT_S_PCR_5(self, config_filename):
    # Load the Config file
    config = loadConfig(config_filename)
    device_a = config['device_a']
    pal_record = config['pal_record']
    device_b = config['device_b']

    # Step 1: Inject PAL record SAS UUT
    self._sas_admin.InjectPalDatabaseRecord(pal_record)
    # Step 2: register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_a in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 2: register device_b in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_b in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 3: Triggers SAS UUT to create a PPA boundary
    cbsdIds = [device_a['cbsdSerialNumber'], device_b['cbsdSerialNumber']]
    palIds = [pal_record['palId']]
    response = self._sas_admin.TriggerPpaCreation(cbsdIds, palIds)
    self.assertEqual(response['response']['responseCode'], 103)

  def generate_PCR_6_default_config(self, filename):
    # Step 1: Load PAL Database Record
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record['channelAssign'] = {
      "primaryAssignmen": {
        "lowFrequency": 3550000000,
        "highFrequency": 3560000000
      },
      "secondaryAssignment": {
        "lowFrequency": 3580000000,
        "highFrequency": 3590000000
      }
    }
    pal_record['userId'] = "pal_user"
    pal_record['palId'] = "pal/10-2017/123456789/A"

    # Step 2: Load the device_a in DP Test Harness
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 39.0119
    device_a['installationParam']['longitude'] = -98.4842
    device_a['userId'] = pal_record['licensee']

    # Step 2: Load the device_b in DP Test Harness
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 39.139836
    device_b['installationParam']['longitude'] = -97.770094
    device_b['userId'] = pal_record['licensee']

    config = {
      'device_a': device_a,
      'device_b': device_b,
      'pal_record': pal_record
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_6_default_config)
  def test_WINNF_FT_S_PCR_6(self, config_filename):
    # Load the Config file
    config = loadConfig(config_filename)
    device_a = config['device_a']
    pal_record = config['pal_record']
    device_b = config['device_b']

    # Step 1: Inject PAL record SAS UUT
    self._sas_admin.InjectPalDatabaseRecord(pal_record)
    # Step 2: register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_a in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 2: register device_b in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_b in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 3: Triggers SAS UUT to create a PPA boundary
    cbsdIds = [device_a['cbsdSerialNumber'], device_b['cbsdSerialNumber']]
    palIds = [pal_record['palId']]
    # execute the pre-request PCR.1
    self.test_WINNF_FT_S_PCR_1('testcases/configs/test_WINNF_FT_S_PCR_1/default.config')
    response = self._sas_admin.TriggerPpaCreation(cbsdIds, palIds, self.polygon_dump)
    self.assertEqual(response['response']['responseCode'], 103)

  def generate_PCR_7_default_config(self, filename):
    # Step1: Load PAL Record
    pal_record = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record['channelAssign'] = {
      "primaryAssignmen": {
        "lowFrequency": 3550000000,
        "highFrequency": 3560000000
      },
      "secondaryAssignment": {
        "lowFrequency": 3580000000,
        "highFrequency": 3590000000
      }
    }
    pal_record['userId'] = "pal_user"
    pal_record['palId'] = "pal/10-2017/123456789/A"

    # Load the device_a in DP Test Harness
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 39.0119
    device_a['installationParam']['longitude'] = -98.4842
    device_a['userId'] = pal_record['licensee']

    # Load the device_b in DP Test Harness
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 39.139836
    device_b['installationParam']['longitude'] = -97.770094
    device_b['userId'] = pal_record['licensee']

    # Inject a PPA Zone Definition for a PPA using the PAL record
    current_time = datetime.now()
    end_time = current_time + datetime.timedelta(hours=10)
    end_time = str(end_time.replace(microsecond=0).isoformat()) + 'Z'
    start_time = current_time + datetime.timedelta(hours=-10)
    start_time = str(start_time.replace(microsecond=0).isoformat()) + 'Z'
    ppaInfo = {}
    ppaInfo['palId'] = pal_record['palId']
    ppaInfo['cbsdReferenceId'] = [device_a['cbsdSerialNumber'],device_b['cbsdSerialNumber']]
    ppaInfo['ppaBeginDate'] = start_time
    ppaInfo['ppaExpirationDate'] = end_time
    ppa_zone = json.load(open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_zone['ppaInfo'] = ppaInfo


    config = {
      'device_a': device_a,
      'device_b': device_b,
      'pal_record': pal_record,
      'ppa_zone': ppa_zone
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_7_default_config)
  def test_WINNF_FT_S_PCR_7(self, config_filename):
    # Load the Config file
    config = loadConfig(config_filename)
    device_a = config['device_a']
    pal_record = config['pal_record']
    device_b = config['device_b']
    ppa_zone = config['ppa_zone']

    # Step 1: Inject PAL record SAS UUT
    self._sas_admin.InjectPalDatabaseRecord(pal_record)
    # execute the pre-request PCR.1
    self.test_WINNF_FT_S_PCR_1('testcases/configs/test_WINNF_FT_S_PCR_1/default.config')
    ppa_zone['zoo'] = self.polygon_dump
    # Step 2: Inject a PPA Zone Definition for a PPA
    self._sas_admin.InjectZoneData(ppa_zone)
    # Step 3: register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_a in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 3: register device_b in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response of device_b in SAS UUT
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response
    # Step 4: Triggers SAS UUT to create a PPA boundary
    cbsdIds = [device_a['cbsdSerialNumber'], device_b['cbsdSerialNumber']]
    palIds = [pal_record['palId']]
    response = self._sas_admin.TriggerPpaCreation(cbsdIds, palIds)
    self.assertEqual(response['response']['responseCode'], 103)




























