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
  Aggregate Interference Calculations Reference Model[R2-SGN-12].
  Based on WINNF-TS-0061, Version V1.0.0-r5.1, 17 January 2018.

  This model provides the functions to calculate the aggregate interference for
  the protection constrains of FSS-Cochannel, FSS-Blocking, ESC, GWPZ and PPA.

  The main routines are:

    calculateAggregateInterferenceForFssCochannel
    calculateAggregateInterferenceForFssBlocking
    calculateAggregateInterferenceForEsc
    calculateAggregateInterferenceForGwpz
    calculateAggregateInterferenceForPpa

  The routines returns a nested dictionary in the format of
  {latitude : {longitude : [interference1, interference2]}}. interference
  is the aggregate interference value in mW for each of the protection constraint.
==================================================================================
"""

import numpy as np
from functools import partial
import logging

from reference_models.common import mpool
from reference_models.common import data
from reference_models.interference import interference as interf
from reference_models.geo import utils

# The grid resolution for area based protection entities.
GWPZ_GRID_RES_ARCSEC = 2
PPA_GRID_RES_ARCSEC = 2


def InterferenceDict(data_list):
  """Creates an interferenceReturns a double dict from a list of lat,lng, interferences."""
  if not isinstance(data_list, list):
    data_list = [data_list]
  result = {}
  for lat, lon, data in data_list:
    if lat not in result: result[lat] = {}
    result[lat][lon] = data

  return result


def convertAndSumInterference(cbsd_interference_list):
  """Converts interference in dBm to mW to calculate aggregate interference"""
  interferences_in_dbm = np.array(cbsd_interference_list)
  return np.sum(interf.dbToLinear(interferences_in_dbm))


def aggregateInterferenceForPoint(protection_point, channels, grants,
                                  fss_info, esc_antenna_info,
                                  protection_ent_type, region_type):
  """Computes the aggregate interference for a protection point.

  This routine is invoked to calculate aggregate interference for ESC sensor,
  FSS Co-channel/Blocking and PPA/GWPZ protection areas.

  Args:
    protection_point: The location of a protected entity as (longitude, latitude) tuple.
    channels: A sequence of channels as tuple (low_freq_hz, high_freq_hz).
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.
    fss_info: The FSS information of type |data.FssInformation| (optional).
    esc_antenna_info: ESC antenna information of type |data.EscInformation| (optional).
    protection_ent_type: The entity type (|data.ProtectedEntityType|).
    region: Region type of the protection point: 'URBAN', 'SUBURBAN' or 'RURAL'.

  Returns:
    A tuple (latitude, longitude, interferences) where interferences is a list
    of interference per channel.
  """

  # Get all the grants inside neighborhood of the protection entity
  grants_inside = interf.findGrantsInsideNeighborhood(
      grants, protection_point, protection_ent_type)

  if not grants_inside:
    # We need one entry per channel, even if they're all zero.
    return protection_point[1], protection_point[0], [0]*len(channels)

  interferences = []
  for channel in channels:
    # Get protection constraint over 5MHz channel range
    protection_constraint = data.ProtectionConstraint(
        latitude=protection_point[1], longitude=protection_point[0],
        low_frequency=channel[0], high_frequency=channel[1],
        entity_type=protection_ent_type)

    # Identify CBSD grants overlapping with frequency range of the protection entity
    # in the neighborhood of the protection point and channel
    neighborhood_grants = interf.findOverlappingGrants(grants_inside, protection_constraint)

    if not neighborhood_grants:
      interferences.append(0)
      continue

    cbsd_interferences = [
        interf.computeInterference(grant, grant.max_eirp, protection_constraint,
                                   fss_info, esc_antenna_info, region_type)
        for grant in neighborhood_grants]

    total_interference = convertAndSumInterference(cbsd_interferences)
    interferences.append(total_interference)

  return protection_point[1], protection_point[0], interferences


def calculateAggregateInterferenceForFssCochannel(fss_record, grants):
  """Calculates per-channel aggregate interference for FSS co-channel.

  Args:
    fss_record: A FSS record (dict).
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.

  Returns:
    Aggregate interference to FSS co-channel in the nested dictionary format:
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
    The list contains the value per protected channel.
  """
  # Get the FSS infos
  fss_point, fss_info, fss_freq_range = data.getFssInfo(fss_record)
  fss_low_freq, fss_high_freq = fss_freq_range

  # Get channels for co-channel CBSDs
  if fss_high_freq < interf.CBRS_HIGH_FREQ_HZ:
    raise ValueError('FSS high frequency should not be less than CBRS high frequency')

  protection_channels = interf.getProtectedChannels(fss_low_freq, interf.CBRS_HIGH_FREQ_HZ)

  logging.info(
      'Computing aggregateInterferenceForPoint for FSS Coch: channels (%s), grants (%s), point (%s), fss_info (%s)',
      protection_channels, grants, fss_point, fss_info)

  interferences = aggregateInterferenceForPoint(fss_point,
                                protection_channels,
                                grants,
                                fss_info,
                                None,
                                data.ProtectedEntityType.FSS_CO_CHANNEL,
                                None)
  return InterferenceDict(interferences)


def calculateAggregateInterferenceForFssBlocking(fss_record, grants):
  """Calculates per-channel aggregate interference for FSS blocking.

  Args:
    fss_record: A FSS record (dict).
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.

  Returns:
    Aggregate interference to FSS blocking in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
    The list contains the value per protected channel.
  """
  fss_ttc_flag = fss_record['ttc']

  # Get the FSS infos
  fss_point, fss_info, fss_freq_range = data.getFssInfo(fss_record)
  fss_low_freq, fss_high_freq = fss_freq_range

  # FSS Passband is between 3700 and 4200 and TT&C flag is set to FALSE
  if (fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and
      fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ and
      fss_ttc_flag is False):
    raise Exception("AggInterf for FSS not applied for FSS Pass band 3700 to 4200 "
                    "and TT&C flag set to false, please check the inputs.")

  # 5MHz channelization is not required for Blocking protection
  # FSS TT&C Blocking Algorithm
  protection_channels = [(interf.CBRS_LOW_FREQ_HZ, fss_low_freq)]

  logging.info(
      'Computing aggregateInterferenceForPoint for FSS Blocking: channels (%s), grants (%s), point (%s), fss_info (%s)',
      protection_channels, grants, fss_point, fss_info)

  interferences = aggregateInterferenceForPoint(fss_point,
                                protection_channels,
                                grants,
                                fss_info,
                                None,
                                data.ProtectedEntityType.FSS_BLOCKING,
                                None)

  return InterferenceDict(interferences)


def calculateAggregateInterferenceForEsc(esc_record, grants):
  """Calculates per-channel aggregate interference for ESC.

  Args:
    esc_record: An ESC record (dict of schema |EscSensorRecord|).
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.

  Returns:
    Aggregate interference to ESC in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
    The list contains the value per protected channel.
  """
  # Get the ESC infos
  protection_point, esc_antenna_info = data.getEscInfo(esc_record)

  # Get ESC passband 3550-3680 MHz protection channels
  protection_channels = interf.getProtectedChannels(interf.ESC_LOW_FREQ_HZ,
                                                    interf.ESC_HIGH_FREQ_HZ)

  logging.info(
      'Computing aggregateInterferenceForPoint for ESC: channels (%s), grants (%s), point (%s), antenna_info (%s)',
      protection_channels, grants, protection_point, esc_antenna_info)

  interferences = aggregateInterferenceForPoint(protection_point,
                                protection_channels,
                                grants,
                                None,
                                esc_antenna_info,
                                data.ProtectedEntityType.ESC,
                                None)

  return InterferenceDict(interferences)


def calculateAggregateInterferenceForGwpz(gwpz_record, grants):
  """Calculates per-channel aggregate interference for GWPZ.

  Args:
    gwpz_record: A GWPZ record dict.
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.

  Returns:
    Aggregate interference to GWPZ in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
    The list contains the value per protected channel.
  """
  gwpz_region = gwpz_record['landCategory']

  # Get Fine Grid Points for a GWPZ protection area
  protection_points = utils.GridPolygon(gwpz_record['zone']['features'][0]['geometry'],
                                        GWPZ_GRID_RES_ARCSEC)
  gwpz_freq_range = gwpz_record['record']['deploymentParam'][0]\
                               ['operationParam']['operationFrequencyRange']
  gwpz_low_freq = gwpz_freq_range['lowFrequency']
  gwpz_high_freq = gwpz_freq_range['highFrequency']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(gwpz_low_freq, gwpz_high_freq)

  # Calculate aggregate interference from each protection constraint with a
  # pool of parallel processes.
  logging.info(
      'Computing aggregateInterferenceForPoint for PPA (%s), channels (%s), grants (%s), region_type (%s) - nPoints (%d)',
      gwpz_record, protection_channels, grants, gwpz_region, len(protection_points))

  interfCalculator = partial(aggregateInterferenceForPoint,
                             channels=protection_channels,
                             grants=grants,
                             fss_info=None,
                             esc_antenna_info=None,
                             protection_ent_type=data.ProtectedEntityType.GWPZ_AREA,
                             region_type=gwpz_region)

  pool = mpool.Pool()
  interferences = pool.map(interfCalculator, protection_points)
  return InterferenceDict(interferences)



def calculateAggregateInterferenceForPpa(ppa_record, pal_records, grants):
  """Calculates per-channel aggregate interference for PPA.

  Args:
    ppa_record: A PPA record dict.
    pal_records: PAL records associated with a PPA protection area
    grants: An iterable of CBSD grants of type |data.CbsdGrantInfo|.

  Returns:
    Aggregate interference to PPA in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
    The list contains the value per protected channel.
  """
  # Get Fine Grid Points for a PPA protection area
  protection_points = utils.GridPolygon(ppa_record['zone']['features'][0]['geometry'],
                                        PPA_GRID_RES_ARCSEC)

  # Get the region type of the PPA protection area
  ppa_region = ppa_record['ppaInfo']['ppaRegionType']

  # Find the PAL records for the PAL_IDs defined in PPA records
  ppa_pal_ids = ppa_record['ppaInfo']['palId']

  matching_pal_records = [pr for pr in pal_records if pr['palId'] == ppa_pal_ids[0]]
  if not matching_pal_records:
    raise ValueError('AggInterf: No matching PAL record, please check input')

  pal_record = matching_pal_records[0]

  # Get the frequencies from the PAL records
  ppa_freq_range = pal_record['channelAssignment']['primaryAssignment']
  ppa_low_freq = ppa_freq_range['lowFrequency']
  ppa_high_freq = ppa_freq_range['highFrequency']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(ppa_low_freq, ppa_high_freq)

  logging.info(
      'Computing aggregateInterferenceForPoint for PPA (%s), channels (%s), grants (%s), region_type (%s) - nPoints (%d)',
      ppa_record, protection_channels, grants, ppa_region, len(protection_points))

  # Calculate aggregate interference from each protection constraint with a
  # pool of parallel processes.
  interfCalculator = partial(aggregateInterferenceForPoint,
                             channels=protection_channels,
                             grants=grants,
                             fss_info=None,
                             esc_antenna_info=None,
                             protection_ent_type=data.ProtectedEntityType.PPA_AREA,
                             region_type=ppa_region)

  pool = mpool.Pool()
  interferences = pool.map(interfCalculator, protection_points)
  return InterferenceDict(interferences)
