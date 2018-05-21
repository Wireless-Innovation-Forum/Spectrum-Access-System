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

"""
==================================================================================
  Iterative Allocation Process(IAP) Reference Model [R2-SGN-16].
  Based on WINNF-TS-0061, Version V1.0.0-r5.1, 17 January 2018.

  This model provides functions to calculate post IAP allowed interference margin for
  the protection constraint of FSS, ESC, GWPZ and PPA.

  The main routines are:

    performIapForEsc
    performIapForGwpz
    performIapForPpa
    performIapForFssCochannel
    performIapForFssBlocking
    calculatePostIapAggregateInterference

  The routines return a nested dictionary containing in the format of
  {latitude : {longitude : [interference1, interference2, etc...]}. interference is
  the post IAP aggregate interference value from all the CBSDs managed by the
  SAS in mW/IAPBW for each of the constraints.
==================================================================================
"""

import logging
from functools import partial
from collections import namedtuple

import numpy as np

from reference_models.common import data
from reference_models.common import mpool
from reference_models.geo import utils
from reference_models.interference import interference as interf

# values from WINNF-TS-0061-V1.1.0 - WG4 SAS Test and Certification Spec-Table
# 8.4-2 Protected entity reference for IAP Protection
# The values are in (dBm/RBW)
THRESH_PPA_DBM_PER_RBW = -80
THRESH_GWPZ_DBM_PER_RBW = -80
THRESH_FSS_CO_CHANNEL_DBM_PER_RBW = -129
THRESH_FSS_BLOCKING_DBM_PER_RBW = -60
THRESH_ESC_DBM_PER_RBW = -109

# Default 1 dB pre IAP margin for all incumbent types
MARGIN_PPA_DB = 1
MARGIN_GWPZ_DB = 1
MARGIN_FSS_CO_CHANNEL_DB = 1
MARGIN_FSS_BLOCKING_DB = 1
MARGIN_ESC_DB = 1

# One Mega Hertz
MHZ = 1.e6

# Channel bandwidth over which SASs execute the IAP process
IAPBW_HZ = 5*MHZ

# GWPZ Area Protection reference bandwidth for the IAP process
GWPZ_RBW_HZ = 10*MHZ

# PPA Area Protection reference bandwidth for the IAP process
PPA_RBW_HZ = 10*MHZ

# FSS Point Protection reference bandwidth for the IAP process
FSS_RBW_HZ = 1*MHZ

# ESC Point Protection reference bandwidth for the IAP process
ESC_RBW_HZ = 1*MHZ

# The grid resolution for area based protection entities.
GWPZ_GRID_RES_ARCSEC = 2
PPA_GRID_RES_ARCSEC = 2


