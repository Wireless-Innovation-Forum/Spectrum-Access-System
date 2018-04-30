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

# A CBSD Grant.
class CbsdGrantInfo(namedtuple('CbsdGrantInfo',
                               [# Installation params
                                'latitude', 'longitude', 'height_agl',
                                'indoor_deployment', 'cbsd_category',
                                'antenna_azimuth', 'antenna_gain', 'antenna_beamwidth',
                                # Grant params
                                'max_eirp',
                                'low_frequency', 'high_frequency',
                                'is_managed_grant'])):
  """CbsdGrantInfo.

  Holds all parameters of a CBSD grant.
  Suitable to be used as a key in dictionaries and sets.

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
  __slots__ = ()

  def uniqueCbsdKey(self):
    """Returns unique CBSD key (ie key based on installation params only)."""
    return self[0:8]


def constructCbsdGrantInfo(reg_request, grant_request, is_managing_sas=True):
  """Constructs a |CbsdGrantInfo| tuple from the given data."""
  lat_cbsd = reg_request['installationParam']['latitude']
  lon_cbsd = reg_request['installationParam']['longitude']
  height_cbsd = reg_request['installationParam']['height']
  height_type_cbsd = reg_request['installationParam']['heightType']
  if height_type_cbsd == 'AMSL':
    # TODO(sbdt): move the feature of AMSL support within the prop models.
    altitude_cbsd = drive.terrain_driver.GetTerrainElevation(lat_cbsd, lon_cbsd)
    height_cbsd = height_cbsd - altitude_cbsd

  return CbsdGrantInfo(
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
    for grant in cbsd_data_record['grants']:
      grant_objects.append(
          constructCbsdGrantInfo(
              cbsd_data_record['registration'],
              grant,
              is_managing_sas=is_managing_sas))

  return grant_objects


def getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects):
  """Returns a list of |CbsdGrantInfo| for SAS UUT and peer SAS TH.

  Args:
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_objects: a list of FAD objects from SAS Test Harness
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
    grants.append(
        constructCbsdGrantInfo(
            reg_request,
            grant_request,
            is_managing_sas))

  return grants


def getAuthorizedGrantsFromDomainProxies(domain_proxies):
  """Returns a list of |CbsdGrantInfo| from some Domain Proxy objects.

  Args:
    domain_proxies: A list of DomainProxy objects to build |CbsdGrantInfo| from.
  Returns:
    A list of |CbsdGrantInfo| for each authorized grant in the given Domain Proxies.
  """
  grants = []
  for domain_proxy in domain_proxies:
    for cbsd in domain_proxy.getCbsdsWithAtLeastOneAuthorizedGrant():
      for grant in cbsd.getAuthorizedGrants():
        grants.append(
            constructCbsdGrantInfo(
                cbsd.getRegistrationRequest(),
                grant.getGrantRequest()))

  return grants
