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

from shapely.geometry import shape, Point, Polygon
from reference_models.geo import vincenty

def purgeOverlappingGrants(cbsds, frequency_range):
  """Removes Grants from CBSDs that overlap with the given frequency range.
  
  Args:
  cbsds: List of CbsdData objects. Grants are removed from the input.
  frequency_range: A dictionary with keys 'lowFrequency' and 'highFrequency'
  """
  for cbsd in cbsds:
    grants_to_purge = []
    if cbsd['grants']:
      for grant in cbsd['grants']:
        if checkForOverlappingGrants(grant, frequency_range):
          grants_to_purge.append(grant)
    for grant in grants_to_purge:
        cbsd['grants'].remove(grant)

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
  """ Get the list of all CBSDs that are present within the polygon or on the 
  boundary of the Polygon

  Args:
    cbsd_list:  List of CbsdData dictionaries as defined in the SAS-SAS specification.
    polygon : A GeoJSON object containing polygon information.
  Returns:
    List of CBSDs lying within or on the boundary of the protectionn area.
  """ 
  cbsds_within_polygon = []
  polygon = shape(polygon['features'][0]['geometry'])
  for cbsd in cbsds:
    cbsd_lat = cbsd['registrationRequest']['installationParam']['latitude']
    cbsd_long = cbsd['registrationRequest']['installationParam']['longitude']
    point = Point(cbsd_lat,cbsd_long)

    # If the CBSD is within the polygon and has grants then add it to the list
    if (polygon.contains(point)  or polygon.touches(point)) and cbsd['grants']:
      cbsds_within_polygon.append(cbsd)
  return cbsds_within_polygon

def getPpaFrequencyRange(ppa_record, pal_records):
  """Determines the frequency range of the PPA from the PAL records.

  The first PAL ID is retrieved from the PPA information and the primary frequency
  assignment of that PAL ID is returned as the PPA frequency range.
  Args:
    ppa_record: A dictionary containing PPA record.
    pal_records: List of PAL record dictionaries.
  Returns:
    Operating frequency range of PPA.
  """
  pal_id = ppa_record['ppaInfo']['palId'][0]

  for pal_record in pal_records:
    if pal_record['palId'] == pal_id:
      return pal_record['channelAssignment']['primaryAssignment']
  else:
    # If the for loop completes without identifying the PAL record then raise exception
    raise Exception("PAL ID: {} could not be found in the PAL_records list".format(pal_id))

def getFssNeighboringCbsdsWithGrants(cbsd_list, fss_record, distance):
  """ Get the list of all CBSDs that lie within 150 KMs of FSS and have at least one grant.

  Args:
    cbsd_list:  List of CbsdData dictionaries as defined in the SAS-SAS specification.
    fss_record: A FSS record dictionary.
  Returns:
    List of CBSDs lying within 150 KMs of FSS and having at least one grant.
  """

  neighboring_cbsds_with_grants = []
  for cbsd in cbsd_list:
    distance_km, _, _ = vincenty.GeodesicDistanceBearing(
        fss_record['record']['deploymentParam'][0]['installationParam']['latitude'],
        fss_record['record']['deploymentParam'][0]['installationParam']['longitude'],
        cbsd['registrationRequest']['installationParam']['latitude'],
        cbsd['registrationRequest']['installationParam']['longitude'])

    if distance_km <= distance and cbsd['grants']:
        neighboring_cbsds_with_grants.append(cbsd)
  return neighboring_cbsds_with_grants

def getFssNeighboringGwbl(gwbl_records, fss_records, distance): 
  """ Get the list of all fss that lie within 150 KMs of GWBL and operating below 3700000000

  Args:
    fss_records:  List of FSS records dictionary.
    gwbl_records: List of  GWBL record dictionary.
  Returns:
    List of FSSs lying within 150 KMs of GWBL and operating below 3700000000.
  """

  list_of_fss_neighboring_gwbl = []
  for gwbl_record in gwbl_records:
    for fss_record in fss_records:

      distance_km, _, _ = vincenty.GeodesicDistanceBearing(
          fss_record['record']['deploymentParam'][0]['installationParam']['latitude'],
          fss_record['record']['deploymentParam'][0]['installationParam']['longitude'],
          gwbl_record['record']['deploymentParam'][0]['installationParam']['latitude'],
          gwbl_record['record']['deploymentParam'][0]['installationParam']['longitude'])  
      if distance_km <= distance and fss_record['record']['deploymentParam'][0]\
             ['operationParam']['operationFrequencyRange']['highFrequency'] < 3700000000:
        list_of_fss_neighboring_gwbl.append(fss_record)
  return list_of_fss_neighboring_gwbl
