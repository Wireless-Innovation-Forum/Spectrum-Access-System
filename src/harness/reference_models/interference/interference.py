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

"""
==================================================================================
  Compute Interference caused by a grant for all the incumbent types
  APIs in this file are used by IAP and Aggregate Interference Reference Models

  The main routines are:

    computeInterference
    computeInterferencePpaGwpzPoint
    computeInterferenceEsc
    computeInterferenceFssCochannel
    computeInterferenceFssBlocking
    getEffectiveSystemEirp

  The common utility APIs are:

    getGrantObjectsFromFAD
    getAllGrantInformationFromCbsdDataDump
    findOverlappingGrantsInsideNeighborhood
    getProtectedChannels

  The routines return a interference caused by a grant in the neighborhood of
  FSS/GWPZ/PPA/ESC incumbent types
==================================================================================
"""
import numpy as np
import multiprocessing
from multiprocessing.managers import BaseManager
from reference_models.antenna import antenna
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.propagation import wf_hybrid
from sas_test_harness import generateCbsdReferenceId
from collections import namedtuple
from enum import Enum

# Initialize terrain driver
# terrainDriver = terrain.TerrainDriver()
terrainDriver = wf_itm.terrainDriver

# Set constant parameters based on requirements in the WINNF-TS-0112
# [R2-SGN-16]
GWPZ_NEIGHBORHOOD_DIST = 40  # neighborhood distance from a CBSD to a given protection
# point (in km) in GWPZ protection area
PPA_NEIGHBORHOOD_DIST = 40  # neighborhood distance from a CBSD to a given protection
# point (in km) in PPA protection area

FSS_CO_CHANNEL_NEIGHBORHOOD_DIST = 150  # neighborhood distance from a CBSD to FSS for
# co-channel protection

FSS_BLOCKING_NEIGHBORHOOD_DIST = 40  # neighborhood distance from a CBSD to FSS
# blocking protection

ESC_NEIGHBORHOOD_DIST_A = 40  # neighborhood distance from a ESC to category A CBSD

ESC_NEIGHBORHOOD_DIST_B = 80  # neighborhood distance from a ESC to category B CBSD

# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL_MHZ = 3625.0

# CBRS Band Frequency Range (Hz)
CBRS_LOW_FREQ_HZ = 3550.e6
CBRS_HIGH_FREQ_HZ = 3700.e6

# FSS Passband low frequency range  (Hz)
FSS_LOW_FREQ_HZ = 3600.e6

# FSS Passband for TT&C (Hz)
FSS_TTC_LOW_FREQ_HZ = 3700.e6
FSS_TTC_HIGH_FREQ_HZ = 4200.e6

# ESC IAP for Out-of-Band Category A CBSDs in Frequency Range (Hz)
ESC_CAT_A_LOW_FREQ_HZ = 3550.e6
ESC_CAT_A_HIGH_FREQ_HZ = 3660.e6

# ESC Passband Frequency Range (Hz)
ESC_LOW_FREQ_HZ = 3550.e6
ESC_HIGH_FREQ_HZ = 3680.e6

# ESC Channel 21 Centre Frequency
ESC_CH21_CF_HZ = 36525.e5

# One Mega Hertz
MHZ = 1.e6

# Channel bandwidth over which SASs execute the aggregate interference and 
# IAP process
RBW_HZ = 5.e6

# GWPZ and PPA height (m)
GWPZ_PPA_HEIGHT = 1.5

# In-band insertion loss
IN_BAND_INSERTION_LOSS = 0.5

# Define an enumeration class named ProtectedEntityType with members
# 'GWPZ_AREA', 'PPA_AREA', 'FSS_CO_CHANNEL', 'FSS_BLOCKING', 'ESC'


class ProtectedEntityType(Enum):
  GWPZ_AREA = 1
  PPA_AREA = 2
  FSS_CO_CHANNEL = 3
  FSS_BLOCKING = 4
  ESC = 5

