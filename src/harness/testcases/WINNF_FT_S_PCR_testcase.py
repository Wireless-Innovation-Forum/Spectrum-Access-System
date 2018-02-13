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
from util import configurable_testcase,getRandomLatLongInPolygon, \
    loadConfig, makePpaAndPalRecordsConsistent, writeConfig, winnforum_testcase
from sas import _RequestGet
from shapely.geometry import Polygon

class PPACreationTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_PCR_1_default_config(self, filename):
    """ Generates the WinnForum configuration for PCR 1. """

    # Load PAL Database Records and devices Category A and B.
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))
    pal_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    ppa_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    pal_record_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    ppa_record_2 = json.load(
      open(os.path.join('testcases', 'testdata', 'ppa_record_1.json')))
    pal_record_1['userId'] = device_a['userId']
    pal_record_1['palId'] = "pal/10-2017/123456789/A"
    pal_record_2['userId'] = device_b['userId']
    pal_record_2['palId'] = "pal/10-2017/123456789/B"

    # Fix PAL frequency for device_a.
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    ppa_record_1, pal_record_1 = makePpaAndPalRecordsConsistent(ppa_record_1,
                                                            [pal_record_1],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            device_a['userId'])
    # Move device_a into the first PPA zone.
    device_a['installationParam']['latitude'], device_a['installationParam'][
               'longitude'] = getRandomLatLongInPolygon(ppa_record_1)
    device_a['userId'] = pal_record_1['licensee']

    # Fix PAL frequency for device_b.
    pal_low_frequency = 3600000000
    pal_high_frequency = 3650000000
    ppa_record_2, pal_record_2 = makePpaAndPalRecordsConsistent(ppa_record_2,
                                                            [pal_record_2],
                                                            pal_low_frequency,
                                                            pal_high_frequency,
                                                            device_a['userId'])
    device_b['installationParam']['latitude'], device_b['installationParam'][
               'longitude'] = getRandomLatLongInPolygon(ppa_record_2)
    device_b['userId'] = pal_record_2['licensee']

    config = {
        'device_a': device_a,
        'device_b': device_b,
        'pal_record_1': pal_record_1,
        'pal_record_2': pal_record_2

    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_1_default_config)
  def test_WINNF_FT_S_PCR_1(self, config_filename):
    """ Successful Maximum PPA Creation

    Checks PPA generated by SAS UUT shall be fully contained within the service area.
    """
    # Load the Config file
    config = loadConfig(config_filename)
    device_a = config['device_a']
    device_b = config['device_b']
    pal_record_1 = config['pal_record_1']
    pal_record_2 = config['pal_record_2']

    # Step 1: Inject one or more PAL records
    self._sas_admin.InjectPalDatabaseRecord(pal_record_1[0])
    self._sas_admin.InjectPalDatabaseRecord(pal_record_2[0])

    # Step 2: Register device_a in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})

    # Do registeration and check registration response of device_a and device_b in SAS UUT
    cbsd_ids = self.assertRegistered([device_a, device_b])

    # Step 3: Triggers SAS UUT to create a PPA boundary
    palIds = [pal_record_1['palId']]
    ppaIds = self._sas_admin.TriggerPpaCreation(cbsd_ids, palIds)

    self.assertGreaterEqual(len(ppaIds),0)
    # Step 4: Triggers the SAS UUT to generate the Full Activity Dump
    self._sas_admin.TriggerCreateActivityDump()

    # Step 5: SAS Test Harness uses the SAS-SAS protocol to retrieve the PPA zone
    full_activity_dump = self._sas.GetSasDumpRecord()
    ppa_record_url = None
    for dump_file in full_activity_dump['files']:
      if dump_file['recordType'] == 'zone':
        ppa_record_url = dump_file['url']
        break

    # Checking whether SAS dump data contains the ppa zone url
    self.assertIsNotNone(ppa_record_url)
    self.polygon_dump = self._sas.GetSasPPADumpRecord(ppa_record_url)

    # Step 6: Using PPA Creation Reference Model to calculate the maximum PPA
    devices_list = [device_a, device_b]
    pal_record_list = [pal_record_1]
    pal_low_frequency = pal_record_1['channelAssign']['primaryAssignmen']['lowFrequency']
    pal_high_frequency = pal_record_1['channelAssign']['primaryAssignmen']['highFrequency']

    # Triggers PPA creation reference model
    polygon_result = ppa_creation_model_byList(devices_list, pal_record_list, pal_record_1['userId'], pal_low_frequency, pal_high_frequency)
    polygon = polygon_result['features'][0]['geometry']['coordinates'][0]
    polygon = Polygon([tuple(i) for i in polygon])
    polygon_dump = Polygon([tuple(i) for i in self.polygon_dump])
    polygon_overlap = polygon.symmetric_difference(polygon_dump)

    # Check the Equation 8.3.1 in Test Specfification is satisified w.r t [n.12, R2-PAL-05]
    self.assertLessEqual(polygon_overlap.area, polygon.area * 0.1)