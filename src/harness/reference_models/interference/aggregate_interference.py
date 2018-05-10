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

from reference_models.common import mpool
from reference_models.common import data
from reference_models.interference import interference as interf
from reference_models.geo import utils

# The grid resolution for area based protection entities.
GWPZ_GRID_RES_ARCSEC = 2
PPA_GRID_RES_ARCSEC = 2


def calculateAggregateInterferenceForFssCochannel(fss_record, cbsd_list):
  """Calculates aggregate interference for FSS co-channel.

  Calculates aggregate interference for each protection constraint in the FSS
  co-channel based on the interferences caused by CBSD's grants in the
  neighborhood of the FSS co-channel protection entity.

  Args:
    fss_record: FSS co-channel protection entity
    cbsd_list: list of CbsdGrantInfo objects containing registrations and grants

  Returns:
    Aggregate interference to FSS co-channel in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
  """
  # Get the protection point of the FSS
  fss_point = fss_record['record']['deploymentParam'][0]['installationParam']
  protection_point = ( fss_point['longitude'], fss_point['latitude'])

  # Get the frequency range of the FSS
  fss_freq_range = fss_record['record']['deploymentParam'][0]\
                     ['operationParam']['operationFrequencyRange']
  fss_low_freq = fss_freq_range['lowFrequency']
  fss_high_freq = fss_freq_range['highFrequency']

  # Get FSS information
  fss_info = data.FssInformation(height_agl=fss_point['height'],
               max_gain_dbi=fss_point['antennaGain'],
               pointing_azimuth=fss_point['antennaAzimuth'],
               pointing_elevation=fss_point['antennaDowntilt'])

  # Get channels for co-channel CBSDs
  if fss_high_freq < interf.CBRS_HIGH_FREQ_HZ:
    protection_channels = interf.getProtectedChannels(fss_low_freq, fss_high_freq)
  else:
    protection_channels = interf.getProtectedChannels(fss_low_freq, interf.CBRS_HIGH_FREQ_HZ)

  aggregate_interference = interf.getInterferenceObject()
  interf.aggregateInterferenceForPoint(protection_point,
      protection_channels, cbsd_list, fss_info, None,
      data.ProtectedEntityType.FSS_CO_CHANNEL, None,
      aggregate_interference)

  # Extract dictionary from DictProxy object using _getvalue() object method
  return aggregate_interference.GetAggregateInterferenceInfo()._getvalue()


def calculateAggregateInterferenceForFssBlocking(fss_record, cbsd_list):
  """Calculates aggregate interference for FSS blocking.

  Calculates aggregate interference for FSS blocking pass band based on the
  interferences caused by CBSD's grants in the neighborhood of the FSS
  blocking protection entity.

  Args:
    fss_record: FSS blocking protection entity
    cbsd_list: list of CbsdGrantInfo objects containing registrations and grants
  Returns:
    Aggregate interference to FSS blocking in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
  """
  fss_ttc_flag = fss_record['ttc']
  # Get the protection point of the FSS
  fss_point = fss_record['record']['deploymentParam'][0]['installationParam']
  protection_point = (fss_point['longitude'], fss_point['latitude'])

  # Get the frequency range of the FSS
  fss_freq_range = fss_record['record']['deploymentParam'][0]\
                     ['operationParam']['operationFrequencyRange']
  fss_low_freq = fss_freq_range['lowFrequency']
  fss_high_freq = fss_freq_range['highFrequency']

  # Get FSS information
  fss_info = data.FssInformation(height_agl=fss_point['height'],
               max_gain_dbi=fss_point['antennaGain'],
               pointing_azimuth=fss_point['antennaAzimuth'],
               pointing_elevation=fss_point['antennaDowntilt'])

  # FSS Passband is between 3700 and 4200 and TT&C flag is set to FALSE
  if(fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and
       fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ and
       fss_ttc_flag is False):
    raise Exception("IAP for FSS not applied for FSS Pass band 3700 to 4200 "
                    "and TT&C flag set to false, please check the inputs.")
  else:
    # 5MHz channelization is not required for Blocking protection
    # FSS TT&C Blocking Algorithm
    protection_channels = [(interf.CBRS_LOW_FREQ_HZ, fss_low_freq)]

    aggregate_interference = interf.getInterferenceObject()
    interf.aggregateInterferenceForPoint(protection_point,
      protection_channels, cbsd_list, fss_info, None,
      data.ProtectedEntityType.FSS_BLOCKING, None,
      aggregate_interference)

  # Extract dictionary from DictProxy object using _getvalue() object method
  return aggregate_interference.GetAggregateInterferenceInfo()._getvalue()


