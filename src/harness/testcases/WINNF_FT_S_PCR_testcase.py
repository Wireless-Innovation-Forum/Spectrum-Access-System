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
import sas_testcase
import uuid
from shapely import ops
from full_activity_dump_helper import getFullActivityDumpSasUut
from reference_models.ppa import ppa
from reference_models.geo import drive, utils
from util import configurable_testcase, loadConfig, \
     makePalRecordsConsistent, writeConfig, getCertificateFingerprint, \
     makePpaAndPalRecordsConsistent, getCertFilename
from request_handler import HTTPError
from datetime import datetime, timedelta
import time

SAS_TEST_HARNESS_URL = 'https://test.harness.url.not.used/v1.2'

def getSasUutClaimedPpaBoundaryFilePath(config_filename):
  """Get the absolute file path SAS UUT claimed PPA boundary to be stored.

  Args:
    config_filename: The absolute file path of the configuration file used in PCR.1 test.
      It is required to differentiate SAS UUT claimed PPA boundary stored as result of
      PCR.1 test executed with different configuration file.

  Returns:
    An expected absolute file path of PPA zone to be stored which is received SAS UUT
      as part of PCR.1 test.

  """
  ppa_zone_data_dir_path = os.path.join('testcases', 'output',
                                        'test_WINNF_FT_S_PCR_1')
  ppa_zone_data_file_name = 'sas_uut_claimed_ppa_boundary_' + \
                            config_filename + '.json'
  ppa_zone_data_file_path = os.path.join(ppa_zone_data_dir_path,
                                         ppa_zone_data_file_name)
  return ppa_zone_data_file_path


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

    # Use the FIPS codes of adjacent census tracts.
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

    # Make PAL records consistent.
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
      'longitude'] = 39.0426, -100.4457
    device_c['installationParam']['heightType'] = 'AGL'

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
        'sasTestHarnessCert': getCertFilename('sas.cert'),
        'sasTestHarnessKey': getCertFilename('sas.key')
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_1_default_config)
  def test_WINNF_FT_S_PCR_1(self, config_filename):
    """Successful Maximum PPA Creation.

    Checks PPA generated by SAS UUT shall be fully contained within the service area.
    """
    # Load the Config file
    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list,
            'palRecords': list,
            'sasTestHarnessCert': basestring,
            'sasTestHarnessKey': basestring
        })

    # Register devices and  check response.
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # Asserts the REG-Conditional value doesn't exist in the registrationRequest,
    # it required to be exist in the registrationRequest data.
    assertRegConditionalsForPpaRefModel(config['registrationRequests'],
                                        config['conditionalRegistrationData'])

    # Trigger PPA creation to calculate maximum PPA boundary and check if any errors
    # encountered in PPA creation reference model.
    test_harness_ppa_geometry = ppa.PpaCreationModel(config['registrationRequests'],
                                                     config['palRecords'])

    # Inject the PAL records.
    for pal_record in config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

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
    ppa_zone_data_file_path = getSasUutClaimedPpaBoundaryFilePath(
        config_filename.split('/')[-1])
    ppa_zone_data_dir_path = os.path.dirname(ppa_zone_data_file_path)
    if not os.path.exists(ppa_zone_data_dir_path):
      os.makedirs(ppa_zone_data_dir_path)
    with open(ppa_zone_data_file_path, 'w') as file_handle:
      file_handle.write(
          json.dumps(uut_ppa_zone_data['zone'], indent=2, sort_keys=False,
                     separators=(',', ': ')))

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

    # Use the FIPS codes of adjacent census tracts.
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

    # Make PAL record consistent.
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
    device_c['installationParam']['heightType'] = 'AGL'

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
        'sasTestHarnessCert': getCertFilename('sas.cert'),
        'sasTestHarnessKey': getCertFilename('sas.key')
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

    # Register devices and  check response.
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # Asserts the REG-Conditional value doesn't exist in the registrationRequest,
    # it is required to be exist in the registrationRequest data.
    assertRegConditionalsForPpaRefModel(config['registrationRequests'],
                                        config['conditionalRegistrationData'])

    # Trigger PPA creation to calculate maximum PPA boundary and check if any errors
    # encountered in PPA creation reference model.
    test_harness_ppa_geometry = ppa.PpaCreationModel(config['registrationRequests'],
                                                     config['palRecords'])

    # Inject the PAL records.
    for pal_record in config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Prepares the PAL Ids to trigger ppa creation request.
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
    # File path where SAS UUT claimed ppa boundary generated in PCR.1 test.
    pcr_1_test_config_file_path = os.path.join('testcases', 'configs',
                                               'test_WINNF_FT_S_PCR_1',
                                               'default.config')
    sas_uut_claimed_ppa_boundary_file_path = getSasUutClaimedPpaBoundaryFilePath(
        'default.config')

    # SAS UUT claimed ppa boundary generated in PCR.1 test.
    try:
      with open(sas_uut_claimed_ppa_boundary_file_path, 'r') as claimed_ppa_file:
        user_claimed_ppa_contour = json.load(claimed_ppa_file)
    except IOError:
      raise RuntimeError('ConfigError:There is an error in reading path:%s \n\n'
                         % sas_uut_claimed_ppa_boundary_file_path)

    # Shrink the user claimed ppa boundary by approximately 1 kilometer.
    user_claimed_ppa_contour_feature_collection = utils.InsureFeatureCollection(
        utils.ShrinkAndCleanPolygon(
            user_claimed_ppa_contour['features'][0]['geometry'], 1e-2),
        as_dict=True)
    # Create the actual config
    config = {
        'configPCR_1': pcr_1_test_config_file_path,
        'userClaimedPpaContour': user_claimed_ppa_contour_feature_collection
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

    # Prepares the PAL Ids to trigger ppa creation request.
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
    test_harness_ppa_geometry = config['userClaimedPpaContour']['features'][0]['geometry']
    self.assertTrue(utils.PolygonsAlmostEqual(test_harness_ppa_geometry, uut_ppa_geometry))

  def generate_PCR_4_default_config(self, filename):
    """Generate the WinnForum configuration for PCR 4."""
    # Load PAL records.
    pal_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    pal_record_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_2.json')))

    # Use the FIPS codes of adjacent census tracts.
    pal_record_1['fipsCode'] = 20063955100
    pal_record_2['fipsCode'] = 20063955200

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

    # Make PAL records consistent.
    pal_records = makePalRecordsConsistent([pal_record_1, pal_record_2],
                                           pal_low_frequency, pal_high_frequency,
                                           device_a['userId'])

    # Set the values of CBSD location, antenna gain, and EIRP limit such that a
    # single PPA can be formed.
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = 39.0373, -100.4184
    device_b['installationParam']['latitude'], device_b['installationParam'][
        'longitude'] = 39.0378, -100.4785

    # At least one of the CBSDs is located outside the service area.
    device_c['installationParam']['latitude'], device_c['installationParam'][
        'longitude'] = 39.09755, -99.9179
    device_c['installationParam']['heightType'] = 'AGL'

    # Set the AntennaGain and EIRP capability chosen in a way that only one PPA zone is created
    # by those CBDSs
    device_a['installationParam']['eirpCapability'] = 30
    device_b['installationParam']['eirpCapability'] = 47
    device_c['installationParam']['eirpCapability'] = 30
    device_a['installationParam']['antennaGain'] = 16
    device_b['installationParam']['antennaGain'] = 16
    device_c['installationParam']['antennaGain'] = 16

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
        'palRecords': pal_records
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_4_default_config)
  def test_WINNF_FT_S_PCR_4(self, config_filename):
    """Unsuccessful PPA Creation with one or more CBSDs Outside Service Area.

    Checks SAS UUT rejects creation of a PPA boundary if at least one of the CBSDs
    included in the CBSD cluster list is located outside PAL holder service area.
    """
    # Load the Config file.
    config = loadConfig(config_filename)

    # Inject the PAL records.
    for pal_record in config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Register devices and check the response.
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # Prepares the PAL Ids to trigger ppa creation request.
    pal_ids = [record['palId'] for record in config['palRecords']]

    # Create PPA creation request to SAS UUT.
    ppa_creation_request = {
        "cbsdIds": cbsd_ids,
        "palIds": pal_ids
    }

    # Trigger PPA Creation to SAS UUT and expect the failure response.
    self.assertPpaCreationFailure(ppa_creation_request)

  def generate_PCR_5_default_config(self, filename):
    """Generate the WinnForum configuration for PCR 5."""
    # Load PAL records.
    pal_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))
    pal_record_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_2.json')))

    # Use the FIPS codes of adjacent census tracts.
    pal_record_1['fipsCode'] = 20063955100
    pal_record_2['fipsCode'] = 20063955200

    # Set the PAL frequency.
    pal_low_frequency = 3570000000
    pal_high_frequency = 3580000000

    # Load device info.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # light check to ensure CBSD userId is not same.
    self.assertNotEqual(device_a['userId'], device_b['userId'])

    # The userId of at least one of the CBSDs is not associated to the userId of
    # the PAL Holder configured in the PAL record for this service area.
    pal_records = makePalRecordsConsistent([pal_record_1, pal_record_2], pal_low_frequency,
                                           pal_high_frequency,
                                           device_a['userId'])

    # CBSDs are located inside the service area.
    device_a['installationParam']['latitude'], device_a['installationParam'][
        'longitude'] = 39.0373, -100.4184
    device_b['installationParam']['latitude'], device_b['installationParam'][
        'longitude'] = 39.0378, -100.4785

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
        'palRecords': pal_records
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_5_default_config)
  def test_WINNF_FT_S_PCR_5(self, config_filename):
    """Unsuccessful PPA Creation with one or more CBSDs Outside Service Area.

    Checks SAS UUT rejects creation of a PPA boundary if at least one of
    the CBSDs included in the CBSD cluster list does not belong to the PAL holder.
    """
    # Load the Config file.
    config = loadConfig(config_filename)

    # Inject the PAL records.
    for pal_record in config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Register devices and check the response.
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # Prepares the PAL Ids to trigger ppa creation request.
    pal_ids = [record['palId'] for record in config['palRecords']]

    # Create PPA creation request to SAS UUT.
    ppa_creation_request = {
        "cbsdIds": cbsd_ids,
        "palIds": pal_ids
    }

    # Trigger PPA Creation to SAS UUT and expect the failure response.
    # SAS does not create a PPA and generates an error.
    self.assertPpaCreationFailure(ppa_creation_request)

  def generate_PCR_6_default_config(self, filename):
    """Generate the WinnForum configuration for PCR 6."""
    # File path where SAS UUT claimed ppa boundary generated in PCR.1 test
    pcr_1_test_config_file_path = os.path.join('testcases', 'configs',
                                               'test_WINNF_FT_S_PCR_1',
                                               'default.config')
    sas_uut_claimed_ppa_boundary_file_path = getSasUutClaimedPpaBoundaryFilePath(
        'default.config')

    # Load SAS UUT claimed ppa boundary and check if any error while retrieving
    # SAS UUT claimed ppa boundary generated in PCR.1 test.
    try:
      with open(sas_uut_claimed_ppa_boundary_file_path, 'r') as claimed_ppa_file:
        user_claimed_ppa_contour = json.load(claimed_ppa_file)
    except IOError:
      raise RuntimeError('ConfigError:There is an error in reading path:%s \n\n'
                         % sas_uut_claimed_ppa_boundary_file_path)

    # Expand the user claimed ppa boundary by approximately 1 kilometer.
    user_claimed_ppa_contour_feature_collection = utils.InsureFeatureCollection(
        utils.ShrinkAndCleanPolygon(
            user_claimed_ppa_contour['features'][0]['geometry'], -1e-2),
        as_dict=True)
    # Create the actual config.
    config = {
        'configPCR_1': pcr_1_test_config_file_path,
        'userClaimedPpaContour': user_claimed_ppa_contour_feature_collection
    }

    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_6_default_config)
  def test_WINNF_FT_S_PCR_6(self, config_filename):
    """Unsuccessful PPA boundary Claimed by PAL Holder Not contained within Maximum PPA Boundary.

    SAS UUT shall reject a PPA boundary claimed by the PAL holder,
    that is not fully contained within the maximum PPA boundary created by SAS UUT.
    """
    # Load the Config file.
    config = loadConfig(config_filename)

    # Load the test_WINNF_FT_S_PCR_1 config. All other inputs must be identical
    # to those used in the corresponding configuration of PCR.1.
    pcr_1_test_config = loadConfig(config['configPCR_1'])

    # Inject the PAL records.
    for pal_record in pcr_1_test_config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Register devices and  check response.
    cbsd_ids = self.assertRegistered(pcr_1_test_config['registrationRequests'],
                                     pcr_1_test_config['conditionalRegistrationData'])

    # Prepares the PAL Ids to trigger ppa creation request.
    pal_ids = [record['palId'] for record in pcr_1_test_config['palRecords']]

    # Create PPA creation request with user claimed ppa contour.
    ppa_creation_request = {
        "cbsdIds": cbsd_ids,
        "palIds": pal_ids,
        "providedContour": config['userClaimedPpaContour']
    }

    # Trigger PPA Creation to SAS UUT.
    self.assertPpaCreationFailure(ppa_creation_request)

  def generate_PCR_7_default_config(self, filename):
    """Generate the WinnForum configuration for PCR 7."""
    # File path where SAS UUT claimed ppa boundary generated in PCR.1 test
    pcr_1_test_config_file_path = os.path.join('testcases', 'configs',
                                               'test_WINNF_FT_S_PCR_1',
                                               'default.config')
    sas_uut_claimed_ppa_boundary_file_path = getSasUutClaimedPpaBoundaryFilePath(
        'default.config')

    # Load SAS UUT claimed ppa boundary and check if any error while retrieving
    # SAS UUT claimed ppa boundary generated in PCR.1 test.
    try:
      with open(sas_uut_claimed_ppa_boundary_file_path, 'r') as overlapped_ppa_file:
        overlapping_ppa_contour = json.load(overlapped_ppa_file)
    except IOError:
      raise RuntimeError('ConfigError:There is an error in reading path:%s \n\n'
                         % sas_uut_claimed_ppa_boundary_file_path)

    # Shrink the user claimed ppa boundary by approximately 1 kilometer.
    overlapping_ppa_contour_geometry = utils.ShrinkAndCleanPolygon(
        overlapping_ppa_contour['features'][0]['geometry'], 1e-2)

    # Create ppa_record where user claimed PPA contour will be replaced.
    overlapping_ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))

    # Update the user_claimed ppa contour geometry required for overlaps ppa.
    overlapping_ppa_record['zone'] = {'type':'FeatureCollection',
                                      'features': [
                                          {'type': 'Feature', 
                                           'properties': {}, 
                                           'geometry': overlapping_ppa_contour_geometry}
                                      ]}

    # Load PCR.1 configuration.
    pcr_1_test_config = loadConfig(pcr_1_test_config_file_path)

    # Set the pal_record used in PCR.1 tests.
    pcr_1_pal_records = pcr_1_test_config['palRecords']

    #updating the PPA record based on the PAL records
    overlapping_ppa_record ['ppaInfo']['palId'] = [pal['palId'] for pal in pcr_1_pal_records]
    overlapping_ppa_record ['id'] = 'zone/ppa/%s/%s/%s' % (overlapping_ppa_record['creator'],
                                                           overlapping_ppa_record['ppaInfo']['palId'][0],
                                                           uuid.uuid4().hex)

    overlapping_ppa_record ['ppaInfo']['ppaBeginDate'] = pcr_1_pal_records[0]['license']['licenseDate']
    overlapping_ppa_record ['ppaInfo']['ppaExpirationDate'] = pcr_1_pal_records[0]['license']['licenseExpiration']

    # Create the actual config.
    config = {
        'configPCR_1': pcr_1_test_config_file_path,
        'overlapPpaRecord': overlapping_ppa_record
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_PCR_7_default_config)
  def test_WINNF_FT_S_PCR_7(self, config_filename):
    """Overlapping PPA Boundaries.

    Checks SAS UUT shall doesnt create PPA zone within the service area.
    Checks SAS UUT shall confirm a valid PPA boundary claimed by the PAL holder,
    composed of one or more adjacent Census Tracts was overlapped by another
    PPA zone.
    """
    # Load the Config file.
    config = loadConfig(config_filename)

    # Load the test_WINNF_FT_S_PCR_1 config. All other inputs must be identical
    # to those used in the corresponding configuration of PCR.1.
    pcr_1_test_config = loadConfig(config['configPCR_1'])

    # Inject the PAL records.
    for pal_record in pcr_1_test_config['palRecords']:
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Inject the overlap ppa zone into SAS UUT.
    zone_id = self._sas_admin.InjectZoneData({'record': config['overlapPpaRecord']})
    self.assertTrue(zone_id)

    # Register devices and check the response.
    cbsd_ids = self.assertRegistered(pcr_1_test_config['registrationRequests'],
                                     pcr_1_test_config['conditionalRegistrationData'])

    # Prepares the PAL Ids to trigger ppa creation request.
    pal_ids = [record['palId'] for record in pcr_1_test_config['palRecords']]

    # Create PPA creation request with device which is already part of
    # existing PPA zone.
    ppa_creation_request = {
        "cbsdIds": cbsd_ids,
        "palIds": pal_ids
    }

    # Trigger PPA Creation to SAS UUT and check SAS UUT should not create PPA boundary
    # claimed by PAL holder was overlapped by PPA zone.
    self.assertPpaCreationFailure(ppa_creation_request)
