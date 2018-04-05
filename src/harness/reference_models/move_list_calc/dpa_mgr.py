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

"""DPA (Dynamic Protection Area) manager.

This DPA manager manages the move list and interference calculation for a DPA.
DPA differs from other protection entities as the aggregated interference is
computed at specific percentile of the combined interference random variable.
"""

from collections import namedtuple
from functools import partial
import multiprocessing

import numpy as np

from reference_models.geo import zones
from reference_models.common import data
from reference_models.common import mpool
from reference_models.move_list_calc import move_list as ml

# The default protection threshold
DPA_DEFAULT_THRESHOLD_PER_10MHZ = -144

# The channel bandwidth
DPA_CHANNEL_BANDWIDTH = 10


# The protection specs, as required by move_list calc routine.
ProtectionSpecs = namedtuple('ProtectionSpecs',
                             ['lowFreq', 'highFreq',
                              'antHeight', 'beamwidth', 'threshold'])


class Dpa(object):
  """Dynamic Protection Area.

  A dynamic protection area is an ESC/Portal triggered protection area.
  There are 2 main types of DPA: Coastal DPAs and Inland DPAs.
  The difference between the two are mainly the set of parameters to use for
  its protection.

  Most DPA are co-channel DPA, although a few are Out-Of-Band for which special
  protection logic is run.

  Attributes:
    channels: The list of (freq_min_mhz, freq_max_mhz) to protect for that DPA.
    protected_points: A list of namedtuple (latitude, longitude) defining the actual
      points to protect within the DPA.
    threshold: The protection threshold (in dBm per 10MHz). The 95% quantile of the
      aggregated interference shall not exceed this level.
    radar_height: The radar height (meters).
    beamwidth: The radar antenna beamwidth (degrees).
    azimuth_range: The radar azimuth range (degrees) as a tuple of
      (min_azimuth, max_azimuth) relative to true north.

    grants: The list of registered grants.
    move_lists: A list of move list (list of |CbsdGrantInfo|) per channel.
    keep_lists: A list of keep list (list of |CbsdGrantInfo|) per channel.
  """
  # TODO(sbdt): review the holistic usage and definition across test harness
  num_iteration = 2000
  protection_zone = zones.GetCoastalProtectionZone()

  @classmethod
  def Configure(cls,
                protection_zone=None,
                num_iteration=2000):
    """Configure operating parameters.

    Args:
      protection_zone: A |shapely.Polygon/MultiPolygon| defining the CatA protection zone.
      num_iteration: The number of iteration to use in the Monte Carlo simulation.
    """
    cls.num_iteration = num_iteration
    if protection_zone is not None:
      cls.protection_zone = protection_zone

  def __init__(self, protected_points,
               threshold=DPA_DEFAULT_THRESHOLD_PER_10MHZ,
               radar_height=50,
               beamwidth=3,
               azimuth_range=(0, 360),
               freq_ranges_mhz=(3550, 3650)):
    """Initialize the DPA attributes."""
    self.protected_points = protected_points
    self.threshold = threshold
    self.radar_height = radar_height
    self.azimuth_range = azimuth_range
    self.beamwidth = beamwidth
    self.channels = GetDpaProtectedChannels(freq_ranges_mhz)
    self.grants = []
    self.ResetLists()

  def ResetLists(self):
    """Reset move list and keep list."""
    self.move_lists = []
    self.nbor_lists = []

  def SetGrantsFromFad(self, sas_uut_fad, sas_th_fads):
    """Sets the list of grants.

    Args:
      sas_uut_fad: The FAD object of SAS UUT.
      sas_th_fads: A list of FAD objects of other SAS test harness.
    """
    # TODO(sbdt): optim = pre-filtering of grants in global DPA neighborhood.
    self.grants = data.getGrantObjectsFromFAD(sas_uut_fad, sas_th_fads)
    self.ResetLists()
    # TEMP: Embed an index to every grant as required by the move_list internals.
    #       Remove this as this does not support multi DPA processing in parallel.
    for k, grant in enumerate(self.grants):
      grant.grant_index = k

  def SetGrantsFromList(self, grants):
    """Sets the list of grants from a list |data.CbsdGrantInfo|."""
    # TODO(sbdt): optim = pre-filtering of grants in global DPA neighborhood.
    self.grants = grants
    self.ResetLists()
    # TEMP: Embed an index to every grant as required by the move_list internals.
    #       Remove this as this does not support multi DPA processing in parallel.
    for k, grant in enumerate(self.grants):
      grant.grant_index = k

  def CalcMoveLists(self):
    """Calculate move/keep lists.
    """
    pool = mpool.Pool()
    self.ResetLists()
    for low_freq, high_freq in self.channels:
      moveListConstraint = partial(
          ml.moveListConstraint,
          low_freq=low_freq * 1.e6,
          high_freq=high_freq * 1.e6,
          grants=self.grants,
          exclusion_zone=Dpa.protection_zone,
          inc_ant_height=self.radar_height,
          num_iter=Dpa.num_iteration,
          threshold=self.threshold,
          beamwidth=self.beamwidth)

      move_list, nbor_list = zip(*pool.map(moveListConstraint,
                                           self.protected_points))

      # Combine the individual point move lists
      move_list = set().union(*move_list)
      nbor_list = set().union(*nbor_list)
      # TODO(sbdt): store as set() once immutability restored
      self.move_lists.append([self.grants[k] for k in move_list])
      self.nbor_lists.append([self.grants[k] for k in nbor_list])

  def _GetChanIdx(self, channel):
    try:
      chan_idx = self.channels.index(channel)
    except ValueError:
      raise ValueError('Channel {} not protected by this DPA'.format(channel))
    return chan_idx

  def GetMoveListMask(self, channel):
    """Returns move list mask as a vector of bool.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
    """
    # Legacy function for old example.
    move_list = self.move_lists[self._GetChanIdx(channel)]
    mask = np.zeros(len(self.grants), np.bool)
    mask[[grant.grant_index for grant in move_list]] = True
    return mask

  def CheckInterference(self, channel, grants_uut_managed_active, margin):
    """Checks interference of keep list of SAS UUT vs test harness.

    This compares the aggregated interference (within some margin) generated by:
      - the test harness keep list, versus
      - the blended SAS UUT / Test harness keep list
    for all protection points and azimuth.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
      grants_uut_managed_active: A list of active |data.CbsdGrantInfo| grants
        not in the move list for the SAS UUT and managed by the SAS.
      margin

    Returns:
      True if all SAS UUT aggregated interference are within margin.
      False if at least one combined protection point / azimuth fails the test.
    """
    chan_idx = self._GetChanIdx(channel)
    move_list = self.move_lists[chan_idx]
    nborlist = self.nbor_lists[chan_idx]

    # Find the keep list of TH and SAS UUT
    keep_list_th_other_sas = [
        grant for grant in self.grants
        if (not grant.is_managed_grant and
            grant in nbor_list and
            grant not in move_list)]
    keep_list_th_managing_sas = [
        grant for grant in self.grants
        if (grant.is_managed_grant and
            grant in nbor_lists and
            grant not in move_list)]
    keep_list_uut_managing_sas = [
        grant for grant in grants_uut_managed_active
        if (grant in nbor_list and
            grant not in keep_list_th_other_sas)]

    # TODO(sbdt): multiprocess this calculation
    for point in self.protected_points:
      th_interferences = ml.CalcInterference(
          point,
          low_freq=channel[0] * 1e6,
          high_freq=channel[1] * 1e6,
          grants=keep_list_th_other_sas + keep_list_th_managing_sas,
          exclusion_zone=Dpa.protection_zone,
          inc_ant_height=self.radar_height,
          num_iter=Dpa.num_iteration,
          beamwidth=self.beamwidth)

      uut_interferences = ml.CalcInterference(
          point,
          low_freq=channel[0] * 1e6,
          high_freq=channel[1] * 1e6,
          grants=keep_list_th_other_sas + keep_list_uut_managing_sas,
          exclusion_zone=Dpa.protection_zone,
          inc_ant_height=self.radar_height,
          num_iter=Dpa.num_iteration,
          beamwidth=self.beamwidth)

      max_diff_interf = np.max(uut_interferences - th_interferences)
      if max_diff_interf > margin:
        return False

    return True


def GetDpaProtectedChannels(freq_ranges_mhz):
  """ Gets protected channels list for DPA.

  Args:
    freq_ranges_mhz: The protection frequencies (MHz) as a list of tuple
      (freq_min_mhz, freq_max_mhz) of the DPA protected frequency ranges.

  Returns:
    A list of protected channels as a tuple (low_freq_mhz, high_freq_mhz)
  """
  channels = set()
  for freq_range in freq_ranges_mhz:
    min_freq = int(freq_range[0] / 10.) * 10
    max_freq = int(freq_range[1] / 10.) * 10
    freqs = np.arange(min_freq, max_freq, 10)
    for freq in freqs:
      channels.add((freq, freq+10))
  return sorted(list(channels))
