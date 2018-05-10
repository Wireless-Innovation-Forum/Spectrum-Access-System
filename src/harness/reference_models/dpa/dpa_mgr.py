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

Example usage:
  # Create a DPA
  # - either with a simple default protection points builder
  dpa = BuildDpa('East1', 'default (25,10,10,5)')
  # - or from a GeoJson file holding a MultiPoint geometry
  dpa = BuildDpa('East1', 'east_dpa_1_points.json')

  # Set the grants
  dpa.SetGrantsFromFad(sas_uut_fad, sas_th_fads)

  # Compute the move list
  dpa.ComputeMoveLists()

  # Calculate the keep list interference for a given channel
  channel = (3650, 3660)
  interf_per_point = dpa.CalcKeepListInterference(channel)

  # Check the interference according to Winnforum IPR tests
  status = dpa.CheckInterference(sas_uut_keep_list, margin_db=2)
"""
import ast
from collections import namedtuple
import functools
import os

import json
import numpy as np
import shapely.geometry as sgeo

from reference_models.geo import utils
from reference_models.geo import zones
from reference_models.common import data
from reference_models.common import mpool
from reference_models.dpa import move_list as ml

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
    channels: The list of 10MHz channels (freq_min_mhz, freq_max_mhz) to protect for
      that DPA.
    protected_points: A list of namedtuple (latitude, longitude) defining the actual
      points to protect within the DPA.
    threshold: The protection threshold (in dBm per 10MHz). The 95% quantile of the
      aggregated interference shall not exceed this level.
    radar_height: The radar height (meters).
    beamwidth: The radar antenna beamwidth (degrees).
    azimuth_range: The radar azimuth range (degrees) as a tuple of
      (min_azimuth, max_azimuth) relative to true north.
    catb_neighbor_dist: The CatB neighbording distance (km).
    dpa_type: The DPA category, either 'esc' or 'portal'.

    grants: The list of registered grants.
    move_lists: A list of move list (set of |CbsdGrantInfo|) per channel.
    nbor_lists: A list of neighbor list (set of |CbsdGrantInfo|) per channel.

  Note that keep list is the grants of the nbor_list not in the move list.

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
  num_iteration = 2000
  protection_zone = None

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

  @classmethod
  def ConfigureDefaultProtectionZone(cls):
    """Configure to use the default protection zone.

    Protection zone was initially specified for CatA neighborhood derivation
    but are now unused. Support is kept for legacy reason however.
    """
    cls.protection_zone = zones.GetCoastalProtectionZone()

  def __init__(self, protected_points,
               threshold=DPA_DEFAULT_THRESHOLD_PER_10MHZ,
               radar_height=50,
               beamwidth=3,
               azimuth_range=(0, 360),
               freq_ranges_mhz=[(3550, 3650)],
               catb_neighbor_dist=ml.CAT_B_NBRHD_DIST_DEFAULT,
               dpa_type='esc'):
    """Initialize the DPA attributes."""
    self.protected_points = protected_points
    self.threshold = threshold
    self.radar_height = radar_height
    self.azimuth_range = azimuth_range
    self.beamwidth = beamwidth
    self.catb_neighbor_dist = catb_neighbor_dist
    self.dpa_type = dpa_type
    self.channels = None
    self._grants = []
    self.has_th_grants = False
    self.ResetFreqRange(freq_ranges_mhz)
    self.ResetLists()

  def __str__(self):
    """Returns the DPA str."""
    return ('Dpa(protected_points=%r, threshold=%.1f, radar_height=%.1f,'
            'beamwidth=%.1f, azimuth_range=%r, channels=%r,'
            'catb_neighbor_dist=%.1f, dpa_type=%r)' % (
                self.protected_points, self.threshold, self.radar_height,
                self.beamwidth, self.azimuth_range, self.channels,
                self.catb_neighbor_dist, self.dpa_type))

  def ResetFreqRange(self, freq_ranges_mhz):
    """Reset the frequency ranges of the DPA.

    Args:
      freq_ranges_mhz: The protection frequencies (MHz) as a list of tuple
        (freq_min_mhz, freq_max_mhz) of the DPA protected frequency ranges.
    """
    channels = GetDpaProtectedChannels(freq_ranges_mhz,
                                       is_portal_dpa=(self.dpa_type=='portal'))
    if channels != self.channels:
      self.ResetLists()
    self.channels = channels

  def ResetLists(self):
    """Reset move list and keep list."""
    self.move_lists = []
    self.nbor_lists = []

  def _DetectIfPeerSas(self):
    """Returns True if holding grants from peer TH SAS."""
    for grant in self._grants:
      if not grant.is_managed_grant:
        return True
    return False

  def SetGrantsFromFad(self, sas_uut_fad, sas_th_fads):
    """Sets the list of grants.

    Args:
      sas_uut_fad: The FAD object of SAS UUT.
      sas_th_fads: A list of FAD objects of other SAS test harness.
    """
    # TODO(sbdt): optim = pre-filtering of grants in global DPA neighborhood.
    self._grants = data.getGrantObjectsFromFAD(sas_uut_fad, sas_th_fads)
    self.ResetLists()
    self.has_th_grants = self._DetectIfPeerSas()

  def SetGrantsFromList(self, grants):
    """Sets the list of grants from a list of |data.CbsdGrantInfo|."""
    # TODO(sbdt): optim = pre-filtering of grants in global DPA neighborhood.
    self._grants = grants
    self.ResetLists()
    self.has_th_grants = self._DetectIfPeerSas()

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
          grants=self._grants,
          exclusion_zone=Dpa.protection_zone,
          inc_ant_height=self.radar_height,
          num_iter=Dpa.num_iteration,
          threshold=self.threshold,
          beamwidth=self.beamwidth,
          min_azimuth=self.azimuth_range[0],
          max_azimuth=self.azimuth_range[1],
          catb_neighbor_dist=self.catb_neighbor_dist)

      move_list, nbor_list = zip(*pool.map(moveListConstraint,
                                           self.protected_points))
      # Combine the individual point move lists
      move_list = set().union(*move_list)
      nbor_list = set().union(*nbor_list)
      self.move_lists.append(move_list)
      self.nbor_lists.append(nbor_list)

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
    mask = np.zeros(len(self._grants), np.bool)
    for k, grant in enumerate(self._grants):
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
        min_azimuth=self.azimuth_range[0],
        max_azimuth=self.azimuth_range[1],
        catb_neighbor_dist=self.catb_neighbor_dist,
        do_max=True)

    pool = mpool.Pool()
    max_interf = pool.map(interfCalculator,
                          self.protected_points)
    return max_interf

  def CheckInterference(self, sas_uut_active_grants, margin_db,
                        channel=None, num_iter=None,
                        do_abs_check_single_uut=False):
    """Checks interference of keep list of SAS UUT vs test harness.

    This compares the aggregated interference (within some margin) generated by:
      - the test harness keep list, versus
      - the blended SAS UUT / Test harness keep list
    for all protection points and azimuth.

    Args:
      sas_uut_active_grants: An iterable of authorized |data.CbsdGrantInfo| grants.
        of the SAS UUT (ie not in the move list).
      margin_db: The margin (in dB) to use for the check.
      channel: A channel as tuple (low_freq_mhz, high_freq_mhz), or None for all channels
        of that Dpa.
      num_iter: The number of Monte Carlo iteration for calculating the aggregate
        interference. If None, use the global class level `num_iteration`.
      do_abs_check_single_uut: If True, performs check against absolute threshold instead
        of relative check against ref model, iff only SAS UUT present (no peer SAS).
    Returns:
      True if all SAS UUT aggregated interference are within margin, False otherwise
      (ie if at least one combined protection point / azimuth fails the test).
    """
    if channel is None:
      for chan in self.channels:
        if not self.CheckInterference(sas_uut_active_grants, margin_db, chan, num_iter,
                                      do_abs_check_single_uut):
          return False
      return True

    keep_list = self.GetKeepList(channel)
    nbor_list = self.GetNeighborList(channel)
    if num_iter is None:
      num_iter = Dpa.num_iteration
    # Find the keep list of TH and SAS UUT
    keep_list_th_other_sas = [
        grant for grant in self._grants
        if (not grant.is_managed_grant and
            grant in keep_list)]
    keep_list_th_managing_sas = [
        grant for grant in self._grants
        if (grant.is_managed_grant and
            grant in keep_list)]
    keep_list_uut_managing_sas = [
        grant for grant in sas_uut_active_grants
        if (grant in nbor_list and
            grant not in keep_list_th_other_sas)]
    # Do absolute threshold in some case
    hard_threshold = None
    if do_abs_check_single_uut and not self.has_th_grants:
      hard_threshold = self.threshold

    checkPointInterf = functools.partial(
        _CalcTestPointInterfDiff,
        channel=channel,
        keep_list_th_other_sas=keep_list_th_other_sas,
        keep_list_th_managing_sas=keep_list_th_managing_sas,
        keep_list_uut_managing_sas=keep_list_uut_managing_sas,
        radar_height=self.radar_height,
        beamwidth=self.beamwidth,
        protection_zone=Dpa.protection_zone,
        num_iter=num_iter,
        azimuth_range=self.azimuth_range,
        catb_neighbor_dist=self.catb_neighbor_dist,
        threshold=hard_threshold
    )
    # TODO(sbdt): could do early stop as soon as one fails, although I would expect
    # the criteria to be changed into checking 99.x% of success instead of 100%.
    pool = mpool.Pool()
    result = pool.map(checkPointInterf, self.protected_points)
    max_diff_interf = max(result)
    return max_diff_interf <= margin_db


def GetDpaProtectedChannels(freq_ranges_mhz, is_portal_dpa=False):
  """ Gets protected channels list for DPA.

  Note: For ESC-monitored DPA, only the highest channel below 3550MHz is
  kept.

  Args:
    freq_ranges_mhz: The protection frequencies (MHz) as a list of tuple
      (freq_min_mhz, freq_max_mhz) of the DPA protected frequency ranges.
    is_portal_dpa: True if a portal DPA, False if Coastal ESC DPA.

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
  channels = sorted(list(channels))
  if not is_portal_dpa:
    # For ESC DPA, channels below 3550 are always ON, and only the highest one dominates.
    idx_above_3550 = 0
    for chan in channels:
      if chan[0] >= 3550:
        break
      idx_above_3550 +=1
    highest_channel_idx_below_3550 = max(0, idx_above_3550 - 1)
    channels = channels[highest_channel_idx_below_3550:]

  return channels


