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


def purgeOverlappingGrants(cbsds, frequency_range):
  """Removes Grants from CBSDs that overlap with the given frequency range.

  Args:
  cbsds: List of CbsdData objects. Grants are removed from the input.
  frequency_range: A dictionary with keys 'lowFrequency' and 'highFrequency'
  """
  for cbsd in cbsds:
    if not cbsd['grants']:
      continue
    cbsd['grants'] = [grant for grant in cbsd['grants']
                            if not checkForOverlappingGrants(grant, frequency_range)]

def checkForOverlappingGrants(grant, frequency_range):
  """Check if a grant overlaps with a given frequency range

  If the lowFrequency or the highFrequency of the grant falls within the
  low and high frequencies of the given range then the grant is considered
  to be overlapping.
  Args:
    grant: A GrantData object dictionary defined in SAS-SAS spec
    frequency_range: A dictionary with keys 'lowFrequency' and 'highFrequency'
  Returns:
    True if the grant overlaps else False
  """
  low_frequency_cbsd = grant['operationParam']['operationFrequencyRange']['lowFrequency']
  high_frequency_cbsd = grant['operationParam']['operationFrequencyRange']['highFrequency']
  low_frequency = frequency_range['lowFrequency']
  high_frequency = frequency_range['highFrequency']
  if (low_frequency_cbsd <= low_frequency < high_frequency_cbsd) or \
     (low_frequency_cbsd < high_frequency <= high_frequency_cbsd):
      return True
  return False


def getCbsdsWithinPolygon(cbsds, polygon):
  """Get the list of all CBSDs that are present within the polygon or on the 
  boundary of the Polygon

  Args:
    cbsds: List of CbsdData dictionaries as defined in the SAS-SAS specification.
    polygon: A GeoJSON object containing polygon information.
  Returns:
    List of CBSDs lying within or on the boundary of the protectionn area.
  """ 
  cbsds_within_polygon = []
  #polygon = sgeo.shape(polygon['features'][0]['geometry'])
  polygon = utils.ToShapely(polygon['features'][0]['geometry'])
  for cbsd in cbsds:
    cbsd_lat = cbsd['registrationRequest']['installationParam']['latitude']
    cbsd_long = cbsd['registrationRequest']['installationParam']['longitude']
    point = sgeo.Point(cbsd_lat, cbsd_long)

    # If the CBSD is within the polygon and has grants then add it to the list
    if (polygon.contains(point) or polygon.touches(point)) and cbsd['grants']:
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
    Operating frequency range of PPA.
  Raises:
    Exception: If the PAL records not found for PPA or if the frequency range in all
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
      raise Exception('PAL record %s not found for PPA ID %s' %(pal_record['palId'], ppa_record['id']))

  # Compare the frequencies of all the PAL records of the PPA
  for pal_frequency in pal_frequencies:
    if pal_frequency != pal_frequencies[0]:
      # If the frequency of the PAL records are not matching raise an exception
      raise Exception('The frequency range in all PAL records are not same for PPA ID %s' %ppa_record['id'])

  # Return the first frequency range of the first matching PAL ID
  return pal_frequencies[0]

def getFssNeighboringCbsdsWithGrants(cbsds, fss_record, distance):
  """Get the list of all CBSDs that lie within 150 KMs of FSS and have at least one grant.

  Args:
    cbsds :  List of CbsdData dictionaries as defined in the SAS-SAS specification.
    fss_record: A FSS record dictionary.
  Returns:
    List of CBSDs lying within 150 KMs of FSS and having at least one grant.
  """

  neighboring_cbsds_with_grants = []
  for cbsd in cbsds:
    distance_km, _, _ = vincenty.GeodesicDistanceBearing(
        fss_record['record']['deploymentParam'][0]['installationParam']['latitude'],
        fss_record['record']['deploymentParam'][0]['installationParam']['longitude'],
        cbsd['registrationRequest']['installationParam']['latitude'],
        cbsd['registrationRequest']['installationParam']['longitude'])
    # Get the list of cbsds that are within 150kms from the FSS entity
    if distance_km <= distance and cbsd['grants']:
        neighboring_cbsds_with_grants.append(cbsd)
  return neighboring_cbsds_with_grants


def getFssNeighboringGwbl(gwbl_records, fss_records, distance): 
  """Get the list of all fss that lie within 150 KMs of GWBL and operating below 3700 MHz

  Args:
    fss_records:  List of FSS records dictionary.
    gwbl_records: List of GWBL record dictionary.
  Returns:
    List of FSSs lying within 150 KMs of GWBL and operating below 3700000000.
  """

  list_of_fss_neighboring_gwbl = []
  for fss_record in fss_records:
    for gwbl_record in gwbl_records:
      # Get the distance of the FSS entity from the GWBL polygon
      distance_km, _, _ = vincenty.GeodesicDistanceBearing(
          fss_record['record']['deploymentParam'][0]['installationParam']['latitude'],
          fss_record['record']['deploymentParam'][0]['installationParam']['longitude'],
          gwbl_record['record']['deploymentParam'][0]['installationParam']['latitude'],
          gwbl_record['record']['deploymentParam'][0]['installationParam']['longitude']) 
      # Get the list of FSS entity that are 150kms from the GWBL area
      if distance_km <= distance and fss_record['record']['deploymentParam'][0]\
             ['operationParam']['operationFrequencyRange']['highFrequency'] < 3700000000:
        list_of_fss_neighboring_gwbl.append(fss_record)
        break
  return list_of_fss_neighboring_gwbl


def getCbsdsNotPartOfPpaCluster(cbsds, ppa_record):
  """Returns the CBSDs that are not part of a PPA cluster list.

  Args:
    cbsds: List of CbsdData objects.
    ppa_record: A PPA record dictionary.
  Returns:
    List of CBSDs that are not part of the PPA cluster list.
  """

  cbsds_not_part_of_ppa_cluster = []
  # Compare the list of CBSDs with the PPA cluster list
  for cbsd in cbsds:
    cbsd_reference_id = generateCbsdReferenceId(cbsd['registrationRequest']['fccId'],
                                                cbsd['registrationRequest']['cbsdSerialNumber'])
    if cbsd_reference_id not in ppa_record['ppaInfo']['cbsdReferenceId']:
        cbsds_not_part_of_ppa_cluster.append(cbsd)

  return cbsds_not_part_of_ppa_cluster
