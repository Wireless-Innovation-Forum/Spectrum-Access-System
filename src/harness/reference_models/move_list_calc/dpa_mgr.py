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
import functools

import numpy as np

from reference_models.geo import zones
from reference_models.common import data
from reference_models.common import mpool
from reference_models.move_list_calc import move_list as ml

# The default protection threshold
DPA_DEFAULT_THRESHOLD_PER_10MHZ = -144

# The channel bandwidth
DPA_CHANNEL_BANDWIDTH = 10


class Dpa(object):
  """Dynamic Protection Area.

  A dynamic protection area is an ESC/Portal triggered protection area, ie not always on.
  There are 2 main types of DPA: Coastal DPAs and Inland DPAs.
  The difference between the two are mainly the set of parameters to use for
  its protection.

  Most DPA are co-channel only, although a few have also Out-Of-Band protected channels
  for which special protection logic is run.

  Attributes:
    channels: The list of (freq_min_mhz, freq_max_mhz) to protect for that DPA.
    protected_points: A list of namedtuple (latitude, longitude) defining the actual
      points to protect within the DPA.
    threshold: The protection threshold (in dBm per 10MHz). The 95% quantile of the
      aggregated interference shall not exceed this level.
    radar_height: The radar height (meters).
    beamwidth: The radar antenna beamwidth (degrees).
    azimuth_range: The radar azimuth range (degrees) as a tuple of
      (min_azimuth, max_azimuth) relative to true north. UNUSED for now

    grants: The list of registered grants.
    move_lists: A list of move list (list of |CbsdGrantInfo|) per channel.
    keep_lists: A list of keep list (list of |CbsdGrantInfo|) per channel.

  Usage:
    # Setup the DPA
    dpa = Dpa(protected_points)
    dpa.SetGrantsFromFad(sas_uut_fad, sas_th_fads)

    # Compute the move list
    dpa.ComputeMoveLists()

    # Calculate the keep list interference for a given channel
    interf_per_point = dpa.CalcKeepListInterference(channel)

    # Check the interference according to Winnforum IPR tests
    status = dpa.CheckInterference(channel, sas_uut_keep_list, margin_db=1)
  """
  # TODO(sbdt): add internal support for azimuth range, since it is used by some
  # inland DPAs.
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

  def SetGrantsFromList(self, grants):
    """Sets the list of grants from a list |data.CbsdGrantInfo|."""
    # TODO(sbdt): optim = pre-filtering of grants in global DPA neighborhood.
    self.grants = grants
    self.ResetLists()

  def ComputeMoveLists(self):
    """Computes move/keep lists.

    This routine updates the internal grants move list and neighbor list. One set of list
    is maintained per protected channel.
    To retrieve the list, see the routines GetMoveList(), GetNeighborList() and
    GetKeepList().
    """
    pool = mpool.Pool()
    self.ResetLists()
    for low_freq, high_freq in self.channels:
      moveListConstraint = functools.partial(
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
      self.move_lists.append(set(self.grants[k] for k in move_list))
      self.nbor_lists.append(set(self.grants[k] for k in nbor_list))

  def _GetChanIdx(self, channel):
    """Gets the channel idx for a given channel."""
    try:
      chan_idx = self.channels.index(channel)
    except ValueError:
      raise ValueError('Channel {} not protected by this DPA'.format(channel))
    return chan_idx

  def GetMoveList(self, channel):
    """Returns the move list for a given channel, as a set of grants.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
    """
    return self.move_lists[self._GetChanIdx(channel)]

  def GetNeighborList(self, channel):
    """Returns the neighbor list for a given channel, as a set of grants.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
    """
    return self.nbor_lists[self._GetChanIdx(channel)]

  def GetKeepList(self, channel):
    """Returns the keep list for a given channel, as a set of grants.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
    """
    return self.GetNeighborList(channel).difference(self.GetMoveList(channel))

  def GetMoveListMask(self, channel):
    """Returns move list mask as a vector of bool.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
    """
    # Legacy function for getting a mask, as used in some example code.
    move_list = self.GetMoveList(channel)
    mask = np.zeros(len(self.grants), np.bool)
    for k, grant in enumerate(self.grants):
      if grant in move_list:
        mask[k] = True
    return mask

  def CalcKeepListInterference(self, channel, num_iter=None):
    """Calculates max aggregate interference per protected point.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
      num_iter: The number of Monte Carlo iteration when calculating the aggregate
        interference.

    Returns:
      The 95% aggregate interference per protected point, as a list.
      Each element is the maximum aggregate interference over all radar directions.
    """
    if num_iter is None:
      num_iter = Dpa.num_iteration
    keep_list = self.GetKeepList(channel)
    interfCalculator = functools.partial(
        ml.calcAggregatedInterference,
        low_freq=channel[0] * 1e6,
        high_freq=channel[1] * 1e6,
        grants=keep_list,
        exclusion_zone=Dpa.protection_zone,
        inc_ant_height=self.radar_height,
        num_iter=num_iter,
        beamwidth=self.beamwidth,
        do_max=True)

    pool = mpool.Pool()
    max_interf = list(pool.map(interfCalculator,
                               self.protected_points))
    return max_interf

  def CheckInterference(self, channel, sas_uut_active_grants, margin_db, num_iter=None):
    """Checks interference of keep list of SAS UUT vs test harness.

    This compares the aggregated interference (within some margin) generated by:
      - the test harness keep list, versus
      - the blended SAS UUT / Test harness keep list
    for all protection points and azimuth.

    Args:
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
      sas_uut_active_grants: An iterable of authorized |data.CbsdGrantInfo| grants.
        of the SAS UUT (ie not in the move list).
      margin_db: The margin (in dB) to use for the check.
      num_iter: The number of Monte Carlo iteration for calculating the aggregate
        interference.

    Returns:
      True if all SAS UUT aggregated interference are within margin, False otherwise
      (ie if at least one combined protection point / azimuth fails the test).
    """
    keep_list = self.GetKeepList(channel)
    nbor_list = self.GetNeighborList(channel)
    if num_iter is None:
      num_iter = Dpa.num_iteration
    # Find the keep list of TH and SAS UUT
    keep_list_th_other_sas = [
        grant for grant in self.grants
        if (not grant.is_managed_grant and
            grant in keep_list)]
    keep_list_th_managing_sas = [
        grant for grant in self.grants
        if (grant.is_managed_grant and
            grant in keep_list)]
    keep_list_uut_managing_sas = [
        grant for grant in sas_uut_active_grants
        if (grant in nbor_list and
            grant not in keep_list_th_other_sas)]

    checkPointInterf = functools.partial(
        _CalcTestPointInterfDiff,
        channel=channel,
        keep_list_th_other_sas=keep_list_th_other_sas,
        keep_list_th_managing_sas=keep_list_th_managing_sas,
        keep_list_uut_managing_sas=keep_list_uut_managing_sas,
        radar_height=self.radar_height,
        beamwidth=self.beamwidth,
        protection_zone=Dpa.protection_zone,
        num_iter=num_iter)

    # TODO(sbdt): could do early stop as soon as one fails, although I expect
    # the criteria to be changed into checking 99.x% of success instead of 100%.
    pool = mpool.Pool()
    result = list(pool.map(checkPointInterf, self.protected_points))
    max_diff_interf = max(result)
    return max_diff_interf <= margin_db


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
    min_freq = int(freq_range[0] / DPA_CHANNEL_BANDWIDTH) * DPA_CHANNEL_BANDWIDTH
    max_freq = int(freq_range[1] / DPA_CHANNEL_BANDWIDTH) * DPA_CHANNEL_BANDWIDTH
    freqs = np.arange(min_freq, max_freq, DPA_CHANNEL_BANDWIDTH)
    for freq in freqs:
      channels.add((freq, freq + DPA_CHANNEL_BANDWIDTH))
  return sorted(list(channels))

def _CalcTestPointInterfDiff(point,
                             channel,
                             keep_list_th_other_sas,
                             keep_list_th_managing_sas,
                             keep_list_uut_managing_sas,
                             radar_height,
                             beamwidth,
                             protection_zone,
                             num_iter):
  """Calculate difference of aggregate interference between reference and SAS UUT.

  This implements the check required by the IPR certification tests, comparing the
  reference model keep list aggregated interference versus the blended one.
  The blended one uses the SAS UUT authorized grants that it manages, plus the CBSD
  of other SAS in the keep list.

  Note that this routine reduce the amount of random variation by reusing the same
  random draw for the CBSD that are shared between the two keep lists. This is done
  by using the caching engine provided by |reference_models.common.cache|.

  Args:
    channel: A channel as tuple (low_freq_mhz, high_freq_mhz).
    keep_list_th_other_sas: A list of |data.CbsdGrantInfo| for non managing SAS, as
      computed by the reference model.
    keep_list_th_managing_sas: A list of |data.CbsdGrantInfo| for managing SAS, as
      computed by the reference model.
    keep_list_uut_managing_sas: A list of |data.CbsdGrantInfo| for managing SAS as
      computed by the SAS UUT.
    radar_height: The radar height (meters).
    beamwidth: The radar antenna beamwidth (degrees).
    protection_zone: A |shapely.Polygon/MultiPolygon| defining the CatA protection zone.
    num_iteration: The number of iteration to use in the Monte Carlo simulation.

  Returns:
    The maximum aggregated difference across all the radar pointing directions between
    the blended and the reference models.
  """
  # Perform caching of the per device interference, as to reduce the Monte-Carlo
  # variability on similar CBSD in keep list.
  # TODO(sbdt): check if better to context manage once per process, with clearing
  # in between.
  with ml.InterferenceCacheManager() as cm:
    th_interferences = ml.calcAggregatedInterference(
        point,
        low_freq=channel[0] * 1e6,
        high_freq=channel[1] * 1e6,
        grants=keep_list_th_other_sas + keep_list_th_managing_sas,
        exclusion_zone=protection_zone,
        inc_ant_height=radar_height,
        num_iter=num_iter,
        beamwidth=beamwidth)
    uut_interferences = ml.calcAggregatedInterference(
        point,
        low_freq=channel[0] * 1e6,
        high_freq=channel[1] * 1e6,
        grants=keep_list_th_other_sas + keep_list_uut_managing_sas,
        exclusion_zone=protection_zone,
        inc_ant_height=radar_height,
        num_iter=num_iter,
        beamwidth=beamwidth)
    return np.max(uut_interferences - th_interferences)