def _CalcTestPointInterfDiff(point,
                             channel,
                             keep_list_th_other_sas,
                             keep_list_th_managing_sas,
                             keep_list_uut_managing_sas,
                             radar_height,
                             beamwidth,
                             protection_zone,
                             num_iter,
                             azimuth_range,
                             catb_neighbor_dist,
                             threshold=None):
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
    protection_zone: An optional |shapely.Polygon/MultiPolygon| defining the CatA
      protection zone.
    num_iteration: The number of iteration to use in the Monte Carlo simulation.
    azimuth_range: The radar azimuth range (degrees) as a tuple of
      (min_azimuth, max_azimuth) relative to true north.
    catb_neighbor_dist: The CatB neighbor distance (km).
    threshold: If set, do an absolute threshold check of SAS UUT interference against
      threshold. Otherwise compare against the reference model aggregated interference.

  Returns:
    The maximum aggregated difference across all the radar pointing directions between
    the blended and the reference models.
  """
  # Perform caching of the per device interference, as to reduce the Monte-Carlo
  # variability on similar CBSD in keep list.
  # TODO(sbdt): check if better to context manage once per process, with clearing
  # in between.
  with ml.InterferenceCacheManager() as cm:
    uut_interferences = ml.calcAggregatedInterference(
        point,
        low_freq=channel[0] * 1e6,
        high_freq=channel[1] * 1e6,
        grants=keep_list_th_other_sas + keep_list_uut_managing_sas,
        exclusion_zone=protection_zone,
        inc_ant_height=radar_height,
        num_iter=num_iter,
        beamwidth=beamwidth,
        min_azimuth=azimuth_range[0],
        max_azimuth=azimuth_range[1],
        catb_neighbor_dist=catb_neighbor_dist)
    if threshold is not None:
      return np.max(uut_interferences - threshold)
    th_interferences = ml.calcAggregatedInterference(
        point,
        low_freq=channel[0] * 1e6,
        high_freq=channel[1] * 1e6,
        grants=keep_list_th_other_sas + keep_list_th_managing_sas,
        exclusion_zone=protection_zone,
        inc_ant_height=radar_height,
        num_iter=num_iter,
        beamwidth=beamwidth,
        min_azimuth=azimuth_range[0],
        max_azimuth=azimuth_range[1],
        catb_neighbor_dist=catb_neighbor_dist)
    return np.max(uut_interferences - th_interferences)


# DPA builder routines
ProtectionPoint = namedtuple('ProtectionPoint',
                             ['latitude', 'longitude'])


def _DefaultProtectionPoints(dpa_geometry,
                             num_pts_front_border=25,
                             num_pts_back_border=10,
                             num_pts_front_zone=10,
                             num_pts_back_zone=5,
                             front_us_border_buffer_km=40):
  """Returns a default list of DPA protection points.

  This creates a default set of points by regular sampling of the contour and gridding
  the interior of the DPA zone. The contour and zone are separated in front and back,
  using the US border (with a buffer) as the delimitation.
  If the DPA is a Point, a single point is returned however.

  Args:
    dpa_geometry: The DPA geometry as a |shapely.Polygon or Point|.
    num_pts_front_border: Number of points in the front border.
    num_pts_back_border: Number of points in the back border.
    num_pts_front_zone: Number of points in the front zone.
    num_pts_back_zone: Number of points in the back zone.
    front_us_border_buffer_km: Buffering of US border for delimiting front/back.
  """
  # Case of DPA points
  if isinstance(dpa_geometry, sgeo.Point):
    return [ProtectionPoint(longitude=dpa_geometry.x, latitude=dpa_geometry.y)]

  # Case of Polygon
  us_border = zones.GetUsBorder()
  us_border_ext = us_border.buffer(front_us_border_buffer_km / 111.)
  front_border = dpa_geometry.exterior.intersection(us_border_ext)
  back_border = dpa_geometry.exterior.difference(us_border_ext)
  front_zone = dpa_geometry.intersection(us_border_ext)
  back_zone = dpa_geometry.difference(us_border_ext)

  step_front_dpa_arcsec = np.sqrt(front_zone.area / num_pts_front_zone) * 3600.
  step_back_dpa_arcsec = np.sqrt(back_zone.area / num_pts_back_zone) * 3600.
  def SampleLine(line, num_points):
    step = line.length / (num_points-1)
    return [line.interpolate(dist) for dist in np.arange(0, line.length, step)]

  front_border_pts = [] if not front_border else [
      ProtectionPoint(longitude=pt.x, latitude=pt.y)
      for pt in SampleLine(front_border, num_pts_front_border)]
  back_border_pts = [] if not back_border else [
      ProtectionPoint(longitude=pt.x, latitude=pt.y)
      for pt in SampleLine(back_border, num_pts_back_border)]
  front_zone_pts = [] if not front_zone else [
      ProtectionPoint(longitude=pt[0], latitude=pt[1])
      for pt in utils.GridPolygon(front_zone, step_front_dpa_arcsec)]
  back_zone_pts = [] if not back_zone else [
      ProtectionPoint(longitude=pt[0], latitude=pt[1])
      for pt in utils.GridPolygon(back_zone, step_back_dpa_arcsec)]
  return front_border_pts + front_zone_pts + back_border_pts + back_zone_pts


def BuildDpa(dpa_name, protection_points_method=None):
  """Builds a DPA parameterized correctly.

  The DPA special parameters are obtained from the DPA database.
  The DPA protection points are generated either from a file, or using a provided default
  method.

  Args:
    dpa_name: The DPA official name.
    protection_points_method: Two methods are supported for getting the protection points:
      + a path pointing to the file holding the protected points location defined as a
        geojson MultiPoint or Point geometry. The path can be either absolute or relative
        to the running script (normally the `harness/` directory).
      + 'default <parameters>': a simple default method. Parameters is a tuple defining
        the number of points to use for different part of the DPA:
          num_pts_front_border: number of points in the front border
          num_pts_back_border: number of points in the back border
          num_pts_front_zone: number of points in the front zone
          num_pts_back_zone: number of points in the back zone
          front_us_border_buffer_km: buffering of US border for delimiting front/back.
        Example of encoding:
          'default (200,50,20,5)'
          Note the default values are (25, 10, 10, 5, 40). Only the passed parameters will
          be redefined.
  Returns:
    A Dpa object.
  Raises:
    IOError: if the provided file cannot be found.
    ValueError: if the provided file is not a valid GeoJSON MultiPoint geometry.
  """
  try:
    dpa_zone = zones.GetCoastalDpaZones()[dpa_name]
    dpa_type = 'esc'
  except KeyError:
    try:
      dpa_zone = zones.GetPortalDpaZones()[dpa_name]
      dpa_type = 'portal'
    except KeyError:
      raise ValueError('DPA %s not found in DPA database' % dpa_name)

  if not protection_points_method:
    protection_points = _DefaultProtectionPoints(dpa_zone.geometry)
  elif protection_points_method.strip().lower().startswith('default'):
    # extract optional parameters
    params = protection_points_method.strip().lower()[len('default'):].strip()
    params = ast.literal_eval(params)
    protection_points = _DefaultProtectionPoints(dpa_zone.geometry, *params)
  else:
    protection_points_file = protection_points_method
    if not os.path.isfile(protection_points_file):
      raise IOError('Protected point definition file for DPA `%s` not found at location: '
                    '%s' % protection_points_file)
    with open(protection_points_file, 'r') as fd:
      mpoints = utils.ToShapely(json.load(fd))
    if isinstance(mpoints, sgeo.Point):
      mpoints = sgeo.MultiPoint([mpoints])
    if not isinstance(mpoints, sgeo.MultiPoint):
      raise ValueError('Protected point definition file for DPA `%s` not a valid MultiPoint'
                       ' geoJSON file.')
    protection_points = [ProtectionPoint(longitude=pt.x, latitude=pt.y)
                         for pt in mpoints]
    # Check validity of points
    if isinstance(dpa_zone, sgeo.Point):
      if len(protection_points) != 1:
        raise ValueError('Multiple protection points for single point DPA %s.' % dpa_name)
      pt = sgeo.Point(protection_points[0].longitude, protection_points[0].latitude)
      if not pt.within(dpa_zone.buffer(0.0005)):
        raise ValueError('Point for single point DPA %s is outside zone: %.5f %.5f'
                         % (dpa_name, pt.x, pt.y))
    else:
      mpoint = sgeo.MultiPoint([(pt.longitude, pt.latitude) for pt in protection_points])
      mpoint_inside = dpa_zone.buffer(0.0005).intersection(mpoint)
      if len(mpoint) != len(mpoint_inside):
        raise ValueError('Some points for DPA %s are outside zone.' % dpa_name)

  if not protection_points:
    raise ValueError('No valid points generated for DPA %s.' % dpa_name)
  # Set all DPA operational parameters
  protection_threshold = dpa_zone.protectionCritDbmPer10MHz
  radar_height = dpa_zone.refHeightMeters
  radar_beamwidth = dpa_zone.antennaBeamwidthDeg
  azimuth_range = (dpa_zone.minAzimuthDeg, dpa_zone.maxAzimuthDeg)
  freq_ranges_mhz = dpa_zone.freqRangeMhz
  catb_neighbor_dist = dpa_zone.catbNeighborDist
  return Dpa(protection_points,
             threshold=protection_threshold,
             radar_height=radar_height,
             beamwidth=radar_beamwidth,
             azimuth_range=azimuth_range,
             freq_ranges_mhz=freq_ranges_mhz,
             catb_neighbor_dist=catb_neighbor_dist,
             dpa_type=dpa_type)