def calculateAggregateInterferenceForEsc(esc_record, cbsd_list):
  """Calculates aggregate interference for ESC.

  Calculates aggregate interference for each protection constraint in the ESC
  based on the interferences caused by CBSD's grants in the neighborhood of
  the ESC protection entity.

  Args:
    esc_record: ESC protection entity
    cbsd_list: list of CbsdGrantInfo objects containing registrations and grants
  Returns:
    Aggregate interference to ESC in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
  """
  # Get the protection point of the ESC
  esc_point = esc_record['installationParam']
  protection_point = (esc_point['longitude'], esc_point['latitude'])

  # Get azimuth radiation pattern
  ant_pattern = esc_point['azimuthRadiationPattern']
  ant_pattern = sorted([(pat['angle'], pat['gain']) for pat in ant_pattern])
  angles, gains = zip(*ant_pattern)
  if angles != tuple(range(360)):
    raise ValueError('ESC pattern inconsistent')
  ant_gain_pattern = np.array(gains)

  # Get ESC antenna information
  esc_antenna_info = data.EscInformation(
      antenna_height=esc_point['height'],
      antenna_azimuth=esc_point['antennaAzimuth'],
      antenna_gain_pattern=ant_gain_pattern)

  # Get ESC passband 3550-3680 MHz protection channels
  protection_channels = interf.getProtectedChannels(interf.ESC_LOW_FREQ_HZ,
                                                    interf.ESC_HIGH_FREQ_HZ)

  aggregate_interference = interf.getInterferenceObject()
  interf.aggregateInterferenceForPoint(protection_point,
    protection_channels, cbsd_list, None,
    esc_antenna_info, data.ProtectedEntityType.ESC, None,
    aggregate_interference)

  # Extract dictionary from DictProxy object using _getvalue() object method
  return aggregate_interference.GetAggregateInterferenceInfo()._getvalue()


def calculateAggregateInterferenceForGwpz(gwpz_record, cbsd_list):
  """Calculates aggregate interference for GWPZ.

  Calculates aggregate interference for each protection constraint in the GWPZ
  based on the interferences caused by CBSD's grants in the neighborhood of
  the GWPZ protection entity.

  Args:
    gwpz_record: GWPZ protection entity
    cbsd_list: list of CbsdGrantInfo objects containing registrations and grants
  Returns:
    Aggregate interference to GWPZ in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
  """
  gwpz_region = gwpz_record['landCategory']

  # Get Fine Grid Points for a GWPZ protection area
  protection_points = utils.GridPolygon(gwpz_record['zone']['features'][0]['geometry'],
                                        GWPZ_GRID_RES_ARCSEC)
  gwpz_freq_range = gwpz_record['deploymentParam']['operationParam']['operationFrequencyRange']
  gwpz_low_freq = gwpz_freq_range['lowFrequency']
  gwpz_high_freq = gwpz_freq_range['highFrequency']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(gwpz_low_freq, gwpz_high_freq)

  # Calculate aggregate interference from each protection constraint with a
  # pool of parallel processes.
  aggregate_interference = interf.getInterferenceObject()

  interfCalculator = partial(interf.aggregateInterferenceForPoint,
                             channels=protection_channels, grants=cbsd_list,
                             fss_info=None, esc_antenna_info=None,
                             protection_ent_type=data.ProtectedEntityType.GWPZ_AREA,
                             region_type=gwpz_region,
                             aggregate_interference=aggregate_interference)

  pool = mpool.Pool()
  pool.map(interfCalculator, protection_points)

  # Extract dictionary from DictProxy object using _getvalue() object method
  return aggregate_interference.GetAggregateInterferenceInfo()._getvalue()


def calculateAggregateInterferenceForPpa(ppa_record, pal_list, cbsd_list):
  """Calculates aggregate interference for PPA.

  Calculates aggregate interference for each protection constraint in the PPA
  based on the interferences caused by CBSD's grants in the neighborhood of
  the PPA protection entity.

  Args:
    ppa_record: PPA protection entity
    pal_list: list of PAL records
    cbsd_list: list of CbsdGrantInfo objects containing registrations and grants
  Returns:
    Aggregate interference to PPA in the nested dictionary format.
      {latitude : {longitude: [aggr_interf1(mW), ..., aggr_interfK(mW)]}}
  """
  # Get Fine Grid Points for a PPA protection area
  protection_points = utils.GridPolygon(ppa_record['zone']['features'][0]['geometry'],
                                        PPA_GRID_RES_ARCSEC)

  # Get the region type of the PPA protection area
  ppa_region = ppa_record['ppaInfo']['ppaRegionType']

  # Find the PAL records for the PAL_IDs defined in PPA records
  ppa_pal_ids = ppa_record['ppaInfo']['palId']

  matching_pal_records = [pr for pr in pal_list if pr['palId'] == ppa_pal_ids[0]]
  if not matching_pal_records:
    raise ValueError('No matching PAL record, please check input')

  pal_record = matching_pal_records[0]

  # Get the frequencies from the PAL records
  ppa_freq_range = pal_record['channelAssignment']['primaryAssignment']
  ppa_low_freq = ppa_freq_range['lowFrequency']
  ppa_high_freq = ppa_freq_range['highFrequency']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(ppa_low_freq, ppa_high_freq)

  aggregate_interference = interf.getInterferenceObject()

  # Calculate aggregate interference from each protection constraint with a
  # pool of parallel processes.
  interfCalculator = partial(interf.aggregateInterferenceForPoint,
                             channels=protection_channels, grants=cbsd_list,
                             fss_info=None, esc_antenna_info=None,
                             protection_ent_type=data.ProtectedEntityType.PPA_AREA,
                             region_type=ppa_region,
                             aggregate_interference=aggregate_interference)

  pool = mpool.Pool()
  pool.map(interfCalculator, protection_points)

  # Extract dictionary from DictProxy object using _getvalue() object method
  return aggregate_interference.GetAggregateInterferenceInfo()._getvalue()