# Global container to store neighborhood distance type of all the protection
_DISTANCE_PER_PROTECTION_TYPE = {
   ProtectedEntityType.GWPZ_AREA :  (GWPZ_NEIGHBORHOOD_DIST, GWPZ_NEIGHBORHOOD_DIST),
   ProtectedEntityType.PPA_AREA : ( PPA_NEIGHBORHOOD_DIST,  PPA_NEIGHBORHOOD_DIST),
   ProtectedEntityType.FSS_CO_CHANNEL : ( FSS_CO_CHANNEL_NEIGHBORHOOD_DIST,  FSS_CO_CHANNEL_NEIGHBORHOOD_DIST),
   ProtectedEntityType.FSS_BLOCKING : ( FSS_BLOCKING_NEIGHBORHOOD_DIST,  FSS_BLOCKING_NEIGHBORHOOD_DIST),
   ProtectedEntityType.ESC: (ESC_NEIGHBORHOOD_DIST_A, ESC_NEIGHBORHOOD_DIST_B)
    }

# Define CBSD grant, i.e., a tuple with named fields of 'latitude',
# 'longitude', 'height_agl', 'indoor_deployment', 'antenna_azimuth',
# 'antenna_gain', 'antenna_beamwidth', 'cbsd_category',
# 'max_eirp', 'low_frequency', 'high_frequency', 'is_managed_grant'
CbsdGrantInformation = namedtuple('CbsdGrantInformation',
                       ['latitude', 'longitude', 'height_agl',
                        'indoor_deployment', 'antenna_azimuth', 'antenna_gain',
                        'antenna_beamwidth', 'cbsd_category',
                        'max_eirp', 'low_frequency', 'high_frequency',
                        'is_managed_grant'])

# Define protection constraint, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'low_frequency', 'high_frequency'
ProtectionConstraint = namedtuple('ProtectionConstraint',
                                  ['latitude', 'longitude', 'low_frequency',
                                   'high_frequency', 'entity_type'])

# Define FSS Protection Point, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'height_agl', 'max_gain_dbi', 'pointing_azimuth',
# 'pointing_elevation'
FssInformation = namedtuple('FssInformation',
                            ['height_agl', 'max_gain_dbi',
                             'pointing_azimuth', 'pointing_elevation'])

# Define ESC information, i.e., a tuple with named fields of
# 'antenna_height', 'antenna_azimuth', 'antenna_gain_pattern'
EscInformation = namedtuple('EscInformation',
                            ['antenna_height', 'antenna_azimuth',
                             'antenna_gain_pattern'])


class AggregateInterferenceOutputFormat:
  """Implementation of output format of aggregate interference

  This class is used to generate specified output format for post IAP
  allowed interference or for aggregate interference to non-DPAs

  Creates a data structure to store post IAP allowed interference or
  aggregate interference to non-DPAs output in the format of
  {latitude : {longitude : [ output_first_5MHz_segment, output_first_5MHz_segment ]}}
  """
  def __init__(self):
    self.manager = multiprocessing.Manager()
    self.aggregate_interference_info = self.manager.dict()
    self.lock = multiprocessing.Lock()

  def UpdateAggregateInterferenceInfo(self, latitude, longitude, interference):
    with self.lock:
      if latitude not in self.aggregate_interference_info:
        self.aggregate_interference_info[latitude] = self.manager.dict()

      # Creating a proxy container for mutable dictionary
      aggregate_interference_proxy = self.aggregate_interference_info[latitude]

      if longitude not in aggregate_interference_proxy:
        aggregate_interference_proxy[longitude] = self.manager.list()

      aggregate_interference_proxy[longitude].append(interference)
      self.aggregate_interference_info[latitude] = aggregate_interference_proxy

  def GetAggregateInterferenceInfo(self):
    return self.aggregate_interference_info


class AggregateInterferenceManager(BaseManager):
  pass


def dbToLinear(x):
  """This function returns dBm to mW converted value"""
  return 10**(x / float(10))


def linearToDb(x):
  """This function returns mW to dBm converted value"""
  return 10 * np.log10(x)