def iapPointConstraint(protection_point, channels, low_freq, high_freq,
                       grants, fss_info, esc_antenna_info,
                       region_type, threshold, protection_ent_type,
                       asas_interference, aggr_interference):
  """Computes aggregate interference(Ap and ASASp) from authorized grants.

  This routine is applicable for FSS Co-Channel and ESC Sensor protection points,
  and PPA/GWPZ protection areas. It calculates aggregate interference over all
  5MHz channels, and feeds post-IAP assessment of allowed interference margins.

  This routine modifies the `asas_interference` and `aggr_interference`
  interference container objects of type |interf.AggregateInterferenceOutputFormat|,
  which holds entries like:
     {latitude : {longitude : [asas_p(mW/IAPBW),.. ]}}
     {latitude : {longitude : [a_p(mW/IAPBW),..] }}

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
    asas_interference: The |interf.AggregateInterferenceOutputFormat| interference
      container for the managing SAS.
    aggr_interference: The |interf.AggregateInterferenceOutputFormat| interference
      container for the all SAS: managing SAS and peer SASes.
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
    for j in xrange(len(channels)):
      asas_interference.UpdateAggregateInterferenceInfo(
          protection_point[1], protection_point[0], 0)
      aggr_interference.UpdateAggregateInterferenceInfo(
          protection_point[1], protection_point[0], 0)
    return

  # Get number of grants, IAP protection threshold and fairshare per channel.
  num_unsatisfied_grants = len(neighbor_grants)

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
    if protection_ent_type is data.ProtectedEntityType.ESC:
      # Integrates roll-off attenuation in threshold
      if channel[0] >= 3650.e6:
        # TODO(sbdt): what is the intent in following line?
        # Also why not doing the analytical formula for speedup
        offset = ((channel[0] - 3650.e6) / 5.e6) * 5
        lowfreq = channel[0]
        roll_of_attenuation = 0
        while lowfreq < channel[1]:
          roll_of_attenuation += interf.dbToLinear(-offset - 0.5)
          lowfreq += MHZ
          offset += 1
        roll_of_attenuation = interf.linearToDb(roll_of_attenuation / 5.)
        iap_threshold = interf.dbToLinear(interf.linearToDb(threshold) -
                                          roll_of_attenuation)

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

  # Update aggregate interference and asas_interference from all the grants
  # at a protection point, channel
  for j, interf_val in enumerate(aggr_interf):
    asas_interference.UpdateAggregateInterferenceInfo(protection_point[1],
      protection_point[0], asas_interf[j])
    aggr_interference.UpdateAggregateInterferenceInfo(protection_point[1],
      protection_point[0], interf_val)


def performIapForEsc(esc_record, sas_uut_fad_object, sas_th_fad_objects):
  """Computes post IAP interference margin for ESC.

  IAP algorithm is run over ESC passband 3550-3660MHz for Category A CBSDs and
  3550-3680MHz for Category B CBSDs.

  Args:
    esc_record: An ESC record (dict of schema |EscSensorRecord|).
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_objects: A list of FAD objects from SAS Test Harness
  Returns:
    ap_iap_ref: The post-IAP allowed interference, as a dict formatted as:
        {latitude : {longitude : [interference(mW/IAPBW), .., interference(mW/IAPBW)]}}
      where the list holds all values per channel of that protection point.
  """
  esc_thresh_q = THRESH_ESC_DBM_PER_RBW + interf.linearToDb(IAPBW_HZ / ESC_RBW_HZ)

  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  # Final IAP protection threshold for ESC is considered after subtracting
  # insertion loss
  esc_iap_threshold = interf.dbToLinear(esc_thresh_q - MARGIN_ESC_DB
                                        + interf.IN_BAND_INSERTION_LOSS)

  grants = data.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS
  num_sas = len(sas_th_fad_objects) + 1

  # Get the ESC infos
  protection_point, esc_antenna_info = data.getEscInfo(esc_record)

  # Get ESC passband 3550-3680 MHz protection channels
  protection_channels = interf.getProtectedChannels(interf.ESC_LOW_FREQ_HZ,
                                                    interf.ESC_HIGH_FREQ_HZ)

  logging.debug('$$$$ Calling ESC Protection $$$$')
  # ESC algorithm
  asas_interference = interf.getInterferenceObject()
  aggr_interference = interf.getInterferenceObject()
  iapPointConstraint(protection_point, protection_channels,
                     interf.ESC_LOW_FREQ_HZ, interf.ESC_HIGH_FREQ_HZ,
                     grants, None, esc_antenna_info, None,
                     esc_iap_threshold, data.ProtectedEntityType.ESC,
                     asas_interference, aggr_interference)

  ap_iap_ref = calculatePostIapAggregateInterference(
      interf.dbToLinear(esc_thresh_q), num_sas,
      asas_interference, aggr_interference)
  return ap_iap_ref


def performIapForGwpz(gwpz_record, sas_uut_fad_object, sas_th_fad_objects):
  """Computes post IAP interference margin for GWPZ incumbents.

  Routine to get protection points within GWPZ protection area and perform
  IAP algorithm on each protection point.

  Args:
    gwpz_record: A GWPZ record dict.
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_objects: A list of FAD objects from SAS Test Harness
  Returns:
    ap_iap_ref: The post-IAP allowed interference, as a dict formatted as:
        {latitude : {longitude : [interference(mW/IAPBW), .., interference(mW/IAPBW)]}}
      where the list holds all values per channel of that protection point.
  """
  gwpz_thresh_q = THRESH_GWPZ_DBM_PER_RBW + interf.linearToDb(IAPBW_HZ / GWPZ_RBW_HZ)

  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  gwpz_iap_threshold = interf.dbToLinear(gwpz_thresh_q - MARGIN_GWPZ_DB)

  grants = data.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS
  num_sas = len(sas_th_fad_objects) + 1

  logging.debug('$$$$ Getting GRID points for GWPZ Protection Area $$$$')
  # Get Fine Grid Points for a GWPZ protection area
  protection_points = utils.GridPolygon(gwpz_record['zone']['features'][0]['geometry'],
                                        GWPZ_GRID_RES_ARCSEC)

  gwpz_freq_range = gwpz_record['record']['deploymentParam'][0]\
                               ['operationParam']['operationFrequencyRange']
  gwpz_low_freq = gwpz_freq_range['lowFrequency']
  gwpz_high_freq = gwpz_freq_range['highFrequency']
  gwpz_region = gwpz_record['landCategory']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(gwpz_low_freq, gwpz_high_freq)

  asas_interference = interf.getInterferenceObject()
  aggr_interference = interf.getInterferenceObject()
  logging.debug('$$$$ Calling GWPZ Protection $$$$')
  iapPoint = partial(iapPointConstraint,
                     channels=protection_channels,
                     low_freq=gwpz_low_freq,
                     high_freq=gwpz_high_freq,
                     grants=grants,
                     fss_info=None,
                     esc_antenna_info=None,
                     region_type=gwpz_region,
                     threshold=gwpz_iap_threshold,
                     protection_ent_type=data.ProtectedEntityType.GWPZ_AREA,
                     asas_interference=asas_interference,
                     aggr_interference=aggr_interference)
  pool = mpool.Pool()
  pool.map(iapPoint, protection_points)

  ap_iap_ref = calculatePostIapAggregateInterference(
      interf.dbToLinear(gwpz_thresh_q), num_sas,
      asas_interference, aggr_interference)

  return ap_iap_ref


def performIapForPpa(ppa_record, sas_uut_fad_object, sas_th_fad_objects,
                     pal_records):
  """Computes post IAP interference margin for PPA incumbents.

  Routine to get protection points within PPA protection area and perform
  IAP algorithm on each protection point.

  Args:
    ppa_record: A PPA record dict.
    sas_uut_fad_object: A FAD object from SAS UUT.
    sas_th_fad_object: A list of FAD objects from SAS Test Harness
    pal_records: PAL records associated with a PPA protection area
  Returns:
    ap_iap_ref: The post-IAP allowed interference, as a dict formatted as:
        {latitude : {longitude : [interference(mW/IAPBW), .., interference(mW/IAPBW)]}}
      where the list holds all values per channel of that protection point.
  """
  ppa_thresh_q = THRESH_PPA_DBM_PER_RBW + interf.linearToDb(IAPBW_HZ / PPA_RBW_HZ)

  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  ppa_iap_threshold = interf.dbToLinear(ppa_thresh_q - MARGIN_PPA_DB)

  grants = data.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects,
                                       ppa_record)

  # Get number of SAS
  num_sas = len(sas_th_fad_objects) + 1

  logging.debug('$$$$ Getting GRID points for PPA Protection Area $$$$')

  # Get Fine Grid Points for a PPA protection area
  protection_points = utils.GridPolygon(ppa_record['zone']['features'][0]['geometry'],
                                        PPA_GRID_RES_ARCSEC)

  # Get the region type of the PPA protection area
  ppa_region = ppa_record['ppaInfo']['ppaRegionType']

  # Find the PAL records for the PAL_IDs defined in PPA records
  ppa_pal_ids = ppa_record['ppaInfo']['palId']

  matching_pal_records = [pr for pr in pal_records if pr['palId'] == ppa_pal_ids[0]]
  if not matching_pal_records:
    raise ValueError('No matching PAL record, please check input')

  pal_record = matching_pal_records[0]

  # Get the frequencies from the PAL records
  ppa_freq_range = pal_record['channelAssignment']['primaryAssignment']
  ppa_low_freq = ppa_freq_range['lowFrequency']
  ppa_high_freq = ppa_freq_range['highFrequency']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(ppa_low_freq, ppa_high_freq)

  # Apply IAP for each protection constraint with a pool of parallel
  # processes.
  logging.debug('$$$$ Calling PPA Protection $$$$')
  asas_interference = interf.getInterferenceObject()
  aggr_interference = interf.getInterferenceObject()
  iapPoint = partial(iapPointConstraint,
                     channels=protection_channels,
                     low_freq=ppa_low_freq,
                     high_freq=ppa_high_freq,
                     grants=grants,
                     fss_info=None,
                     esc_antenna_info=None,
                     region_type=ppa_region,
                     threshold=ppa_iap_threshold,
                     protection_ent_type=data.ProtectedEntityType.PPA_AREA,
                     asas_interference=asas_interference,
                     aggr_interference=aggr_interference)
  pool = mpool.Pool()
  pool.map(iapPoint, protection_points)

  ap_iap_ref = calculatePostIapAggregateInterference(
      interf.dbToLinear(ppa_thresh_q), num_sas,
      asas_interference, aggr_interference)

  return ap_iap_ref


def performIapForFssCochannel(fss_record, sas_uut_fad_object, sas_th_fad_objects):
  """Computes post IAP interference margin for FSS Co-channel incumbent.

  FSS protection is provided over co-channel pass band.

  Args:
    fss_record: A FSS record (dict).
    sas_uut_fad_object: A FAD object from SAS UUT
    sas_th_fad_object: A list of FAD objects from SAS Test Harness
  Returns:
    ap_iap_ref: The post-IAP allowed interference, as a dict formatted as:
        {latitude : {longitude : [interference(mW/IAPBW), .., interference(mW/IAPBW)]}}
      where the list holds all values per channel of that protection point.
  """
  fss_cochannel_thresh_q = (THRESH_FSS_CO_CHANNEL_DBM_PER_RBW
                            + interf.linearToDb(IAPBW_HZ / FSS_RBW_HZ))

  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  fss_cochannel_iap_threshold = interf.dbToLinear(fss_cochannel_thresh_q
                                                  - MARGIN_FSS_CO_CHANNEL_DB)

  grants = data.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS
  num_sas = len(sas_th_fad_objects) + 1

  # Get the FSS infos
  fss_point, fss_info, fss_freq_range = data.getFssInfo(fss_record)
  fss_low_freq, fss_high_freq = fss_freq_range

  # Get channels for co-channel CBSDs
  assert(fss_high_freq >= interf.CBRS_HIGH_FREQ_HZ)
  protection_channels = interf.getProtectedChannels(fss_low_freq, interf.CBRS_HIGH_FREQ_HZ)

  asas_interference = interf.getInterferenceObject()
  aggr_interference = interf.getInterferenceObject()
  # FSS Co-channel algorithm
  logging.debug('$$$$ Calling FSS co-channel Protection $$$$')
  iapPointConstraint(fss_point,
                     protection_channels,
                     fss_low_freq,
                     interf.CBRS_HIGH_FREQ_HZ,
                     grants,
                     fss_info,
                     None,
                     None,
                     fss_cochannel_iap_threshold,
                     data.ProtectedEntityType.FSS_CO_CHANNEL,
                     asas_interference,
                     aggr_interference)

  ap_iap_ref = calculatePostIapAggregateInterference(
      interf.dbToLinear(fss_cochannel_thresh_q), num_sas,
      asas_interference, aggr_interference)

  return ap_iap_ref


def performIapForFssBlocking(fss_record, sas_uut_fad_object, sas_th_fad_objects):
  """Computes post IAP interference margin for FSS Blocking incumbent.

  FSS protection is provided over blocking pass band.

  Args:
    fss_record: A FSS record (dict).
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
  Returns:
    ap_iap_ref: The post-IAP allowed interference, as a dict formatted as:
        {latitude : {longitude : [interference(mW/IAPBW), .., interference(mW/IAPBW)]}}
      where the list holds all values per channel of that protection point.
  """
  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  fss_blocking_iap_threshold = interf.dbToLinear(THRESH_FSS_BLOCKING_DBM_PER_RBW -
                                                 MARGIN_FSS_BLOCKING_DB)

  grants = data.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS
  num_sas = len(sas_th_fad_objects) + 1

  # Get FSS T&C Flag value
  fss_ttc_flag = fss_record['ttc']

  # Get the FSS infos
  fss_point, fss_info, fss_freq_range = data.getFssInfo(fss_record)
  fss_low_freq, fss_high_freq = fss_freq_range

  # FSS Passband is between 3700 and 4200 and TT&C flag is set to FALSE
  if (fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and
      fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ and
      fss_ttc_flag is False):
    raise Exception("IAP for FSS not applied for FSS Pass band 3700 to 4200 "
                    "and TT&C flag set to false, please check the inputs.")

  logging.debug('$$$$ Calling FSS blocking Protection $$$$')
  # 5MHz channelization is not required for Blocking protection
  protection_channels = [(interf.CBRS_LOW_FREQ_HZ, fss_low_freq)]
  asas_interference = interf.getInterferenceObject()
  aggr_interference = interf.getInterferenceObject()
  iapPointConstraint(fss_point,
                     protection_channels,
                     interf.CBRS_LOW_FREQ_HZ,
                     fss_low_freq,
                     grants,
                     fss_info,
                     None,
                     None,
                     fss_blocking_iap_threshold,
                     data.ProtectedEntityType.FSS_BLOCKING,
                     asas_interference,
                     aggr_interference)

  ap_iap_ref = calculatePostIapAggregateInterference(
      interf.dbToLinear(THRESH_FSS_BLOCKING_DBM_PER_RBW), num_sas,
      asas_interference, aggr_interference)
  return ap_iap_ref


def calculatePostIapAggregateInterference(q_p, num_sas,
                                          asas_interference,
                                          aggr_interference):
  """Computes post IAP allowed aggregate interference.

  Routine to calculate aggregate interference from all the CBSDs managed by the
  SAS at protected entity.

  Args:
    q_p: Pre IAP threshold value for protection type (mW)
    num_sas: Number of SASs in the peer group
    asas_interference: The |interf.AggregateInterferenceOutputFormat| interference
      container for the managing SAS. A dictionary in the format of
      {latitude : {longitude : [asas_p(mW/IAPBW), asas_p(mW/IAPBW)]}}, where
      asas_p is aggregate interference calculated within IAPBW by managing SAS using
      the EIRP obtained from IAP results for that point p for CBSDs managed by the
      managing SAS. Only grants overlapping IAPBW are used in the calculation
    aggr_interference: The |interf.AggregateInterferenceOutputFormat| interference
      container for the managing SAS and peer SASes. Same as `asas_interference`
      but for all CBSDs managed by all SASes.

  Returns:
    ap_iap_ref: The post-IAP allowed interference, as a dict formatted as:
        {latitude : {longitude : [interference(mW/IAPBW), .., interference(mW/IAPBW)]}}
      where the list holds all values per channel of that protection point.
  """
  ap_iap_ref = {}
  # Extract dictionary from DictProxy object using _getvalue object method
  asas_info = asas_interference.GetAggregateInterferenceInfo()._getvalue()
  a_p_info = aggr_interference.GetAggregateInterferenceInfo()._getvalue()

  # Compute AP_IAP_Ref
  for latitude, a_p_ch in a_p_info.items():
    ap_iap_ref[latitude] = {}
    for longitude, a_p_list in a_p_ch.items():
      ap_iap_ref[latitude][longitude] = [
          ((q_p - a_p) / num_sas + asas_info[latitude][longitude][idx])
          for idx, a_p in enumerate(a_p_list)]

  return ap_iap_ref
