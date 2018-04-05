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

"""Reference data model.

This defines the common objects used by the reference models, and
the utility routines for creating them for example from FAD objects.
"""
from collections import namedtuple
import enum
from reference_models.geo import drive


class ProtectedEntityType(enum.Enum):
  """The protected entity type.
  """
  GWPZ_AREA = 1
  PPA_AREA = 2
  FSS_CO_CHANNEL = 3
  FSS_BLOCKING = 4
  ESC = 5
  DPA = 6


# A protection constraint.
ProtectionConstraint = namedtuple('ProtectionConstraint',
                                  ['latitude', 'longitude',
                                   'low_frequency', 'high_frequency',
                                   'entity_type'])

class CbsdGrantInfo(object):
  """CbsdGrantInfo.

  Holds all parameters of a CBSD grant.

  Attributes:
    latitude: The CBSD latitude (degrees).
    longitude: The CBSD longitude (degrees).
    height_agl: The height above ground level (meters).
    indoor_deployment: True if indoor, False if outdoor.
    antenna_azimuth: The antenna pointing azimuth relative to true north and defined
      in clockwise fashion.
    antenna_gain: The antenna nominal gain (dBi).
    antenna_beamwidth: The 3dB antenna beamwidth (degrees).
    cbsd_category: Either 'A' for Cat A or 'B' for Cat B CBSD.
    max_eirp: The maximum EIRP of the CBSD (dBm).
    low_frequency: The grant min frequency (Hz).
    high_frequency: The gran max frequency (Hz).
    is_managed_grant: True iff the grant belongs to the managing SAS.
  """
  __slots__ = ('latitude', 'longitude', 'height_agl', 'indoor_deployment',
               'antenna_azimuth', 'antenna_gain','antenna_beamwidth',
               'cbsd_category', 'max_eirp', 'low_frequency', 'high_frequency',
               'is_managed_grant', 'grant_index')
  def __init__(self, is_managed_grant=True, grant_index=None, **kwargs):
    for attr in self.__slots__[:-2]:
      setattr(self, attr, kwargs[attr])
    self.is_managed_grant = is_managed_grant
    self.grant_index = grant_index

  def __repr__(self):
    attrs = ('%s=%r' % (attr, getattr(self, attr)) for attr in self.__slots__)
    return 'CbsdGrantInfo(%s)' % ', '.join(attrs)


def getAllGrantInfoFromCbsdDataDump(cbsd_data_records, is_managing_sas=True):
  """Returns a list of |CbsdGrantInfo| from FAD object.

  Args:
    cbsd_data_records: A list of |CbsdData| objects retrieved from FAD records.
    is_managing_sas: Flag indicating if the `cbsd_data_record` from the managing SAS
      (True) or a peer SAS (False).
  """

  grant_objects = []

  # Loop over each CBSD grant
  for cbsd_data_record in cbsd_data_records:
    registration = cbsd_data_record['registration']
    grants = cbsd_data_record['grants']

    # Check CBSD location
    lat_cbsd = registration['installationParam']['latitude']
    lon_cbsd = registration['installationParam']['longitude']
    height_cbsd = registration['installationParam']['height']
    height_type_cbsd = registration['installationParam']['heightType']
    if height_type_cbsd == 'AMSL':
      # TODO(sbdt): move the feature of AMSL support within the prop models.
      altitude_cbsd = drive.terrain_driver.GetTerrainElevation(lat_cbsd, lon_cbsd)
      height_cbsd = height_cbsd - altitude_cbsd

    for grant in grants:
      # Return CBSD information
      cbsd_grant = CbsdGrantInfo(
        # Get information from the registration
        latitude=lat_cbsd,
        longitude=lon_cbsd,
        height_agl=height_cbsd,
        indoor_deployment=registration['installationParam']['indoorDeployment'],
        antenna_azimuth=registration['installationParam']['antennaAzimuth'],
        antenna_gain=registration['installationParam']['antennaGain'],
        antenna_beamwidth=registration['installationParam']['antennaBeamwidth'],
        cbsd_category=registration['cbsdCategory'],
        max_eirp=grant['operationParam']['maxEirp'],
        low_frequency=grant['operationParam']['operationFrequencyRange']['lowFrequency'],
        high_frequency=grant['operationParam']['operationFrequencyRange']['highFrequency'],
        is_managed_grant=is_managing_sas)
      grant_objects.append(cbsd_grant)
  return grant_objects


def getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects):
  """Returns a list of |CbsdGrantInfo| for SAS UUT and peer SAS TH.

  Args:
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
  """
  # List of CBSD grant tuples extracted from FAD record
  grants = getAllGrantInfoFromCbsdDataDump(
      sas_uut_fad_object.getCbsdRecords(), True)
  for fad in sas_th_fad_objects:
    grants.extend(getAllGrantInfoFromCbsdDataDump(
        fad.getCbsdRecords(), False))

  return grants


def getGrantsFromRequests(registration_requests, grant_requests, is_managing_sas=True):
  """Returns a list of |CbsdGrantInfo| from some registration/grant requests.

  Args:
    registration_requests: A list of CBSD registration requests, each one being a
      dict containing the CBSD registration information (field 'installationParam').
    grant_requests: A list of CBSD grant requests related to the corresponding
      `registration_request`, each one being a dict containing the grant information
     (field 'operationParam').
    is_managing_sas: Flag indicating if the `cbsd_data_record` from the managing SAS
      (True) or a peer SAS (False).
  """
  grants = []
  for reg_request, grant_request in zip(registration_requests, grant_requests):
    # Return CBSD information
    lat_cbsd = reg_request['installationParam']['latitude']
    lon_cbsd = reg_request['installationParam']['longitude']
    height_cbsd = reg_request['installationParam']['height']
    height_type_cbsd = reg_request['installationParam']['heightType']
    if height_type_cbsd == 'AMSL':
      # TODO(sbdt): move the feature of AMSL support within the prop models.
      altitude_cbsd = drive.terrain_driver.GetTerrainElevation(lat_cbsd, lon_cbsd)
      height_cbsd = height_cbsd - altitude_cbsd

    cbsd_grant = CbsdGrantInfo(
        # Get information from the registration
        latitude=lat_cbsd,
        longitude=lon_cbsd,
        height_agl=height_cbsd,
        indoor_deployment=reg_request['installationParam']['indoorDeployment'],
        antenna_azimuth=reg_request['installationParam']['antennaAzimuth'],
        antenna_gain=reg_request['installationParam']['antennaGain'],
        antenna_beamwidth=reg_request['installationParam']['antennaBeamwidth'],
        cbsd_category=reg_request['cbsdCategory'],
        max_eirp=grant_request['operationParam']['maxEirp'],
        low_frequency=grant_request['operationParam']['operationFrequencyRange']['lowFrequency'],
        high_frequency=grant_request['operationParam']['operationFrequencyRange']['highFrequency'],
        is_managed_grant=is_managing_sas)

    grants.append(cbsd_grant)

  return grants