def getProtectedChannels(low_freq_hz, high_freq_hz):
  """Gets protected channels list

  Performs 5MHz IAP channelization and returns a list of tuple containing
  (low_freq,high_freq)

  Args:
    low_freq_hz: Low frequency of the protected entity(Hz).
    high_freq_hz: High frequency of the protected entity(Hz)
  Returns:
    An array of protected channel frequency range tuple
    (low_freq_hz,high_freq_hz).
  """
  assert low_freq_hz < high_freq_hz, 'Low frequency is greater than high frequency'
  channels = np.arange( max(low_freq_hz, 3550*MHZ), min(high_freq_hz, 3700*MHZ), 5*MHZ)

  return [(low, high) for low,high in zip(channels, channels+5*MHZ)]


def findGrantsInsideNeighborhood(grants, protection_point, entity_type):
  """Finds grants inside protection entity neighborhood

  Args:
    grants: an iterator of grants with attributes latitude and longitude
    protection_point: location of a protected entity as (longitude,latitude) tuple
    entity_type: enum of type ProtectedEntityType
  Returns:
    grants_inside: a list of grants, each one being a namedtuple of type
                   CbsdGrantInformation, of all CBSDs inside the neighborhood
                   of the protection constraint.
  """
  # Initialize an empty list
  grants_inside = []

  # Loop over each CBSD grant
  for grant in grants:
    # Compute distance from CBSD location to protection constraint location
    dist_km, _, _ = vincenty.GeodesicDistanceBearing(grant.latitude,
                      grant.longitude, protection_point[1], protection_point[0])

    # Check if CBSD is inside the neighborhood of protection constraint
    if dist_km <= _DISTANCE_PER_PROTECTION_TYPE[entity_type][grant.cbsd_category == 'B']:
      grants_inside.append(grant)

  return grants_inside


def findOverlappingGrants(grants, constraint):
  """Finds grants overlapping with protection entity

  Grants overlapping with frequency range of the protection entity are
  considered as overlapping grants

  Args:
    grants: an iterator of grants with attributes latitude and longitude
    constraint: protection constraint of type ProtectionConstraint
  Returns:
    grants_inside: a list of grants, each one being a namedtuple of type
                   CbsdGrantInformation, of all CBSDs inside the neighborhood
                   of the protection constraint.
  """

  # Initialize an empty list
  grants_inside = []

  # Loop over each CBSD grant
  for grant in grants:
    # Check frequency range
    overlapping_bw = min(grant.high_frequency, constraint.high_frequency) \
                        - max(grant.low_frequency, constraint.low_frequency)
    freq_check = (overlapping_bw > 0)

    # ESC Passband is 3550-3680MHz
    # Category A CBSD grants are considered in the neighborhood only for
    # constraint frequency range 3550-3660MHz
    if (constraint.entity_type == ProtectedEntityType.ESC and
          grant.cbsd_category == 'A' and
          constraint.high_frequency > ESC_CAT_A_HIGH_FREQ_HZ):
          freq_check = False

    # Append the grants information if it is inside the neighborhood of
    # protection constraint
    if freq_check:
      grants_inside.append(grant)

  return grants_inside


def getCbsdsNotPartOfPpaCluster(cbsds, ppa_record):
    """Returns the CBSDs that are not part of a PPA cluster list.

    Args:
      cbsds : List of CBSDData objects.
      ppa_record : A PPA record dictionary.
    Returns:
      List of CBSDs that are not part of the PPA cluster list.
    """
    cbsds_not_part_of_ppa_cluster = []
    # Compare the list of CBSDs with the PPA cluster list
    for cbsd in cbsds:
      cbsd_reference_id = generateCbsdReferenceId(cbsd['registration']['fccId'],
                            cbsd['registration']['cbsdSerialNumber'])
      if cbsd_reference_id not in ppa_record['ppaInfo']['cbsdReferenceId']:
        cbsds_not_part_of_ppa_cluster.append(cbsd)

    return cbsds_not_part_of_ppa_cluster


def getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects, ppa_record=None): 
  """Extracts CBSD grant objects from FAD objects


  Args:
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
    ppa_record: A PPA record dictionary.
  Returns:
    grant_objects: a list of CBSD grants dictionary containing registration
    and grants
  """
  # List of CBSD grant tuples extracted from FAD record
  grant_objects = []
 
  grant_objects_uut = getAllGrantInformationFromCbsdDataDump(
                        sas_uut_fad_object.getCbsdRecords(), True, ppa_record)

  grant_objects_test_harness = []

  for fad in sas_th_fad_objects:
    grant_objects_test_harness.extend(getAllGrantInformationFromCbsdDataDump(
                                   fad.getCbsdRecords(), False, ppa_record))

  grant_objects = grant_objects_uut + grant_objects_test_harness

  return grant_objects


def getAllGrantInformationFromCbsdDataDump(cbsd_data_records, is_managing_sas=True, ppa_record=None):
  """Extracts list of CbsdGrantInformation namedtuple

  Routine to extract CbsdGrantInformation tuple from CBSD data records from
  FAD objects. For protected entity of type PPA, CBSDs, which belong to the PPA cluster
  list are not taken into consideration

  Args:
    cbsd_data_records: A list CbsdData object retrieved from FAD records.
    is_managing_sas: flag indicating cbsd data record is from managing SAS or
                     peer SAS
                     True - Managing SAS, False - Peer SAS
    ppa_record: A PPA record dictionary.
  Returns:
    grant_objects: a list of grants, each one being a namedtuple of type
                   CBSDGrantInformation, of all CBSDs from SAS UUT FAD and
                   SAS Test Harness FAD
  """

  grant_objects = []
  
  if ppa_record is not None:
    cbsd_data_records = getCbsdsNotPartOfPpaCluster(cbsd_data_records, ppa_record)

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
      altitude_cbsd = terrainDriver.GetTerrainElevation(lat_cbsd, lon_cbsd)
      height_cbsd = height_cbsd - altitude_cbsd

    for grant in grants:
      # Return CBSD information
      cbsd_grant = CbsdGrantInformation(
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


def computeInterferencePpaGwpzPoint(cbsd_grant, constraint, h_inc_ant,
                                  max_eirp, region='SUBURBAN'):
  """Compute interference grant causes to GWPZ or PPA protection area

  Routine to compute interference neighborhood grant causes to protection
  point within GWPZ or PPA protection area

  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    h_inc_ant: reference incumbent antenna height (in meters)
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
    region: Region type of the GWPZ or PPA area
  Returns:
    interference: interference contribution(dBm)
  """

  if (cbsd_grant.latitude == constraint.latitude and
        cbsd_grant.longitude == constraint.longitude):
    db_loss = 0
    incidence_angles = wf_itm._IncidenceAngles(hor_cbsd=0, ver_cbsd=0, hor_rx=0, ver_rx=0)
  else:
    # Get the propagation loss and incident angles for area entity
    db_loss, incidence_angles, _ = wf_hybrid.CalcHybridPropagationLoss(
                                     cbsd_grant.latitude, cbsd_grant.longitude,
                                     cbsd_grant.height_agl, constraint.latitude,
                                     constraint.longitude, h_inc_ant,
                                     cbsd_grant.indoor_deployment,
                                     reliability=-1,
                                     freq_mhz=FREQ_PROP_MODEL_MHZ,
                                     region=region)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Get the interference value for area entity
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,
                   ant_gain)

  interference = eirp - db_loss
  return interference


