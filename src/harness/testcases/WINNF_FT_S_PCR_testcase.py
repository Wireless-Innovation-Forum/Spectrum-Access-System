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

"""Implementation of PCR tests."""
import json
import logging
import os
import signal
import time
import subprocess
import sas_testcase
from shapely import ops
from full_activity_dump_helper import getFullActivityDumpSasUut
from reference_models.ppa import ppa
from reference_models.geo import drive, utils
from util import configurable_testcase, loadConfig, \
     makePalRecordsConsistent, writeConfig, getCertificateFingerprint
TEST_CONFIG_COMMAND = 'cd reference_models;python test_config.py'
SAS_TEST_HARNESS_URL = 'https://test.harness.url.not.used/v1.2'


def isPpaWithinServiceArea(pal_records, ppa_zone_geometry):
  """Check if the ppa zone geometry with in service area then return True.

  Checks the ppa zone geometry's boundary and interior intersect only with the
  interior of the service area (not its boundary or exterior).

  Args:
    pal_records: A list of pal records to compute service area based on
      census_tracts.
    ppa_zone_geometry: A PPA polygon dictionary in GeoJSON format.

  Returns:
    A value is the boolean with the value as True if the ppa zone geometry's
      boundary and interior intersect with in the interior of the service
      area otherwise value as false.

  """
  # Get the census tract for each pal record and convert it to Shapely
  # geometry.
  census_tracts_for_pal = [
      utils.ToShapely(drive.census_tract_driver.GetCensusTract(
          pal['license']['licenseAreaIdentifier'])
                      ['features'][0]['geometry']) for pal in pal_records]
  pal_service_area = ops.cascaded_union(census_tracts_for_pal)

  # Convert GeoJSON dictionary to Shapely object.
  ppa_zone_shapely_geometry = utils.ToShapely(ppa_zone_geometry)

  return ppa_zone_shapely_geometry.buffer(-1e-6).within(pal_service_area)


def assertRegConditionalsForPpaRefModel(registration_request,
                                        conditional_registration_data):
  """Check the REG Conditionals for PPA creation model and raises an exception.

  Performs the assert to check installationParam present in
  registrationRequests or conditional registration data and raises an exception.
  PpaCreationModel requires the input registrationRequests to have
  'installationParam'. But this parameter is removed for devices where
  conditionals are pre-loaded. Adding the 'installationParam' into
  registrationRequests by taking the corresponding values from
  conditionalRegistrationData.

  Args:
    registration_request: A list of individual CBSD registration
      requests (each of which is itself a dictionary).
    conditional_registration_data: A list of individual CBSD registration
      data that need to be preloaded into SAS (each of which is a dictionary).
      data that need to be preloaded into SAS (each of which is a dictionary).
      the fccId and cbsdSerialNumber fields are required, other fields are
      optional but required for ppa reference model.

  Raises:
    It will throws an exception if the installationParam object and required
      fields is not found in conditionalRegistrationData and registrationRequests
      for category B.

  """
  for device in registration_request:
    if 'installationParam' not in device:
      install_param_assigned = False
      for conditional_params in conditional_registration_data:
        # Check if FCC_ID+Serial_Number present in registrationRequest
        # and conditional_params match and add the 'installationParam'.
        if (conditional_params['fccId'] == device['fccId'] and
                conditional_params['cbsdSerialNumber'] == device['cbsdSerialNumber']):
          device.update({'installationParam': conditional_params['installationParam']})
          install_param_assigned = True
          # If the cbsdCategory is not present in registration request then
          # assign it to the cbsdCategory in conditional_params.
          if 'cbsdCategory' not in device:
            device.update({'cbsdCategory': conditional_params.get('cbsdCategory',
                                                                  'B')})
      # Raise an exception if InstallationParam is not found in the conditionals.
      if not install_param_assigned:
        raise Exception("InstallationParam not found in conditionals for device "
                        "%s:%s" % (device['fccId'], device['cbsdSerialNumber']))


