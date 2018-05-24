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

    findOverlappingGrantsInsideNeighborhood
    getProtectedChannels

  The routines return a interference caused by a grant in the neighborhood of
  FSS/GWPZ/PPA/ESC incumbent types
==================================================================================
"""
from collections import namedtuple
import multiprocessing
from multiprocessing.managers import BaseManager
import logging
import numpy as np

from reference_models.common import data
from reference_models.antenna import antenna
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.propagation import wf_hybrid

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
ESC_CH21_CF_HZ = 3652.5e6

# One Mega Hertz
MHZ = 1.e6

# Channel bandwidth over which SASs execute the aggregate interference and
# IAP process
RBW_HZ = 5.e6

# GWPZ and PPA height (m)
GWPZ_PPA_HEIGHT = 1.5

# In-band insertion loss
IN_BAND_INSERTION_LOSS = 0.5

# Global container to store neighborhood distance type of all the protection
_DISTANCE_PER_PROTECTION_TYPE = {
    data.ProtectedEntityType.GWPZ_AREA :  (GWPZ_NEIGHBORHOOD_DIST, GWPZ_NEIGHBORHOOD_DIST),
    data.ProtectedEntityType.PPA_AREA : ( PPA_NEIGHBORHOOD_DIST,  PPA_NEIGHBORHOOD_DIST),
    data.ProtectedEntityType.FSS_CO_CHANNEL : ( FSS_CO_CHANNEL_NEIGHBORHOOD_DIST,  FSS_CO_CHANNEL_NEIGHBORHOOD_DIST),
    data.ProtectedEntityType.FSS_BLOCKING : ( FSS_BLOCKING_NEIGHBORHOOD_DIST,  FSS_BLOCKING_NEIGHBORHOOD_DIST),
    data.ProtectedEntityType.ESC: (ESC_NEIGHBORHOOD_DIST_A, ESC_NEIGHBORHOOD_DIST_B)
}


# Management of a common structure object to manage the interference calculation.
# This object uses multiprocessing.Manager() to share the internals among multiple
# processes.
class AggregateInterferenceOutputFormat(object):
  """Implementation of output format of aggregate interference

  This class is used to generate specified output format for post IAP
  allowed interference or for aggregate interference to non-DPAs

  Creates a data structure to store post IAP allowed interference or
  aggregate interference to non-DPAs output in the format of
    {latitude : {longitude : [ output_first_5MHz_segment, ... , output_last_5MHz_segment ]}}
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

  # TODO(sbdt): remove that function and replace with the following one
  def GetAggregateInterferenceInfo(self):
    return self.aggregate_interference_info

  def GetAggregateInterferenceContent(self):
    return self.aggregate_interference_info._getvalue()


class AggregateInterferenceManager(BaseManager):
  pass


def getInterferenceObject():
  """ Creates the AggregateInterferenceOutputFormat class object, which will
  be shared across multiple processes using AggregateInterferenceManager
  customized manager"""
  AggregateInterferenceManager.register('AggregateInterferenceOutputFormat',
                                        AggregateInterferenceOutputFormat)
  manager = AggregateInterferenceManager()
  manager.start()

  return manager.AggregateInterferenceOutputFormat()


def dbToLinear(x):
  """This function returns dBm to mW converted value"""
  return 10**(x / 10.)


def linearToDb(x):
  """This function returns mW to dBm converted value"""
  return 10 * np.log10(x)


def getProtectedChannels(low_freq_hz, high_freq_hz):
  """Gets protected channels list.

  Performs 5MHz IAP channelization and returns a list of tuple containing
  (low_freq,high_freq)

  Args:
    low_freq_hz: Low frequency of the protected entity(Hz).
    high_freq_hz: High frequency of the protected entity(Hz)
  Returns:
    An array of protected channel frequency range tuple
    (low_freq_hz,high_freq_hz).
  """
  if low_freq_hz >= high_freq_hz:
    raise ValueError('Low frequency is greater than high frequency')
  channels = np.arange( max(low_freq_hz, 3550*MHZ), min(high_freq_hz, 3700*MHZ), 5*MHZ)

  return [(low, high) for low, high in zip(channels, channels+5*MHZ)]