def computeInterferenceEsc(cbsd_grant, constraint, esc_antenna_info, max_eirp):
  """Compute interference grant causes to a ESC protection point

  Routine to compute interference neighborhood grant causes to ESC protection
  point

  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    esc_antenna_info: contains information on ESC antenna height, azimuth,
                      gain and pattern gain
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
  Returns:
    interference: interference contribution(dBm)
  """

  # Get the propagation loss and incident angles for ESC entity
  db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(cbsd_grant.latitude,
                                   cbsd_grant.longitude, cbsd_grant.height_agl,
                                   constraint.latitude, constraint.longitude,
                                   esc_antenna_info.antenna_height,
                                   cbsd_grant.indoor_deployment, reliability=-1,
                                   freq_mhz=FREQ_PROP_MODEL_MHZ)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Compute ESC antenna gain in the direction of CBSD
  esc_ant_gain = antenna.GetAntennaPatternGains(
      incidence_angles.hor_rx,
      esc_antenna_info.antenna_azimuth,
      esc_antenna_info.antenna_gain_pattern)

  # Get the total antenna gain by summing the antenna gains from CBSD to ESC
  # and ESC to CBSD
  effective_ant_gain = ant_gain + esc_ant_gain

  # Compute the interference value for ESC entity
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,effective_ant_gain)

  interference = eirp - db_loss - IN_BAND_INSERTION_LOSS
  return interference


def computeInterferenceFssCochannel(cbsd_grant, constraint, fss_info, max_eirp):
  """Compute interference grant causes to a FSS protection point

  Routine to compute interference neighborhood grant causes to FSS protection
  point for co-channel passband
  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    fss_info: contains fss point and antenna information
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
  Returns:
    interference: interference contribution(dBm)
  """

  # Get the propagation loss and incident angles for FSS entity_type
  db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(cbsd_grant.latitude,
                                   cbsd_grant.longitude, cbsd_grant.height_agl,
                                   constraint.latitude, constraint.longitude,
                                   fss_info.height_agl, cbsd_grant.indoor_deployment,
                                   reliability=-1, freq_mhz=FREQ_PROP_MODEL_MHZ)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Compute FSS antenna gain in the direction of CBSD
  fss_ant_gain = antenna.GetFssAntennaGains(incidence_angles.hor_rx,
                   incidence_angles.ver_rx, fss_info.pointing_azimuth,
                   fss_info.pointing_elevation, fss_info.max_gain_dbi)

  # Get the total antenna gain by summing the antenna gains from CBSD to FSS
  # and FSS to CBSD
  effective_ant_gain = ant_gain + fss_ant_gain

  # Compute the interference value for Fss co-channel entity
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,
                   effective_ant_gain)
  interference = eirp - db_loss - IN_BAND_INSERTION_LOSS
  return interference


def getFssMaskLoss(cbsd_grant, constraint):
  """Gets the FSS mask loss for a FSS blocking protection constraint"""
  # Get 50MHz offset below the lower edge of the FSS earth station
  offset = constraint.low_frequency - 50.e6

  # Get CBSD grant frequency range
  cbsd_freq_range = cbsd_grant.high_frequency - cbsd_grant.low_frequency

  fss_mask_loss = 0

  # if lower edge of the FSS passband is less than CBSD grant
  # lowFrequency and highFrequency
  if (constraint.low_frequency < cbsd_grant.low_frequency and
         constraint.low_frequency < cbsd_grant.high_frequency):
    fss_mask_loss = 0.5

  # if CBSD grant lowFrequency and highFrequency is less than
  # 50MHz offset from the FSS passband lower edge
  elif (cbsd_grant.low_frequency < offset and
     cbsd_grant.high_frequency < offset):
    fss_mask_loss = linearToDb((cbsd_freq_range / MHZ) * 0.25)

  # if CBSD grant lowFrequency is less than 50MHz offset and
  # highFrequency is greater than 50MHz offset
  elif (cbsd_grant.low_frequency < offset and
            cbsd_grant.high_frequency > offset):
    low_freq_mask_loss = linearToDb(((offset - cbsd_grant.low_frequency) /
                                                     MHZ) * 0.25)
    fss_mask_loss = low_freq_mask_loss + linearToDb(((
        cbsd_grant.high_frequency - offset) / MHZ) * 0.6)

  # if FSS Passband lower edge frequency is grater than CBSD grant
  # lowFrequency and highFrequency and
  # CBSD grand low and high frequencies are greater than 50MHz offset
  elif (constraint.low_frequency > cbsd_grant.low_frequency and
      constraint.low_frequency > cbsd_grant.high_frequency and
      cbsd_grant.low_frequency > offset and
             cbsd_grant.high_frequency > offset):
    fss_mask_loss = linearToDb((cbsd_freq_range / MHZ) * 0.6)

  return fss_mask_loss