class PpaCreationTestcase(sas_testcase.SasTestCase):
  """Implementation of PCR tests.

  Checks the area of the non-overlapping difference between the maximum PPA boundary
  created by SAS UUT shall be no more than 10% of the area of the maximum PPA boundary
  created by the Reference Model for different varying condition and verify the SAS UUT
  is able to create PPA zone or error.
  """

  @classmethod
  def setUpClass(cls):
    """Verify the reference model configuration is proper for the test setup."""
    # Verify reference model configuration by executing the test_config.py to
    # determine success or failure based on the verification result to proceed the
    # test case execution.

    test_config_setup_verification = subprocess.check_output(TEST_CONFIG_COMMAND,
                                                             shell=True)
    logging.debug("test_config_setup_verification:%s", test_config_setup_verification)
    assert 'SUCCESS' in test_config_setup_verification, test_config_setup_verification

  @classmethod
  def tearDownClass(cls):
    pass

  def triggerPpaCreationAndWaitUntilComplete(self, ppa_creation_request):
    """Triggers PPA Creation Admin API and returns PPA ID if the creation status is completed.

    Triggers PPA creation to the SAS UUT. Checks the status of the PPA creation
    by invoking the PPA creation status API. If the status is complete then the
    PPA ID is returned. The status is checked every 10 secs for upto 2 hours.
    Exception is raised if the PPA creation returns error or times out.

    Args:
      ppa_creation_request: A dictionary with a multiple key-value pair containing the
        "cbsdIds", "palIds" and optional "providedContour"(a GeoJSON object).

    Returns:
      A Return value is string format of the PPA ID.

    """
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)

    # Verify ppa_id should not be None.
    self.assertIsNotNone(ppa_id, msg="PPA ID received from SAS UUT as result of "
                                     "PPA Creation is None")

    logging.info('TriggerPpaCreation is in progress')

    # Triggers most recent PPA Creation Status immediately and checks for the
    # status of activity every 10 seconds until it is completed. If the status
    # is not changed within 2 hours it will throw an exception.
    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                  (_ for _ in ()).throw(
                      Exception('Most Recent PPA Creation Status Check Timeout')))

    # Timeout after 2 hours if it's not completed.
    signal.alarm(7200)

    # Check the Status of most recent ppa creation every 10 seconds.
    while not self._sas_admin.GetPpaCreationStatus()['completed']:
      time.sleep(10)

    # Additional check to ensure whether PPA creation status has error.
    self.assertFalse(self._sas_admin.GetPpaCreationStatus()['withError'],
                     msg='There was an error while creating PPA')
    signal.alarm(0)

    return ppa_id

  def triggerFadGenerationAndRetrievePpaZone(self, ssl_cert, ssl_key):
    """Triggers FAD and Retrieves PPA Zone Record.

    Pulls FAD from SAS UUT. Retrieves the ZoneData Records from FAD,
    checks that only one record is present.

    Args:
      ssl_cert: Path to SAS type cert file to be used for pulling FAD record.
      ssl_key: Path to SAS type key file to be used for pulling FAD record.

    Returns:
      A PPA record of format of ZoneData Object.

    """
    # Notify the SAS UUT about the SAS Test Harness.
    certificate_hash = getCertificateFingerprint(ssl_cert)
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TEST_HARNESS_URL})

    # As SAS is reset at the beginning of the test, the FAD records should
    # contain only one zone record containing the PPA that was generated.
    # Hence the first zone record is retrieved.
    uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin, ssl_cert,
                                        ssl_key)

    # Check if the retrieved FAD that has valid and at least one
    # PPA zone record.
    uut_ppa_zone_data = uut_fad.getZoneRecords()
    self.assertEquals(len(uut_ppa_zone_data), 1,
                      msg='There is no single PPA Zone record received from SAS'
                          ' UUT')

    return uut_ppa_zone_data[0]

  def generate_PCR_1_default_config(self, filename):
    """Generate the WinnForum configuration for PCR 1."""
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

    # Set the AntennaGain and EIRP capability.
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
        'sasTestHarnessCert': os.path.join('certs', 'sas.cert'),
        'sasTestHarnessKey': os.path.join('certs', 'sas.key')
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_1_default_config)
  def test_WINNF_FT_S_PCR_1(self, config_filename):
    """Successful Maximum PPA Creation.

    Checks PPA generated by SAS UUT shall be fully contained within the service area.
    """
    # Load the Config file
    config = loadConfig(config_filename)

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

    # Trigger PPA Creation to SAS UUT.
    ppa_id = self.triggerPpaCreationAndWaitUntilComplete(ppa_creation_request)
    logging.debug('ppa_id received from SAS UUT:%s', ppa_id)

    # Notify SAS UUT about SAS Harness and trigger Full Activity Dump and
    # retrieves the PPA Zone record.
    uut_ppa_zone_data = self.triggerFadGenerationAndRetrievePpaZone(
        ssl_cert=config['sasTestHarnessCert'],
        ssl_key=config['sasTestHarnessKey'])

    # Asserts the REG-Conditional value doesn't exist in the registrationRequest,
    # it required to be exist in the registrationRequest data.
    assertRegConditionalsForPpaRefModel(config['registrationRequests'],
                                        config['conditionalRegistrationData'])

    # Trigger PPA creation.
    test_harness_ppa_geometry = ppa.PpaCreationModel(
        config['registrationRequests'], config['palRecords'])

    # Check if the PPA generated by the SAS UUT is fully contained within the
    # service area.
    logging.debug("SAS UUT PPA - retrieved through FAD:%s",
                  json.dumps(uut_ppa_zone_data, indent=2, sort_keys=False,
                             separators=(',', ': ')))
    logging.debug("Reference model PPA - retrieved through PpaCreationModel:%s",
                  json.dumps(json.loads(test_harness_ppa_geometry), indent=2,
                             sort_keys=False,
                             separators=(',', ': ')))

    uut_ppa_geometry = uut_ppa_zone_data['zone']['features'][0]['geometry']
    self.assertTrue(isPpaWithinServiceArea(config['palRecords'], uut_ppa_geometry),
                    msg="PPA Zone is not within service area")

    # Check the Equation 8.3.1 in Test Specfification is satisified w.r t
    # [n.12, R2-PAL-05]. Check the area of the non-overlapping difference between
    # the maximum PPA boundary created by SAS UUT shall be no more than 10% of the area
    # of the maximum PPA boundary created by the Reference Model.
    self.assertTrue(utils.PolygonsAlmostEqual(test_harness_ppa_geometry,
                                              uut_ppa_geometry))