def findGrantsInsideNeighborhood(grants, protection_point, entity_type):
  """Finds grants inside protection entity neighborhood.

  Args:
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.
    protection_point: The location of a protected entity as (longitude, latitude) tuple.
    entity_type: The entity type (|data.ProtectedEntityType|).
  Returns:
    grants_inside: a list of grants, each one being a namedtuple of type
                   |data.CbsdGrantInfo|, of all CBSDs inside the neighborhood
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


def grantFrequencyOverlapCheck(grant, ch_low_freq, ch_high_freq, protection_ent_type):
  """Checks if grant frequency overlaps with protection constraint frequency range.

  Args:
    grant: A CBSD grant of type |data.CbsdGrantInfo|.
    ch_low_freq: The low frequency of protection channel.
    ch_high_freq: The high frequency of protection channel.
    protection_ent_type: An enum of type |data.ProtectedEntityType|.
  Returns:
    True if grant frequency overlaps with protection constraint frequency range,
    False otherwise.
  """
  # Check frequency range
  overlapping_bw = min(grant.high_frequency, ch_high_freq) \
                      - max(grant.low_frequency, ch_low_freq)
  freq_check = (overlapping_bw > 0)

  # ESC Passband is 3550-3680MHz
  # Category A CBSD grants are considered in the neighborhood only for
  # constraint frequency range 3550-3660MHz
  if (protection_ent_type == data.ProtectedEntityType.ESC and
        grant.cbsd_category == 'A' and
        ch_high_freq > ESC_CAT_A_HIGH_FREQ_HZ):
    freq_check = False

  return freq_check


def findOverlappingGrants(grants, constraint):
  """Finds grants overlapping with protection entity.

  Grants overlapping with frequency range of the protection entity are
  considered as overlapping grants.

  Args:
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.
    constraint: A protection constraint of type |data.ProtectionConstraint|.
  Returns:
    grants_overlap: a list of |data.CbsdGrantInfo| grants of all CBSDs inside
      the neighborhood of the protection constraint.
  """
  grants_overlap = [grant for grant in grants
                    if grantFrequencyOverlapCheck(
                        grant, constraint.low_frequency,
                        constraint.high_frequency, constraint.entity_type)]
  return grants_overlap


def computeInterferencePpaGwpzPoint(cbsd_grant, constraint, h_inc_ant,
                                    max_eirp, region='SUBURBAN'):
  """Computes interference that a grant causes to GWPZ or PPA protection area.

  Routine to compute interference neighborhood grant causes to protection
  point within GWPZ or PPA protection area.

  Args:
    cbsd_grant: A CBSD grant of type |data.CbsdGrantInfo|.
    constraint: The protection constraint of type |data.ProtectionConstraint|.
    h_inc_ant: The reference incumbent antenna height (in meters).
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
    region: Region type of the GWPZ or PPA area: 'URBAN', 'SUBURBAN' or 'RURAL'.
  Returns:
    The interference contribution (dBm).
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

  # Get the exact overlap of the grant over the GWPZ area channels
  if constraint.entity_type == data.ProtectedEntityType.GWPZ_AREA:
    grant_overlap_bandwidth = min(cbsd_grant.high_frequency, constraint.high_frequency) \
        - max(cbsd_grant.low_frequency, constraint.low_frequency)
  else:
    grant_overlap_bandwidth = RBW_HZ

  # Get the interference value for area entity
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,
                   ant_gain, grant_overlap_bandwidth)

  interference = eirp - db_loss
  return interference


def computeInterferenceEsc(cbsd_grant, constraint, esc_antenna_info, max_eirp):
  """Computes interference that a grant causes to a ESC protection point.

  Routine to compute interference neighborhood grant causes to ESC protection
  point.

  Args:
    cbsd_grant: A CBSD grant of type |data.CbsdGrantInfo|.
    constraint: The protection constraint of type |data.ProtectionConstraint|.
    esc_antenna_info: ESC antenna information of type |data.EscInformation|.
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
  Returns:
    The interference contribution(dBm).
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

  interference = eirp - db_loss
  return interference


def computeInterferenceFssCochannel(cbsd_grant, constraint, fss_info, max_eirp):
  """Computes interference that a grant causes to a FSS protection point.

  Routine to compute interference neighborhood grant causes to FSS protection
  point for co-channel passband.

  Args:
    cbsd_grant: A CBSD grant of type |data.CbsdGrantInfo|.
    constraint: The protection constraint of type |data.ProtectionConstraint|.
    fss_info: The FSS information of type |data.FssInformation|.
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure.
  Returns:
    The interference contribution(dBm).
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
  """Gets the FSS mask loss for a FSS blocking protection constraint.

  Args:
    cbsd_grant: A CBSD grant of type |data.CbsdGrantInfo|.
    constraint: The protection constraint of type |data.ProtectionConstraint|.
      The constraint defines the FSS out of band left part, so typically
      [3550, min_passband_freq] or [3550, 3700].
  """
  # Sanity checks
  if (cbsd_grant.low_frequency >= cbsd_grant.high_frequency or
      cbsd_grant.low_frequency >= constraint.high_frequency):
    raise ValueError('CBSD grant frequencies incorrect')

  # Find the 50MHz edge and its rounded version
  edge_freq = constraint.high_frequency - 50*MHZ
  edge_freq_round = int(edge_freq/MHZ +0.5)*MHZ
  # Part of grant in closest mask segment
  seg1 = (max(cbsd_grant.low_frequency, edge_freq_round),
          min(cbsd_grant.high_frequency, constraint.high_frequency))
  # Part of grant in farther mask segment
  seg2 = (cbsd_grant.low_frequency,
          min(cbsd_grant.high_frequency, edge_freq_round))

  # Now compute the attenuation
  freqs1 = np.arange(seg1[0] + 0.5*MHZ, seg1[1], MHZ)
  freqs2 = np.arange(seg2[0] + 0.5*MHZ, seg2[1], MHZ)
  attens1 = (constraint.high_frequency - freqs1)/MHZ * 0.6 + 0.5
  attens2 = (edge_freq - freqs2)/MHZ * 0.25 + 30.5
  attens = np.concatenate((attens1, attens2))
  fss_mask_attenuation = -linearToDb(np.mean(dbToLinear(-attens)))
  return fss_mask_attenuation