def computeInterferenceFssBlocking(cbsd_grant, constraint, fss_info, max_eirp):
  """Compute interference grant causes to a FSS protection point

  Routine to compute interference neighborhood grant causes to FSS protection
  point for blocking passband

  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    fss_info: contains fss point and antenna information
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
  Returns:
    interference: interference contribution(dBm)
  """

  # Get the propagation loss and incident angles for FSS entity
  # blocking channels
  db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(
                                   cbsd_grant.latitude, cbsd_grant.longitude,
                                   cbsd_grant.height_agl, constraint.latitude,
                                   constraint.longitude, fss_info.height_agl,
                                   cbsd_grant.indoor_deployment, reliability=-1,
                                   freq_mhz=FREQ_PROP_MODEL_MHZ)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Compute FSS antenna gain in the direction of CBSD
  fss_ant_gain = antenna.GetFssAntennaGains(incidence_angles.hor_rx,
                   incidence_angles.ver_rx, fss_info.pointing_azimuth,
                   fss_info.pointing_elevation, fss_info.max_gain_dbi)


  # Get the total antenna gain by summing the antenna gains from CBSD to FSS
  # and FSS to CBSD
  effective_ant_gain = ant_gain + fss_ant_gain

  # Compute EIRP of CBSD grant inside the frequency range of
  # protection constraint
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,
           effective_ant_gain, (cbsd_grant.high_frequency - cbsd_grant.low_frequency))
  # Calculate the interference contribution
  interference = eirp - getFssMaskLoss(cbsd_grant, constraint) - db_loss

  return interference


def getEffectiveSystemEirp(max_eirp, cbsd_max_ant_gain, effective_ant_gain,
                           reference_bandwidth=RBW_HZ):
  """Calculates effective EIRP caused by a grant

  Utility API to get effective EIRP caused by a grant in the
  neighborhood of the protected entity FSS/ESC/PPA/GWPZ.

  Args:
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
    cbsd_max_ant_gain: The nominal antenna gain of the CBSD.
    effective_ant_gain: The actual total antenna gains at the CBSD and protected
      entity. This takes into account the actual antenna patterns.
    reference_bandwidth: Reference bandwidth over which effective EIRP is calculated
  Returns:
    eirp_cbsd: Effective EIRP of the CBSD(dBm)
  """

  eirp_cbsd = ((max_eirp - cbsd_max_ant_gain) + effective_ant_gain + linearToDb
            (reference_bandwidth / MHZ))

  return eirp_cbsd


def computeInterference(grant, eirp, channel_constraint, fss_info=None,
  esc_antenna_info=None, region_type=None):
  """Calculates interference caused by a grant

  Utility API to get interference caused by a grant in the
  neighborhood of the protected entity FSS/ESC/PPA/GWPZ.

  Args:
    grant : namedtuple of type CbsdGrantInformation
    eirp : EIRP of the grant
    channel_constraint: namedtuple of type ProtectionConstraint
    fss_info: contains fss point and antenna information
    esc_antenna_info: contains information on ESC antenna height, azimuth,
                      gain and pattern gain
    region_type: region type of protection PPA/GWPZ area.
  Returns:
    interference: Interference caused by a grant(dBm)
  """

  # Compute interference to FSS Co-channel protection constraint
  if channel_constraint.entity_type is ProtectedEntityType.FSS_CO_CHANNEL:
    interference = computeInterferenceFssCochannel(
                     grant, channel_constraint, fss_info, eirp)

  # Compute interference to FSS Blocking protection constraint
  elif channel_constraint.entity_type is ProtectedEntityType.FSS_BLOCKING:
    interference = computeInterferenceFssBlocking(
                     grant, channel_constraint, fss_info, eirp)

  # Compute interference to ESC protection constraint
  elif channel_constraint.entity_type is ProtectedEntityType.ESC:
    interference = computeInterferenceEsc(
                     grant, channel_constraint, esc_antenna_info, eirp)

  # Compute interference to GWPZ or PPA protection constraint
  else:
    interference = computeInterferencePpaGwpzPoint(
                     grant, channel_constraint, GWPZ_PPA_HEIGHT,
                     eirp, region_type)

  return interference


