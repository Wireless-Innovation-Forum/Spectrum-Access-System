"""Defines reference model patch to save given power after IAP.

Usage:
  Simply import that module.
"""
# TODO: integrate these changes officially in the reference model, as they
#       are useful in general for a bunch of studies.

# A few reference model data/routines are changed in common/data.py and
# iap/iap.py modules.
# The code is identical to the original code, except for littles pieces marked
# wih word "PATCHED" below.
#
# Ultimately these changes can be reintegrated in the reference model, as they
# are in general useful for several studies.

import logging

from collections import namedtuple

from reference_models.common import cache
from reference_models.common import data
from reference_models.iap import iap
from reference_models.geo import drive
from reference_models.propagation import wf_hybrid
from reference_models.interference import interference as interf


#--------------------------------------------------
# In common/data.py
#
#  CbsdGrantInfo is patched to add the iap power
class CbsdGrantInfo(namedtuple('CbsdGrantInfo',
                               [# Installation params
                                'latitude', 'longitude', 'height_agl',
                                'indoor_deployment', 'cbsd_category',
                                'antenna_azimuth', 'antenna_gain', 'antenna_beamwidth',
                                # Grant params
                                'max_eirp',
                                'iap_eirp', # *****PATCHED*****
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
    max_eirp: The maximum EIRP of the CBSD (dBm per MHz).
    iap_eirp: The EIRP provided by the IAP process.
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

  max_eirp, low_frequency, high_frequency = None, None, None
  if grant_request is not None:
    if 'requestedOperationParam' in grant_request:
      max_eirp = grant_request['requestedOperationParam']['maxEirp']
      low_frequency = grant_request['requestedOperationParam']['operationFrequencyRange']['lowFrequency']
      high_frequency = grant_request['requestedOperationParam']['operationFrequencyRange']['highFrequency']
    else:
      max_eirp = grant_request['operationParam']['maxEirp']
      low_frequency = grant_request['operationParam']['operationFrequencyRange']['lowFrequency']
      high_frequency = grant_request['operationParam']['operationFrequencyRange']['highFrequency']
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
      max_eirp=max_eirp,
      iap_eirp={max_eirp}, # *****PATCHED*****
      low_frequency=low_frequency,
      high_frequency=high_frequency,
      is_managed_grant=is_managing_sas)

#--------------------------------------------------
# In iap/iap.py
#
# iapPointConstraint is patched to save the IAP given frequency on input grants
# (new `iap_eirp` field of the CbsdGrantInfo).

def iapPointConstraint(protection_point, channels, low_freq, high_freq,
                       grants, fss_info, esc_antenna_info,
                       region_type, threshold, protection_ent_type):
  """Computes aggregate interference(Ap and ASASp) from authorized grants.

  This routine is applicable for FSS Co-Channel and ESC Sensor protection points,
  and PPA/GWPZ protection areas. It calculates aggregate interference over all
  5MHz channels, and feeds post-IAP assessment of allowed interference margins.

  Args:
    protection_point: A protection point as a tuple (longitude, latitude).
    channels: The 5MHz channels as a list of (low_freq, high_freq) tuples.
    low_freq: low frequency of protection constraint (Hz)
    high_freq: high frequency of protection constraint (Hz)
    grants: An iterable of |data.CbsdGrantInfo| grants.
    fss_info: The FSS information of type |data.FssInformation|.
    esc_antenna_info: ESC antenna information of type |data.EscInformation|.
    region_type: Region type of the protection point: 'URBAN', 'SUBURBAN' or 'RURAL'.
    threshold: The protection threshold (mW).
    protection_ent_type: The entity type (|data.ProtectedEntityType|).

  Returns:
    A tuple (latitude, longitude, asas_interference, agg_interference) where:
      asas_interference: a list of interference (per channel) for managing SAS.
      agg_interference: a list of total interference (per channel).
  """
  # Get protection constraint of protected entity
  protection_constraint = data.ProtectionConstraint(
      latitude=protection_point[1], longitude=protection_point[0],
      low_frequency=low_freq, high_frequency=high_freq, entity_type=protection_ent_type)

  # Get all the grants inside neighborhood of the protection entity
  grants_inside = interf.findGrantsInsideNeighborhood(
      grants, protection_point, protection_ent_type)

  # Get all the grants inside neighborhood of the protection entity, and
  # with frequency overlap to the protection point.
  neighbor_grants = interf.findOverlappingGrants(
      grants_inside,
      protection_constraint)

  if not neighbor_grants:
    return (protection_point[1], protection_point[0],
            [0] * len(channels), [0] * len(channels))

  # Get number of grants, IAP protection threshold and fairshare per channel.
  num_unsatisfied_grants = len(neighbor_grants)

  # *** PATCHED *** Print the number of grants in the neighborhood
  print('Number of grants in the ESC neighborhood: %d / %d'
        % (num_unsatisfied_grants, len(grants_inside) ))

  # Initialize list of aggregate interference from all the grants
  # (including grants from managing and peer SAS )
  aggr_interf = [0] * len(channels)
  # Initialize list of aggregate interference from managing SAS grants.
  asas_interf = [0] * len(channels)

  # Algorithm to calculate interference within IAPBW using EIRP obtained for all
  # the grants through application of IAP
  num_unsatisfied_grants_channels = []
  iap_threshold_channels = []
  fairshare_channels = []

  for index, channel in enumerate(channels):
    # Get protection constraint over 5MHz channel range
    channel_constraint = data.ProtectionConstraint(
        latitude=protection_point[1], longitude=protection_point[0],
        low_frequency=channel[0], high_frequency=channel[1],
        entity_type=protection_ent_type)

    # Identify CBSD grants overlapping with frequency range of the protection entity
    # in the neighborhood of the protection point and channel
    channel_neighbor_grants = interf.findOverlappingGrants(neighbor_grants,
                                                           channel_constraint)
    num_unsatisfied_grants_channel = len(channel_neighbor_grants)

    # Computes interference quota for this protection_point and channel.
    iap_threshold = threshold

    # Calculate the fair share per channel based on unsatisfied grants
    fairshare_channel = 0
    if num_unsatisfied_grants_channel > 0:
      fairshare_channel = float(iap_threshold) / num_unsatisfied_grants_channel

    num_unsatisfied_grants_channels.append(num_unsatisfied_grants_channel)
    iap_threshold_channels.append(iap_threshold)
    fairshare_channels.append(fairshare_channel)

  # List of grants initialized with max EIRP
  grants_eirp = [grant.max_eirp for grant in neighbor_grants]

  # Initialize list of grants_satisfied to False
  grants_satisfied = [False] * num_unsatisfied_grants

  # Initialize list of grants_removed to False
  grants_removed = [False] * num_unsatisfied_grants

  # Initialize grant overlap and interference per channel dictionary
  # Values will be stored in the format of key as tuple (grant_id, channel_id)
  # and respective value as:
  #   overlap_flag: True/False based on grant overlaps with channel
  #   interference: respective interference value for the key
  grants_overlap_flag = {}
  grants_interference = {}

  with cache.CacheManager(wf_hybrid.CalcHybridPropagationLoss):
    # Using memoizing cache manager only for lengthy calculation (hybrid on PPA/GWPZ).
    while num_unsatisfied_grants > 0:
      for g_idx, grant in enumerate(neighbor_grants):

        if grants_satisfied[g_idx]:
          continue

        for idx, channel in enumerate(channels):
          # Check if grant overlaps with protection point, channel
          grant_overlap_check = interf.grantFrequencyOverlapCheck(
              grant, channel[0], channel[1], protection_ent_type)

          grants_overlap_flag[(g_idx, idx)] = grant_overlap_check
          if not grant_overlap_check:
            continue
          # Get protection constraint over 5MHz channel range
          channel_constraint = data.ProtectionConstraint(
              latitude=protection_point[1], longitude=protection_point[0],
              low_frequency=channel[0], high_frequency=channel[1],
              entity_type=protection_ent_type)

          # Compute interference that grant causes to protection point over channel
          interference = interf.dbToLinear(interf.computeInterference(
              grant, grants_eirp[g_idx], channel_constraint, fss_info,
              esc_antenna_info, region_type))

          # If calculated interference is more than fair share of interference
          # to which the grants are entitled then grant is considered unsatisfied
          if interference < fairshare_channels[idx]:
            # Add the interference caused by all the grants in a 5MHz channel
            grants_interference[(g_idx, idx)] = interference
            grants_satisfied[g_idx] = True
          else:
            grants_satisfied[g_idx] = False
            break

      num_grants_good_overall_channels = 0

      for gr_idx, grant in enumerate(neighbor_grants):
        if grants_removed[gr_idx]:
          continue
        if not grants_satisfied[gr_idx]:
          continue
        if num_unsatisfied_grants > 0:
          num_unsatisfied_grants -= 1
        for ch_idx, channel in enumerate(channels):
          # Grant interferes with protection point over channel
          if grants_overlap_flag[(gr_idx, ch_idx)]:
            iap_threshold_channels[ch_idx] = (iap_threshold_channels[ch_idx] -
                                              grants_interference[(gr_idx, ch_idx)])
            num_unsatisfied_grants_channels[ch_idx] -= 1
            # Re-calculate fairshare for a channel
            if num_unsatisfied_grants_channels[ch_idx] > 0:
              fairshare_channels[ch_idx] = (float(iap_threshold_channels[ch_idx]) /
                                            num_unsatisfied_grants_channels[ch_idx])
            aggr_interf[ch_idx] += grants_interference[(gr_idx, ch_idx)]
            if grant.is_managed_grant:
              asas_interf[ch_idx] += grants_interference[(gr_idx, ch_idx)]

          # Removing grants from future consideration
          grants_removed[gr_idx] = True

          # Increase number of grants good over all channels
          num_grants_good_overall_channels += 1

      if num_grants_good_overall_channels == 0:
        for grant_idx, grant in enumerate(neighbor_grants):
          # Reduce power level of all the unsatisfied grants
          if not grants_satisfied[grant_idx]:
            grants_eirp[grant_idx] -= 1

  logging.debug('IAP point_constraint @ point %s: %s',
                (protection_point[1], protection_point[0]),
                zip(asas_interf, aggr_interf))

  # *****Start PATCHED*****
  # Add the grant eirp for protected point to iap eirp.
  for grant, grant_eirp in zip(neighbor_grants, grants_eirp):
    grant.iap_eirp.add(grant_eirp)
  # ***** End Patch *****

  # Return the computed data
  return protection_point[1], protection_point[0], asas_interf, aggr_interf

MHZ = 1.e6
IAPBW_HZ = 5*MHZ
THRESH_ESC_DBM_PER_RBW = -109
MARGIN_ESC_DB = 1
ESC_RBW_HZ = 1*MHZ
THRESH_ESC_DBM_PER_IAPBW = (THRESH_ESC_DBM_PER_RBW +
                            interf.linearToDb(IAPBW_HZ / ESC_RBW_HZ))

def performIapForEsc(esc_record, grants, sas_th_fad_objects):
  """Computes post IAP interference margin for ESC.

  IAP algorithm is run over ESC passband 3550-3660MHz for Category A CBSDs and
  3550-3680MHz for Category B CBSDs.

  Args:
    esc_record: An ESC record (dict of schema |EscSensorRecord|).
    grants: A list of CbsdGrantInfo
    sas_th_fad_objects: A list of FAD objects from SAS Test Harness
  Returns:
    ap_iap_ref: The post-IAP allowed interference, as a dict formatted as:
        {latitude : {longitude : [interference(mW/IAPBW), .., interference(mW/IAPBW)]}}
      where the list holds all values per channel of that protection point.
  """
  esc_thresh_q = THRESH_ESC_DBM_PER_IAPBW

  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  esc_iap_threshold = interf.dbToLinear(esc_thresh_q - MARGIN_ESC_DB)

  # grants = data.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS
  num_sas = len(sas_th_fad_objects) + 1

  # Get the ESC infos
  protection_point, esc_antenna_info = data.getEscInfo(esc_record)

  # Get ESC passband 3550-3680 MHz protection channels
  protection_channels = interf.getProtectedChannels(interf.ESC_LOW_FREQ_HZ,
                                                    interf.ESC_HIGH_FREQ_HZ)

  logging.debug('$$$$ Calling ESC Protection $$$$')
  # ESC algorithm
  iap_interfs = iapPointConstraint(protection_point, protection_channels,
                               interf.ESC_LOW_FREQ_HZ, interf.ESC_HIGH_FREQ_HZ,
                               grants, None, esc_antenna_info, None,
                               esc_iap_threshold, data.ProtectedEntityType.ESC)

  ap_iap_ref = iap.calculatePostIapAggregateInterference(
      interf.dbToLinear(esc_thresh_q), num_sas, iap_interfs)
  return ap_iap_ref

#=============================================
# Effective patching done here
data.CbsdGrantInfo = CbsdGrantInfo
data.constructCbsdGrantInfo = constructCbsdGrantInfo
iap.iapPointConstraint = iapPointConstraint
iap.performIapForEsc = performIapForEsc