def computeInterferenceFssBlocking(cbsd_grant, constraint, fss_info, max_eirp):
  """Computes interference that a grant causes to a FSS protection point.

  Routine to compute interference neighborhood grant causes to FSS protection
  point for blocking passband

  Args:
    cbsd_grant: A CBSD grant of type |data.CbsdGrantInfo|.
    constraint: The protection constraint of type |data.ProtectionConstraint|.
    fss_info: The FSS information of type |data.FssInformation|.
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure.

  Returns:
    The interference contribution(dBm).
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
  eff_bandwidth = (min(cbsd_grant.high_frequency, constraint.high_frequency)
                   - cbsd_grant.low_frequency)
  if eff_bandwidth < 0:
    raise ValueError('Computing FSS blocking on grant fully inside FSS passband')
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,
                                effective_ant_gain, eff_bandwidth)
  # Calculate the interference contribution
  interference = eirp - getFssMaskLoss(cbsd_grant, constraint) - db_loss

  return interference


def getEffectiveSystemEirp(max_eirp, cbsd_max_ant_gain, effective_ant_gain,
                           reference_bandwidth=RBW_HZ):
  """Calculates effective EIRP caused by a grant.

  Utility API to get effective EIRP caused by a grant in the
  neighborhood of the protected entity FSS/ESC/PPA/GWPZ.

  Args:
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure.
    cbsd_max_ant_gain: The nominal antenna gain of the CBSD.
    effective_ant_gain: The actual total antenna gains at the CBSD and protected
      entity. This takes into account the actual antenna patterns.
    reference_bandwidth: Reference bandwidth over which effective EIRP is calculated.
  Returns:
    The effective EIRP of the CBSD(dBm)
  """

  eirp_cbsd = ((max_eirp - cbsd_max_ant_gain) + effective_ant_gain + linearToDb
            (reference_bandwidth / MHZ))

  return eirp_cbsd


def computeInterference(grant, eirp, constraint,
                        fss_info=None, esc_antenna_info=None, region_type=None):
  """Calculates interference caused by a grant.

  Utility API to get interference caused by a grant in the
  neighborhood of the protected entity FSS/ESC/PPA/GWPZ.

  Args:
    grant: A CBSD grant of type |data.CbsdGrantInfo|.
    eirp: The EIRP of the grant.
    constraint: A protection constraint of type |data.ProtectionConstraint|.
    fss_info: The FSS information of type |data.FssInformation|.
    esc_antenna_info: ESC antenna information of type |data.EscInformation|.
    region: Region type of the GWPZ or PPA area: 'URBAN', 'SUBURBAN' or 'RURAL'.
  Returns:
    interference: Interference caused by a grant(dBm)
  """
  # Compute interference to FSS Co-channel protection constraint
  if constraint.entity_type is data.ProtectedEntityType.FSS_CO_CHANNEL:
    interference = computeInterferenceFssCochannel(
                     grant, constraint, fss_info, eirp)

  # Compute interference to FSS Blocking protection constraint
  elif constraint.entity_type is data.ProtectedEntityType.FSS_BLOCKING:
    interference = computeInterferenceFssBlocking(
                     grant, constraint, fss_info, eirp)

  # Compute interference to ESC protection constraint
  elif constraint.entity_type is data.ProtectedEntityType.ESC:
    interference = computeInterferenceEsc(
                     grant, constraint, esc_antenna_info, eirp)

  # Compute interference to GWPZ or PPA protection constraint
  else:
    interference = computeInterferencePpaGwpzPoint(
                     grant, constraint, GWPZ_PPA_HEIGHT,
                     eirp, region_type)

  logging.info(
      'Interference for grant (%s) with EIRP (%s) to constraint (%s) with fss_info (%s), esc_antenna_info (%s), and region (%s) is equal to %s dBm.',
      grant, eirp, constraint, fss_info, esc_antenna_info, region, interference)

  return interference