def convertAndSumInterference(cbsd_interference_list):
  """Converts interference in dBm to mW to calculate aggregate interference"""
  interferences_in_dbm = np.array(cbsd_interference_list)
  return np.sum(dbToLinear(interferences_in_dbm))


def aggregateInterferenceForPoint(protection_point, channels, low_freq, high_freq,
      grant_objects, fss_info, esc_antenna_info, protection_ent_type,
      region_type, aggregate_interference):
  """Algorithm to compute aggregate interference for protection point

  This method is invoked to calculate aggregate interference for FSS(Co-channel
  and blocing passband) and ESC protection points.It is also invoked for
  protection points within PPA and GWPZ protection areas.

  Args:
   protection_point: Protection point as a tuple (longitude, latitude)
   channels: A sequence of channels as tuple (low_freq_hz, high_freq_hz)
   low_freq: Low frequency of protection constraint (Hz)
   high_freq: High frequency of protection constraint (Hz)
   grant_objects: A list of grant requests, each one being a namedtuple
                  containing grant information
   fss_info: Contains fss point and antenna information
   esc_antenna_info: Contains information on ESC antenna height, azimuth,
                     gain and pattern gain
   protection_ent_type: An enum member of class ProtectedEntityType
   region_type: Region type of the protection point
   aggregate_interference : object of class type AggregateInterferenceOutputFormat
   Returns:
      Updates aggregate_interference object for a aggregate interference(mW)
      per protection channel of a protection point.
      Dictionary in the format of
      {latitude : {longitude : [aggr_interference(mW), aggr_interference(mW)]}},
      aggr_interference is a aggregate interference(mW) in a particular protection
      channel of protection point
  """
  # Get all the grants inside neighborhood of the protection entity
  grants_inside = findGrantsInsideNeighborhood(
                    grant_objects, protection_point, protection_ent_type)

  if len(grants_inside) > 0:
    for channel in channels:
      # Get protection constraint over 5MHz channel range
      protection_constraint = ProtectionConstraint(
          latitude=protection_point[1], longitude=protection_point[0],
          low_frequency=channel[0], high_frequency=channel[1],
          entity_type=protection_ent_type)

      # Identify CBSD grants overlapping with frequency range of the protection entity
      # in the neighborhood of the protection point and channel
      neighborhood_grants = findOverlappingGrants(
                              grants_inside, protection_constraint)

      if not neighborhood_grants:
        # As number of neighborhood grants are zero, setting
        # aggregate_interference to '0' for a protection_constraint
        aggregate_interference.UpdateAggregateInterferenceInfo(protection_point[1],
          protection_point[0], 0)
        continue

      cbsd_interference_list = []

      for grant in neighborhood_grants:
        cbsd_interference_list.append(computeInterference(
          grant, grant.max_eirp, protection_constraint, fss_info,
          esc_antenna_info, region_type))

      aggr_interference = convertAndSumInterference(cbsd_interference_list)
      aggregate_interference.UpdateAggregateInterferenceInfo(protection_point[1],
          protection_point[0], aggr_interference)


def getInterferenceObject():
  """ Creates the AggregateInterferenceOutputFormat class object, which will
  be shared across multiple processes using AggregateInterferenceManager
  customized manager"""
  AggregateInterferenceManager.register('AggregateInterferenceOutputFormat',
                                        AggregateInterferenceOutputFormat)
  manager = AggregateInterferenceManager()
  manager.start()

  return manager.AggregateInterferenceOutputFormat()
