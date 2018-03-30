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


def assertRegConditionalsForPpaRefModel(registration_requests,
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
    registration_requests: A list of individual CBSD registration
      requests (each of which is itself a dictionary).
    conditional_registration_data: A list of individual CBSD registration
      data that need to be preloaded into SAS (each of which is a dictionary).
      the fccId and cbsdSerialNumber fields are required, other fields are
      optional but required for ppa reference model.

  Raises:
    Exception: If the installationParam object and required
      fields is not found in conditionalRegistrationData and registrationRequests
      for category B then raises an exception.

  """
  for device in registration_requests:
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
            # Causes KeyError: 'cbsdCategory' if 'cbsdCategory' does not exist
            device['cbsdCategory'] = conditional_params['cbsdCategory']
          break
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
    device_c = json.load(
      open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Set the same user ID for all devices
    device_b['userId'] = device_a['userId']
    device_c['userId'] = device_a['userId']

    # Device_a is Category A.
    self.assertEqual(device_a['cbsdCategory'], 'A')

    # Device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')

    # Set the values of fipsCode in pal_records_a and b to make them adjacent.
    # 20063955100 and 20063955200 respectively
    pal_records = makePalRecordsConsistent([pal_record_a, pal_record_b],
                                           pal_low_frequency, pal_high_frequency,
                                           device_a['userId'])

    # Set the locations of devices to reside with in service area.
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = 39.0373, -100.4184
    device_b['installationParam']['latitude'], device_b['installationParam'][
        'longitude'] = 39.0378, -100.4785

    # placed the device_c in between device_a and device_b within service area.
    device_c['installationParam']['latitude'], device_c['installationParam'][
      'longitude'] = 39.0378, -100.4463

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
    devices = [device_a, device_b, device_c]
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

    # Write SAS UUT PPA to output directory of PCR.1 test.
    # PPA Zone received from SAS UUT in PCR.1 test will be considered as input
    # for PCR 3,PCR 6 and PCR 7 tests.
    ppa_zone_data_dir_path = os.path.join('testcases', 'output', 'test_WINNF_FT_S_PCR_1')
    ppa_zone_data_file_name = 'sas_uut_claimed_ppa_boundary_' + \
                              config_filename.split('/')[-1] + '.json'
    ppa_zone_data_file_path = os.path.join(ppa_zone_data_dir_path,
                                           ppa_zone_data_file_name)
    if not os.path.exists(ppa_zone_data_dir_path):
      os.makedirs(ppa_zone_data_dir_path)
    with open(ppa_zone_data_file_path, 'w') as file_handle:
      file_handle.write(
          json.dumps(config, indent=2, sort_keys=False, separators=(',', ': ')))

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

  def generate_PCR_2_default_config(self, filename):
    """Generate the WinnForum configuration for PCR 2."""
    # Load PAL records.
    pal_record_a = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    pal_record_b = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_2.json')))

    # Set the values of fipsCode in pal_records_a and pal_records_b to make them adjacent.
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
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Set the same user ID for all devices.
    device_b['userId'] = device_a['userId']
    device_c['userId'] = device_a['userId']

    # Device_a is Category A.
    self.assertEqual(device_a['cbsdCategory'], 'A')

    # Device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')

    # Set the values of fipsCode in pal_records_a and b to make them adjacent.
    # 20063955100 and 20063955200 respectively.
    pal_records = makePalRecordsConsistent([pal_record_a, pal_record_b],
                                           pal_low_frequency, pal_high_frequency,
                                           device_a['userId'])

    # Set the values of CBSD location, antenna gain, and EIRP limit such that a
    # single PPA can be formed.
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = 38.74021, -100.53862

    # At least one of the CBSDs is close to the boundary of the Service Area,
    # so that -96 dBm/10 MHz protection contour extends beyond the service area boundary.
    device_b['installationParam']['latitude'], device_b['installationParam'][
        'longitude'] = 38.70645, -100.46034

    # placed the device_c in between device_a and device_b within service area.
    device_c['installationParam']['latitude'], device_c['installationParam'][
        'longitude'] = 38.72281, -100.50103

    # Set the AntennaGain and EIRP capability in a way that only
    # one PPA zone is created by those CBDSs using PPA Creation Reference Model.
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
    devices = [device_a, device_b, device_c]
    config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'palRecords': pal_records,
        'sasTestHarnessCert': os.path.join('certs', 'sas.cert'),
        'sasTestHarnessKey': os.path.join('certs', 'sas.key')
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_2_default_config)
  def test_WINNF_FT_S_PCR_2(self, config_filename):
    """Successful Maximum PPA Boundary Creation Clipped by Service Area Boundary.

    Checks the maximum PPA boundary, being clipped by the Service Area composed of
    one or more adjacent Census Tracts.
    Checks PPA generated by SAS UUT shall be fully contained within the service area.
    """
    # Load the Config file.
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

    # Trigger Full Activity Dump and retrieves the PPA Zone record.
    uut_ppa_zone_data = self.triggerFadGenerationAndRetrievePpaZone(
        ssl_cert=config['sasTestHarnessCert'],
        ssl_key=config['sasTestHarnessKey'])

    # Asserts the REG-Conditional value doesn't exist in the registrationRequest,
    # it is required to be exist in the registrationRequest data.
    assertRegConditionalsForPpaRefModel(config['registrationRequests'],
                                        config['conditionalRegistrationData'])

    # Trigger PPA Creation to SAS UUT.
    test_harness_ppa_geometry = ppa.PpaCreationModel(config['registrationRequests'],
                                                     config['palRecords'])

    # Check if the PPA generated by the SAS UUT is fully contained within the service area.
    logging.debug("SAS UUT PPA - retrieved through FAD:%s",
                  json.dumps(uut_ppa_zone_data, indent=2, sort_keys=False,
                             separators=(',', ': ')))
    logging.debug("Reference model PPA - retrieved through PpaCreationModel:%s",
                  json.dumps(json.loads(test_harness_ppa_geometry), indent=2, sort_keys=False,
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

  def generate_PCR_3_default_config(self, filename):
    """Generate the WinnForum configuration for PCR 3."""
    # File path where SAS UUT claimed ppa boundary generated in PCR.1 test
    sas_uut_claimed_ppa_boundary_file_path = os.path.join('testcases', 'output',
                                                          'test_WINNF_FT_S_PCR_1',
                                                          'sas_uut_claimed_ppa_boundary_'
                                                          'default.config.json')

    # Load SAS UUT claimed ppa boundary and check if any error while retrieving
    # SAS UUT claimed ppa boundary generated in PCR.1 test.
    try:
      with open(sas_uut_claimed_ppa_boundary_file_path, 'r') as claimed_ppa_file:
        user_claimed_ppa_contour = json.load(claimed_ppa_file)
    except IOError:
      raise RuntimeError('ConfigError:There is an error in reading path:%s'
                         % sas_uut_claimed_ppa_boundary_file_path)

    # Shrink the user claimed ppa boundary by 1 kilometer.
    user_claimed_ppa_contour_shapely = utils.ToShapely(
        user_claimed_ppa_contour['features'][0]['geometry']).buffer(-1e-2)
    user_claimed_ppa_contour_geometry = json.loads(utils.ToGeoJson(
        user_claimed_ppa_contour_shapely))

    config = {
        'configPCR_1': os.path.join('testcases', 'configs', 'test_WINNF_FT_S_PCR_1',
                                    'default.config'),
        'userClaimedPpaContour': user_claimed_ppa_contour_geometry
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_3_default_config)
  def test_WINNF_FT_S_PCR_3(self, config_filename):
    """Successful PPA Confirmation with Claimed Boundary by PAL Holder.

    Checks PPA generated by SAS UUT shall be fully contained within the service area.
    Checks SAS UUT shall confirm a valid PPA boundary claimed by the PAL holder,
    composed of one or more adjacent Census Tracts.
    """
    # Load the Config file.
    config = loadConfig(config_filename)

    # Load the test_WINNF_FT_S_PCR_1 config. All other inputs must be identical
    # to those used in the corresponding configuration of PCR.1.
    pcr_1_test_config = loadConfig(config['configPCR_1'])

    # Inject the PAL records.
    for pal_record in pcr_1_test_config['palRecords']:
        self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Register devices and check the response.
    cbsd_ids = self.assertRegistered(pcr_1_test_config['registrationRequests'],
                                     pcr_1_test_config['conditionalRegistrationData'])

    # Trigger SAS UUT to create a PPA boundary.
    pal_ids = [record['palId'] for record in pcr_1_test_config['palRecords']]

    # Create PPA creation request with user claimed ppa contour.
    ppa_creation_request = {
        "cbsdIds": cbsd_ids,
        "palIds": pal_ids,
        "providedContour": config['userClaimedPpaContour']
    }

    # Trigger PPA Creation to SAS UUT.
    ppa_id = self.triggerPpaCreationAndWaitUntilComplete(ppa_creation_request)
    logging.debug('ppa_id received from SAS UUT:%s', ppa_id)

    # Trigger Full Activity Dump and retrieves the PPA Zone record.
    uut_ppa_zone_data = self.triggerFadGenerationAndRetrievePpaZone(
        ssl_cert=pcr_1_test_config['sasTestHarnessCert'],
        ssl_key=pcr_1_test_config['sasTestHarnessKey'])

    # Check if the PPA generated by the SAS UUT is fully contained within the service area.
    logging.debug("SAS UUT PPA - retrieved through FAD:%s",
                  json.dumps(uut_ppa_zone_data, indent=2, sort_keys=False,
                             separators=(',', ': ')))
    logging.debug("User claimed PPA boundary:%s",
                  json.dumps(config['userClaimedPpaContour'], indent=2, sort_keys=False,
                             separators=(',', ': ')))
    uut_ppa_geometry = uut_ppa_zone_data['zone']['features'][0]['geometry']
    self.assertTrue(isPpaWithinServiceArea(pcr_1_test_config['palRecords'], uut_ppa_geometry),
                    msg="PPA Zone is not within service area")

    # Check the maximum PPA boundary created by SAS UUT is identical with the maximum
    # PPA claimed boundary.
    test_harness_ppa_geometry = config['userClaimedPpaContour']
    self.assertTrue(utils.PolygonsAlmostEqual(test_harness_ppa_geometry, uut_ppa_geometry))

