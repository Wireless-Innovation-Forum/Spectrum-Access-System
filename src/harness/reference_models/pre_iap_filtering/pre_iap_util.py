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

import shapely.geometry as sgeo
from reference_models.geo import vincenty
from sas_test_harness import generateCbsdReferenceId
from reference_models.geo import utils

# GWBL parameters
FSS_GWBL_PROTECTION_FREQ_RANGE = {'lowFrequency': 3650e6,
                                  'highFrequency': 3700e6}
FSS_GWBL_PROTECTION_DISTANCE_KM = 150


def purgeOverlappingGrants(cbsds, frequency_range):
  """Removes Grants from CBSDs that overlap with the given frequency range.

  Args:
    cbsds: List of |CbsdData| objects. Grants are removed from the input.
    frequency_range: The frequency range in Hz as a dictionary with keys
       'lowFrequency' and 'highFrequency'.
  """
  for cbsd in cbsds:
    cbsd['grants'] = [grant for grant in cbsd['grants']
                      if not checkForOverlappingGrants(grant, frequency_range)]


def checkForOverlappingGrants(grant, frequency_range):
  """Returns True if a grant overlaps with a given frequency range.

  If the lowFrequency or the highFrequency of the grant falls within the
  low and high frequencies of the given range then the grant is considered
  to be overlapping.

  Args:
    grant: A |GrantData| object dictionary defined in SAS-SAS spec
    frequency_range: The frequency range in Hz as a dictionary with keys
       'lowFrequency' and 'highFrequency'.
  """
  low_frequency_cbsd = grant['operationParam']['operationFrequencyRange']['lowFrequency']
  high_frequency_cbsd = grant['operationParam']['operationFrequencyRange']['highFrequency']
  low_frequency = frequency_range['lowFrequency']
  high_frequency = frequency_range['highFrequency']
  return ((low_frequency_cbsd <= low_frequency < high_frequency_cbsd) or
          (low_frequency_cbsd < high_frequency <= high_frequency_cbsd))


def getCbsdsWithinPolygon(cbsds, polygon):
  """Returns the list of all CBSDs within a polygon protection area.

  The returned CBSDs can lie either within the polygon or on its boundary.

  Args:
    cbsds: List of |CbsdData| dictionaries as defined in the SAS-SAS specification.
    polygon: A GeoJSON object containing polygon information.
  """
  cbsds_within_polygon = []
  polygon = utils.ToShapely(polygon['features'][0]['geometry'])
  for cbsd in cbsds:
    if not cbsd['grants']:
      continue
    cbsd_lat = cbsd['registration']['installationParam']['latitude']
    cbsd_lon = cbsd['registration']['installationParam']['longitude']
    point = sgeo.Point(cbsd_lon, cbsd_lat)
    # If the CBSD is within the polygon and has grants then add it to the list
    # TODO: check the need for touches() check
    if (polygon.contains(point) or polygon.touches(point)):
      cbsds_within_polygon.append(cbsd)

  return cbsds_within_polygon


def getPpaFrequencyRange(ppa_record, pal_records):
  """Determines the frequency range of the PPA from the PAL records.

  The first PAL ID is retrieved from the PPA information and the primary frequency
  assignment of that PAL ID is returned as the PPA frequency range.

  Args:
    ppa_record: A PPA record dictionary.
    pal_records: List of PAL record dictionaries.
  Returns:
    The operating frequency range of PPA as a dictionary with keys:
      'lowFrequency', 'highFrequency'
  Raises:
    ValueError: If the PAL records not found for PPA or if the frequency range in all
      PAL records are not same for PPA.
  """
  pal_frequencies = []
  ppa_pal_ids = ppa_record['ppaInfo']['palId']
  num_ppa_pal = len(ppa_pal_ids)
  # Get all the frequencies from the PAL records whose ID is present in the given PPA record
  for pal_record in pal_records:
    for pal_id in range(0, num_ppa_pal):
      if pal_record['palId'] == ppa_pal_ids[pal_id]:
        pal_frequency = pal_record['channelAssignment']['primaryAssignment']
        pal_frequencies.append(pal_frequency)
        break
    else:
      # Raise an exception if no matching PAL ID is found
      raise ValueError('PAL record %s not found for PPA ID %s' % (
          pal_record['palId'], ppa_record['id']))

  # Compare the frequencies of all the PAL records of the PPA
  for pal_frequency in pal_frequencies:
    if pal_frequency != pal_frequencies[0]:
      # If the frequency of the PAL records are not matching, raise an exception
      raise ValueError('The frequency range in all PAL'
                      'records are not same for PPA ID %s' % ppa_record['id'])

  # Return the first frequency range of the first matching PAL ID
  return pal_frequencies[0]


def getFssNeighboringCbsdsWithGrants(cbsds, fss_point,
                                     distance_km=FSS_GWBL_PROTECTION_DISTANCE_KM):
  """Returns the list of all CBSDs in the neighborhood of a FSS.

  The neighborhood is typically defined by all CBSD within 150 KMs and having
  at least one grant.

  Args:
    cbsds :  List of |CbsdData| dictionaries as defined in the SAS-SAS specification.
    fss_point: A tuple (longitude, latitude) of the FSS location.
    distance_km: The neighboring distance (km).
  """
  neighboring_cbsds_with_grants = []
  for cbsd in cbsds:
    if not cbsd['grants']:
      continue
    distance, _, _ = vincenty.GeodesicDistanceBearing(
        fss_point[1],
        fss_point[0],
        cbsd['registration']['installationParam']['latitude'],
        cbsd['registration']['installationParam']['longitude'])
    # Get the list of cbsds that are within 150kms from the FSS entity
    if distance <= distance_km and cbsd['grants']:
        neighboring_cbsds_with_grants.append(cbsd)
  return neighboring_cbsds_with_grants


def getFssNeighboringGwbl(gwbl_records, fss_records):
  """Returns the list of all FSS within 150km of GWBL and operating below 3700MHz.

  Args:
    gwbl_records: List of GWBL record dictionaries.
    fss_records: List of FSS records dictionaries.
  """
  list_of_fss_neighboring_gwbl = []
  gwbl_locations = [
      (gwbl_record['record']['deploymentParam'][0]['installationParam']['longitude'],
       gwbl_record['record']['deploymentParam'][0]['installationParam']['latitude'])
      for gwbl_record in gwbl_records]

  for fss_record in fss_records:
    fss_params = fss_record['record']['deploymentParam'][0]
    fss_high_freq = fss_params['operationParam']['operationFrequencyRange']['highFrequency']
    if fss_high_freq >= 3700e6:
      continue
    fss_latitude = fss_params['installationParam']['latitude']
    fss_longitude = fss_params['installationParam']['longitude']
    for gwbl_longitude, gwbl_latitude in gwbl_locations:
      # TODO: If speed limiting, quick filtering to speed up things with approx dist bound.
      # Exact distance filtering
      # Get the distance of the FSS entity from the GWBL polygon
      distance, _, _ = vincenty.GeodesicDistanceBearing(
          fss_latitude,
          fss_longitude,
          gwbl_latitude,
          gwbl_longitude)
      # Get the list of FSS entity that are 150kms from the GWBL area
      if distance <= FSS_GWBL_PROTECTION_DISTANCE_KM:
        list_of_fss_neighboring_gwbl.append(fss_record)
        break
  return list_of_fss_neighboring_gwbl
