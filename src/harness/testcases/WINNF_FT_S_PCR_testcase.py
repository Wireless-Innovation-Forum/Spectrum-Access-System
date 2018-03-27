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
"""  Implementation of PCR tests """

import json
import os
import sas
import sas_testcase
from shapely import ops
from reference_models.ppa import ppa
from reference_models.geo import CONFIG, census_tract, utils
from util import configurable_testcase, loadConfig, \
     makePalRecordsConsistent, writeConfig, getCertificateFingerprint

DEFAULT_ITU_DATAPATH = CONFIG.GetItuDir()
DEFAULT_TERRAIN_DATAPATH = CONFIG.GetTerrainDir()
DEFAULT_LANDCOVER_DATAPATH = CONFIG.GetLandCoverDir()
DEFAULT_CENSUSTRACTS_DATAPATH = CONFIG.GetCensusTractsDir()


def assertPpaWithinServiceArea(pal_records, ppa_zone_geometry):
  """ Check if the ppa zone geometry's boundary and interior intersect only
    with the interior of the service area (not its boundary or exterior).

  Args:
    pal_records: A list of pal records to compute service area based on census_tracts.
    ppa_zone_geometry: A PPA polygon dictionary in GeoJSON format.
  """

  census_tract_driver = census_tract.CensusTractDriver()

  # Get the census tract for each pal record and convert it to Shapely geometry.
  census_tracts_for_pal = [
      utils.ToShapely(census_tract_driver.GetCensusTract(pal['license']['licenseAreaIdentifier'])
                      ['features'][0]['geometry']) for pal in pal_records]
  pal_service_area = ops.cascaded_union(census_tracts_for_pal)

  # Convert GeoJSON dictionary to Shapely object.
  ppa_zone_shapely_geometry = utils.ToShapely(ppa_zone_geometry)

  return ppa_zone_shapely_geometry.buffer(-1e-6).within(pal_service_area)


class PpaCreationTestcase(sas_testcase.SasTestCase):
  """
  Implementation of PCR tests to verify the area of the non-overlapping
  difference between the maximum PPA boundary created by SAS UUT shall be no more than
  10% of the area of the maximum PPA boundary created by the Reference Model.
  """
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_PCR_1_default_config(self, filename):
    """ Generates the WinnForum configuration for PCR 1. """

    # Load PAL records.
    pal_record_a = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    pal_record_b = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_2.json')))

    # Set the values of fipsCode in pal_records_a and b to make them adjacent.
    # 20063955100 and 20063955200 respectively.
    pal_record_a['fipsCode'] = 20063955100
    pal_record_b['fipsCode'] = 20063955200

    # Set the PAL frequency.
    pal_low_frequency = 3570000000
    pal_high_frequency = 3580000000

    # Load device info.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Set the same user ID for all devices
    device_b['userId'] = device_a['userId']

    # Device_a is Category A.
    self.assertEqual(device_a['cbsdCategory'], 'A')

    # Device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')

    # Set the values of fipsCode in pal_records_a and b to make them adjacent.
    # 20063955100 and 20063955200 respectively
    pal_records = makePalRecordsConsistent([pal_record_a, pal_record_b],
                                           pal_low_frequency, pal_high_frequency,
                                           device_a['userId'])

    # Set the locations of devices to reside with in service area
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = 39.0373, -100.4184
    device_b['installationParam']['latitude'], device_b['installationParam'][
        'longitude'] = 39.0378, -100.4785

    # Set the AntennaGain and EIRP capability
    device_a['installationParam']['eirpCapability'] = 30
    device_b['installationParam']['eirpCapability'] = 47
    device_a['installationParam']['antennaGain'] = 16
    device_b['installationParam']['antennaGain'] = 16

    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    conditionals = [conditionals_b]
    del device_b['installationParam']
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['measCapability']

    # Create the actual config.
    devices = [device_a, device_b]
    config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'palRecords': pal_records,
        'sasTestHarnessCert': os.path.join('certs/sas.cert'),
        'sasTestHarnessKey': os.path.join('certs/sas.key')
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_1_default_config)
  def test_WINNF_FT_S_PCR_1(self, config_filename):
    """ Successful Maximum PPA Creation.

    Checks PPA generated by SAS UUT shall be fully contained within the service area.
    """

    # Load the Config file
    config = loadConfig(config_filename)

    # light checking of itu,terrain and landcover data path exists.
    self.assertTrue(os.path.exists(DEFAULT_ITU_DATAPATH),
                    msg='ITU Data path is not configured')
    self.assertTrue(os.path.exists(DEFAULT_TERRAIN_DATAPATH),
                    msg='Terrain Data path is not configured')
    self.assertTrue(os.path.exists(DEFAULT_LANDCOVER_DATAPATH),
                    msg='LandCover Data path is not configured')
    self.assertTrue(os.path.exists(DEFAULT_CENSUSTRACTS_DATAPATH),
                    msg='CensusTract Data path is not configured')

    # Inject the PAL records.
    for pal_record in config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Register devices and  check response.
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # Trigger SAS UUT to create a PPA boundary.
    pal_ids = [record['palId'] for record in config['palRecords']]
    ppa_creation_request = {
        "cbsdIds": cbsd_ids,
        "palIds": pal_ids
    }
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)

    # Verify ppa_id should not be None.
    self.assertIsNotNone(ppa_id)

    # Notify the SAS UUT about the SAS Test Harness.
    certificate_hash = getCertificateFingerprint(config['sasTestHarnessCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': self._sas._base_url})

    # As SAS is reset at the beginning of the test, the FAD records should contain
    # only one zone record containing the PPA that was generated. Hence the first
    # zone record is retrieved and verified if it matches the PPA ID.
    response = self.TriggerFullActivityDumpAndWaitUntilComplete(
        config['sasTestHarnessCert'], config['sasTestHarnessKey'])
    self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
    ppa_zone_data = []

    # Download 'zone' dump file.
    for dump_file in response['files']:
      self.assertContainsRequiredFields("ActivityDumpFile.schema.json", dump_file)
      downloaded_file = None
      if dump_file['recordType'] == 'zone':
        url = str(dump_file['url']).strip()
        downloaded_file = self._sas.DownloadFile(url, config['sasTestHarnessCert'],
                                                 config['sasTestHarnessKey'])
        ppa_zone_data.extend(downloaded_file['recordData'])

    # Check if the retrieved FAD PPA zone record matches the PPA ID that was generated
    # using the admin API.
    self.assertEqual(ppa_zone_data[0]['id'], ppa_id)
    uut_ppa_geometry = ppa_zone_data[0]['zone']['features'][0]['geometry']

    # Configure the Census Tract Directory that the PPA uses
    ppa.ConfigureCensusTractDriver(DEFAULT_CENSUSTRACTS_DATAPATH)

    # PpaCreationModel requires the input registrationRequests to have 'installationParam'.
    # But this parameter is removed for devices where conditionals are pre-loaded.
    # Adding the 'installationParam' into registrationRequests by taking the
    # corresponding values from conditionalRegistrationData.
    for device in config['registrationRequests']:
      if not device.has_key('installationParam'):
        for conditional_params in config['conditionalRegistrationData']:
          # Check if FCC_ID+Serial_Number present in registrationRequest
          # and conditional_params match and add the 'installationParam'.
          if conditional_params['fccId'] == device['fccId'] and \
                          conditional_params['cbsdSerialNumber'] == device['cbsdSerialNumber']:
            device.update({
                'installationParam': conditional_params['installationParam']
            })
            device.update({
                'cbsdCategory': conditional_params['cbsdCategory']
            })

    # Trigger PPA creation.
    test_harness_ppa_geometry = ppa.PpaCreationModel(
        config['registrationRequests'], config['palRecords'])

    # Check if the PPA generated by the SAS UUT is fully contained within the service area.
    self.assertTrue(assertPpaWithinServiceArea(config['palRecords'], uut_ppa_geometry),
                    msg="PPA Zone is not within service area")

    # Check the Equation 8.3.1 in Test Specfification is satisified w.r t [n.12, R2-PAL-05]
    # Check the area of the non-overlapping difference between
    # the maximum PPA boundary created by SAS UUT shall be no more than 10% of the area
    # of the maximum PPA boundary created by the Reference Model.
    self.assertTrue(utils.PolygonsAlmostEqual(test_harness_ppa_geometry, uut_ppa_geometry))
