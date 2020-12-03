# This software was developed by employees of the National Institute
# of Standards and Technology (NIST), an agency of the Federal
# Government. Pursuant to title 17 United States Code Section 105, works
# of NIST employees are not subject to copyright protection in the United
# States and are considered to be in the public domain. Permission to freely
# use, copy, modify, and distribute this software and its documentation
# without fee is hereby granted, provided that this notice and disclaimer
# of warranty appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
# WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
# ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
# BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
# ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS
# SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR
# OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY
# OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT
# OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#
# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with
# the code in compliance with the conditions of those licenses.

#==================================================================================
# DPA Move List Reference Model.
# Based on WINNF-TS-0112, Version V1.4.1, 16 January 2018.
#
# The main routines are:
#   - 'moveListConstraint()': calculates the move list for one point
#   - 'calcAggregatedInterference()': calculates the 95% quantile interference for one point
#==================================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import namedtuple, defaultdict
from enum import Enum
import functools
from functools import partial
import logging

import numpy as np
import shapely.geometry as sgeo
from shapely.geometry import MultiPolygon as MPolygon
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
import six
from six.moves import range
from six.moves import zip

from reference_models.antenna import antenna
from reference_models.common import cache
from reference_models.common import data
from reference_models.common import data
from reference_models.common import mpool
from reference_models.geo import drive
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm

# Import WINNF reference models including propagation, geo, and CBSD antenna gain models

# Constant parameters based on requirements in the WINNF-TS-0112 [R2-SGN-24]
# Monte Carlo percentile for protection
PROTECTION_PERCENTILE = 95

# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0

# Frequency range of co-channel DPAs (Hz)
LOW_FREQ_COCH = 3550e6
HIGH_FREQ_COCH = 3700e6

# Out-of-band maximum conducted power (dBm/MHz) (FCC Part 96 Rules (96.41))
OOB_POWER_WITHIN_10MHZ = -13
OOB_POWER_OUTSIDE_10MHZ = -25
OOB_POWER_BELOW_3530MHZ = -40


# Define interference contribution, i.e., a tuple with named fields of
# 'randomInterference', 'bearing_c_cbsd'
InterferenceContribution = namedtuple('InterferenceContribution',
                                      ['randomInterference', 'bearing_c_cbsd'])


# Define an enumeration class named DpaType with members
# 'CO_CHANNEL', 'OUT_OF_BAND'
class DpaType(Enum):
  CO_CHANNEL = 1
  OUT_OF_BAND = 2


def findDpaType(low_freq, high_freq):
  """Finds the DPA protection type for a given frequency range.

  Args:
    low_freq: The minimum frequency (Hz).
    high_freq: The maximum frequency (Hz).

  Returns:
    DpaType.CO_CHANNEL or DpaType.OUT_OF_BAND
  """
  if low_freq >= LOW_FREQ_COCH and high_freq <= HIGH_FREQ_COCH:
    return DpaType.CO_CHANNEL
  elif high_freq <= LOW_FREQ_COCH:
    return DpaType.OUT_OF_BAND
  raise ValueError('Invalid DPA frequency range')


def filterGrantsForFreqRange(grants, low_freq, high_freq):
  """Returns a list of all grants affecting a protected frequency range.

  Args:
    grants: A list of |data.CbsdGrantInfo| grants.
    low_freq: The minimum frequency (Hz).
    high_freq: The maximum frequency (Hz).
  """
  chan_type = findDpaType(low_freq, high_freq)
  if chan_type == DpaType.OUT_OF_BAND:
    # All grants affect COCHANNEL, including those higher than 3650MHz.
    return grants
  return [g for g in grants
          if (min(g.high_frequency, high_freq) - max(g.low_frequency, low_freq)) > 0]


def findGrantsInsideNeighborhood(grants, constraint,
                                 dpa_type,
                                 neighbor_distances):
  """Identify the CBSD grants in the neighborhood of protection constraint.

  Inputs:
    grants:         a list of CBSD |data.CbsdGrantInfo| grants.
    constraint:     protection constraint of type |data.ProtectionConstraint|
    dpa_type:       an enum member of class DpaType
    neighbor_distances: the neighborhood distances (Km) as a sequence:
      [cata_dist, catb_dist, cata_oob_dist, catb_oob_dist]

  Returns:
    A tuple of:
      grants_inside:  a list of |data.CbsdGrantInfo| grants, being inside the
                      neighborhood of that protection `constraint`.
      idxs_inside:    the indices of `grants_inside` in original `grant` list.
  """
  # Initialize an empty list
  grants_inside = []
  idxs_inside = []

  neighbor_dists = neighbor_distances[0:2]
  if dpa_type is DpaType.OUT_OF_BAND:
    neighbor_dists = neighbor_distances[2:]

  # Loop over each CBSD grant and filter the ones inside the neighborhood
  for k, grant in enumerate(grants):
    # Check frequency range
    if dpa_type is not DpaType.OUT_OF_BAND:
      overlapping_bw = (min(grant.high_frequency, constraint.high_frequency)
                        - max(grant.low_frequency, constraint.low_frequency))
      if overlapping_bw <= 0:
        continue

    # Compute distance from CBSD location to protection constraint location
    dist_km, _, _ = vincenty.GeodesicDistanceBearing(
        grant.latitude, grant.longitude,
        constraint.latitude, constraint.longitude)

    # Check if CBSD is inside the neighborhood of protection constraint
    if dist_km > neighbor_dists[grant.cbsd_category == 'B']:
      continue

    grants_inside.append(grant)
    idxs_inside.append(k)

  return grants_inside, idxs_inside


def ComputeOOBConductedPower(low_freq_cbsd, low_freq_c, high_freq_c):
  """Compute maximum conducted power of a CBSD grant to an out-of-band
  protection constraint based on FCC Part 96 Rules (96.41)

  Inputs:
    low_freq_cbsd:  low frequency of CBSD grant channel (Hz)
    low_freq_c:     low frequency of protection constraint (Hz)
    high_freq_c:    high frequency of protection constraint (Hz)

  Returns:
    Maximum out-of-band conducted power (dBm)
  """
  # Compute overlapping bandwidths
  overlap_bw_within_10MHz = (min(low_freq_cbsd, high_freq_c) -
                             max(low_freq_cbsd-10.e6, low_freq_c))
  overlap_bw_outside_10MHz = (min(low_freq_cbsd-10.e6, high_freq_c) -
                              max(3530.e6, low_freq_c))
  overlap_bw_below_3530MHz = min(3530.e6, high_freq_c) - low_freq_c

  # Compute total conducted power
  power_within_10MHz_mW = 0
  power_outside_10MHz_mW = 0
  power_below_3530MHz_mW = 0
  if overlap_bw_within_10MHz > 0:
    power_within_10MHz_mW = (10 ** (OOB_POWER_WITHIN_10MHZ / 10.)
                             * overlap_bw_within_10MHz / 1.e6)

  if overlap_bw_outside_10MHz > 0:
    power_outside_10MHz_mW = (10 ** (OOB_POWER_OUTSIDE_10MHZ / 10.)
                              * overlap_bw_outside_10MHz / 1.e6)

  if overlap_bw_below_3530MHz > 0:
    power_below_3530MHz_mW = (10 ** (OOB_POWER_BELOW_3530MHZ / 10.)
                              * overlap_bw_below_3530MHz / 1.e6)

  power_mW = power_within_10MHz_mW + power_outside_10MHz_mW + power_below_3530MHz_mW
  return 10 * np.log10(power_mW)


def computeInterference(grant, constraint, inc_ant_height, num_iteration, dpa_type):
  """Calculate interference contribution of each grant in the neighborhood to
  the protection constraint c.

  Inputs:
    cbsd_grant:     a |data.CbsdGrantInfo| grant
    constraint:     protection constraint of type |data.ProtectionConstraint|
    inc_ant_height: reference incumbent antenna height (in meters)
    num_iteration:  a number of Monte Carlo iterations
    dpa_type:       an enum member of class DpaType

  Returns:
    A tuple of
      interference: 	interference contribution, a tuple with named fields
         'randomInterference' (K random interference contributions
         of the grant to protection constraint c), and 'bearing_c_cbsd'
         (bearing from c to CBSD grant location).
      medianInterference: the median interference.
  """
  # Get frequency information
  low_freq_cbsd = grant.low_frequency
  high_freq_cbsd = grant.high_frequency
  low_freq_c = constraint.low_frequency
  high_freq_c = constraint.high_frequency

  # Compute median and K random realizations of path loss/interference contribution
  # based on ITM model as defined in [R2-SGN-03] (in dB)
  reliabilities = np.random.uniform(0.001, 0.999, num_iteration)  # get K random
  # reliability values from an uniform distribution over [0.001,0.999)
  reliabilities = np.append(reliabilities, [0.5])  # add 0.5 (for median loss) as
  # a last value to reliabilities array
  results = wf_itm.CalcItmPropagationLoss(
      grant.latitude, grant.longitude, grant.height_agl,
      constraint.latitude, constraint.longitude, inc_ant_height,
      grant.indoor_deployment,
      reliability=reliabilities,
      freq_mhz=FREQ_PROP_MODEL)
  path_loss = np.array(results.db_loss)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(
      results.incidence_angles.hor_cbsd,
      grant.antenna_azimuth, grant.antenna_beamwidth, grant.antenna_gain)

  # Compute EIRP of CBSD grant inside the frequency range of protection constraint
  if dpa_type is not DpaType.OUT_OF_BAND: # For co-channel offshore/inland DPAs

    # CBSD co-channel bandwidth overlapping with
    # frequency range of protection constraint
    co_channel_bw = min(high_freq_cbsd, high_freq_c) - max(low_freq_cbsd, low_freq_c)

    # Compute EIRP within co-channel bandwidth
    eirp_cbsd = ((grant.max_eirp - grant.antenna_gain) + ant_gain
                 + 10 * np.log10(co_channel_bw / 1.e6))

  else:   # For out-of-band inland DPAs

    # Compute out-of-band conducted power
    oob_power = ComputeOOBConductedPower(low_freq_cbsd, low_freq_c, high_freq_c)
    # Compute out-of-band EIRP
    eirp_cbsd = oob_power + ant_gain

  # Calculate the interference contributions
  interf = eirp_cbsd - path_loss
  median_interf = interf[-1]      # last element is the median interference
  K_interf = interf[:-1]          # first 'K' interference

  # Store interference contributions
  interference = InterferenceContribution(randomInterference=K_interf,
                                          bearing_c_cbsd=results.incidence_angles.hor_rx)
  return interference, median_interf


def formInterferenceMatrix(grants, grants_ids, constraint,
                           inc_ant_height, num_iter, dpa_type):
  """Form the matrix of interference contributions to protection constraint c.

  Inputs:
    grants:             a list of |data.CbsdGrantInfo| grants of all CBSDs inside the
                        neighborhood of the protection constraint.
    grants_ids:         the list of grants ids corresponding to `grants` list.
    constraint:         protection constraint of type |data.ProtectionConstraint|
    inc_ant_height:     reference incumbent antenna height (in meters)
    num_iter:           number of random iterations
    dpa_type:           an enum member of class DpaType

  Returns:
    A tuple of:
      I:                  a matrix of interference contributions to protection
                          constraint (c) with dimensions (num_iter . len(grants))
      sorted_grant_ids:   the list of IDs of the sorted grant list
      sorted_bearings:    a list of bearings from protection point to CBSDs of the
                          sorted grant list
  """
  # Compute interference contributions of each grant to the protection constraint
  interf_list = []
  median_interf = []
  for cbsd_grant in grants:
    interf, median = computeInterference(cbsd_grant, constraint, inc_ant_height,
                                         num_iter, dpa_type)
    interf_list.append(interf)
    median_interf.append(median)
  # Sort grants by their median interference contribution, smallest to largest
  sorted_idxs = sorted(
      list(range(len(median_interf))), key=median_interf.__getitem__)
  I = np.array([interf_list[k].randomInterference for k in sorted_idxs]).transpose()
  sorted_bearings = np.array([interf_list[k].bearing_c_cbsd for k in sorted_idxs])
  sorted_grant_ids = [grants_ids[k] for k in sorted_idxs]
  return I, sorted_grant_ids, sorted_bearings


def findAzimuthRange(min_azimuth, max_azimuth, beamwidth):
  """Returns the azimuth range for a given radar antenna 'beamwidth'."""
  if beamwidth == 360:
    azimuths = [0]
  else:
    if max_azimuth < min_azimuth:
      max_azimuth += 360
    azimuths = np.arange(min_azimuth, max_azimuth+beamwidth/2., beamwidth/2.0)
    if azimuths[-1] > max_azimuth: azimuths[-1] = max_azimuth
    if azimuths[-1] % 360. == azimuths[0]: azimuths = azimuths[:-1]
    azimuths[azimuths>=360] -= 360
  return azimuths


def find_nc(I, bearings, t, beamwidth, min_azimuth, max_azimuth):
  """Returns the index (nc) of the grant in the ordered list of grants such that
  the protection percentile of the interference from the first nc grants is below the
  threshold for all azimuths of the receiver antenna.

  Inputs:
    I:      2D array of interference contributions (dBm/10 MHz); columns
            correspond to grants, and rows correspond to Monte Carlo iterations.
    bearings: a list of bearings from protection point to CBSDs.
    t:      protection percentile threshold (dBm/10 MHz)
    beamwidth: protection antenna beamwidth (degree).
    min_azimuth: minimim protection azimuth (degree).
    max_azimuth: maximum protection azimuth (degree).

  Returns:
    nc:     index nc that defines the move list to be {G_nc+1, G_nc+2, ..., G_Nc}
  """
  # Create array of incumbent antenna azimuth angles (degrees).
  azimuths = findAzimuthRange(min_azimuth, max_azimuth, beamwidth)

  # Initialize nc to Nc.
  Nc = I.shape[1]
  nc = Nc

  # Convert protection threshold and interference matrix to linear units.
  t_mW = np.power(10.0, t/10.0)
  I_mW = np.power(10.0, I/10.0)

  # Loop through every azimuth angle.
  for azi in azimuths:

    # Calculate interference contributions at output of receiver antenna.
    dpa_gains = antenna.GetRadarNormalizedAntennaGains(bearings, azi, beamwidth)
    IG = I_mW * 10**(dpa_gains/10.0)

    # Compute the protection percentile of the aggregate interference, and remove
    # grants until the protection threshold is met or all grants are moved.
    agg_interf = np.percentile(np.sum(IG[:, 0:nc], axis=1),
                               PROTECTION_PERCENTILE, interpolation='lower')
    if agg_interf <= t_mW:
      continue

    # Conduct binary search for nc.
    hi = nc
    lo = 0
    while (hi - lo) > 1:
      mid = (hi + lo) // 2
      agg_interf = np.percentile(np.sum(IG[:, 0:mid], axis=1),
                                 PROTECTION_PERCENTILE, interpolation='lower')
      if agg_interf > t_mW:
        hi = mid
      else:
        lo = mid

    nc = lo
    if nc == 0:
      return 0

  return nc


def _addMinFreqGrantToFront(l, grant):
  """Add the min freq `grant` to the front of list `l`."""
  l.append(grant)
  if l[-1].low_frequency < l[0].low_frequency:
    l[0], l[-1] = l[-1], l[0]

#------------------------------------------
# Public interface below
def moveListConstraint(protection_point, low_freq, high_freq,
                       grants,
                       inc_ant_height,
                       num_iter, threshold, beamwidth,
                       neighbor_distances,
                       min_azimuth=0, max_azimuth=360):
  """Returns the move list for a given protection constraint.

  Note that the returned indexes corresponds to the grant.grant_index

  Inputs:
    protection_point:  A protection point location, having attributes
                      'latitude' and 'longitude'.
    low_freq:          The low frequency of protection constraint (Hz).
    high_freq:         The high frequency of protection constraint (Hz).
    grants:            A list of CBSD |data.CbsdGrantInfo| grants.
    inc_ant_height:    The reference incumbent antenna height (meters).
    num_iter:          The number of Monte Carlo iterations.
    threshold:         The protection threshold (dBm/10 MHz).
    beamwidth:         The protection antenna beamwidth (degree).
    neighbor_distances: The neighborhood distances (km) as a sequence:
      [cata_dist, catb_dist, cata_oob_dist, catb_oob_dist]
    min_azimuth:       The minimum azimuth (degrees) for incumbent transmission.
    max_azimuth:       The maximum azimuth (degrees) for incumbent transmission.

  Returns:
    A tuple of (move_list_grants, neighbor_list_grants) for that protection constraint:
      + the grants on the move list.
      + the grants in the neighborhood list.
  """
  logging.debug('DPA Create move list for point (%s), freq (%s, %s), threshold (%s), neighborhood distance (%r)',
               protection_point, low_freq, high_freq, threshold, neighbor_distances)
  if not grants:
    return [], []

  dpa_type = findDpaType(low_freq, high_freq)
  if not beamwidth: beamwidth = 360

  # Assign values to the protection constraint
  constraint = data.ProtectionConstraint(latitude=protection_point.latitude,
                                         longitude=protection_point.longitude,
                                         low_frequency=low_freq,
                                         high_frequency=high_freq,
                                         entity_type=data.ProtectedEntityType.DPA)

  # DPA Purge algorithm for OOB
  if dpa_type is DpaType.OUT_OF_BAND:
    cbsds_grants_map = defaultdict(list)
    for grant in grants:
      key = grant.uniqueCbsdKey()
      _addMinFreqGrantToFront(cbsds_grants_map[key], grant)
    # Reset the grants to the minimum frequency grant for each CBSDs.
    grants = [cbsd_grants[0] for cbsd_grants in six.itervalues(cbsds_grants_map)]

  # Identify CBSD grants in the neighborhood of the protection constraint
  neighbor_grants, neighbor_idxs = findGrantsInsideNeighborhood(
      grants, constraint, dpa_type, neighbor_distances)

  movelist_grants = []
  if len(neighbor_grants):  # Found CBSDs in the neighborhood
    # Form the matrix of interference contributions
    I, sorted_neighbor_idxs, bearings = formInterferenceMatrix(
        neighbor_grants, neighbor_idxs, constraint, inc_ant_height, num_iter, dpa_type)

    # Find the index (nc) of the grant in the ordered list of grants such that
    # the protection percentile of the interference from the first nc grants is below
    # the threshold for all azimuths of the receiver antenna.
    nc = find_nc(I, bearings, threshold, beamwidth, min_azimuth, max_azimuth)

    # Determine the associated move list (Mc)
    movelist_grants = [grants[k] for k in sorted_neighbor_idxs[nc:]]

    # DPA Purge Algorithm for OOB - reintegrated in move list
    if dpa_type is DpaType.OUT_OF_BAND:
      # Add back all purged list with state of main one
      extra_grants = []
      for grant in movelist_grants:
        cbsd_extra_grants = cbsds_grants_map[grant.uniqueCbsdKey()][1:]
        if cbsd_extra_grants:
          extra_grants.extend(cbsd_extra_grants)

      movelist_grants.extend(extra_grants)
      # Note: the following update on neighbor list is optional, the whole
      # code would run the same if we were including only the main grant in
      # the neighbor list. But for sake of consistency, we keep them.
      extra_grants = []
      for grant in neighbor_grants:
        cbsd_extra_grants = cbsds_grants_map[grant.uniqueCbsdKey()][1:]
        if cbsd_extra_grants:
          extra_grants.extend(cbsd_extra_grants)

      neighbor_grants.extend(extra_grants)

  logging.debug('DPA Returning movelist_grants=(%s), neighbor_grants=(%s)',
               movelist_grants, neighbor_grants)
  return (movelist_grants, neighbor_grants)


def getDpaNeighborGrants(grants, protection_points, dpa_geometry,
                         low_freq, high_freq, neighbor_distances):
  """Gets the list of actual neighbor grants of a DPA, for a given channel.

  This looks at the total keep list considering a bunch of protected points.

  Args:
    grants:  A list of CBSD |data.CbsdGrantInfo| active grants.
    protection_points: A list of protection point locations defining the DPA, each one
      having attributes 'latitude' and 'longitude'.
    dpa_geometry: The DPA |shapely.geometry| for detection of inside grants.
    low_freq: The low frequency of protection constraint (Hz).
    high_freq: The high frequency of protection constraint (Hz).
    neighbor_distances: The neighborhood distances (km) as a sequence:
      [cata_dist, catb_dist, cata_oob_dist, catb_oob_dist]

  Returns:
    A set of |CbsdGrantInfo| neighbor grants.
  """
  dpa_type = findDpaType(low_freq, high_freq)

  neighbor_grants = set()
  if dpa_geometry and not isinstance(dpa_geometry, sgeo.Point):
    inside_grants = set(g for g in grants
                        if sgeo.Point(g.longitude, g.latitude).intersects(dpa_geometry))
    neighbor_grants = set(filterGrantsForFreqRange(inside_grants, low_freq, high_freq))

  for point in protection_points:
    # Assign values to the protection constraint
    constraint = data.ProtectionConstraint(latitude=point.latitude,
                                           longitude=point.longitude,
                                           low_frequency=low_freq,
                                           high_frequency=high_freq,
                                           entity_type=data.ProtectedEntityType.DPA)

    # Identify CBSD grants in the neighborhood of the protection constraint
    nbors, _ = findGrantsInsideNeighborhood(grants, constraint,
                                                  dpa_type,
                                                  neighbor_distances)
    neighbor_grants.update(nbors)

  return neighbor_grants


def calcAggregatedInterference(protection_point,
                               low_freq, high_freq,
                               grants,
                               inc_ant_height,
                               num_iter,
                               beamwidth,
                               neighbor_distances,
                               min_azimuth=0,
                               max_azimuth=360,
                               do_max=False):
  """Computes the 95% aggregated interference quantile on a protected point.

  Inputs:
    protection_point:  A protection point location, having attributes 'latitude' and
                       'longitude'.
    low_freq:          The low frequency of protection constraint (Hz).
    high_freq:         The high frequency of protection constraint (Hz).
    grants:            A list of CBSD |data.CbsdGrantInfo| active grants.
    inc_ant_height:    The reference incumbent antenna height (meters).
    num_iter:          The number of Monte Carlo iterations.
    beamwidth:         The protection antenna beamwidth (degree).
    min_azimuth:       The minimum azimuth (degrees) for incumbent transmission.
    max_azimuth:       The maximum azimuth (degrees) for incumbent transmission.
    neighbor_distances: The neighborhood distances (km) as a sequence:
      [cata_dist, catb_dist, cata_oob_dist, catb_oob_dist]
    do_max:            If True, returns the maximum interference over all radar azimuth.

  Returns:
    The 95% aggregated interference (dB) either:
      - as a vector (ndarray) of length N, where the element k corresponds to
          azimuth k * (beamwith/2). The length N is thus equal to 2 * 360 / beamwith,
          (or 2 * azimuth_range / beamwidth if using a smaller azimuth range than
           360 degrees, as specified by min_azimuth/max_azimuth).
      - or the maximum over all radar azimuth, if `do_max` is set to True.
  """
  dpa_type = findDpaType(low_freq, high_freq)
  if not beamwidth: beamwidth = 360

  # Assign values to the protection constraint
  constraint = data.ProtectionConstraint(latitude=protection_point.latitude,
                                         longitude=protection_point.longitude,
                                         low_frequency=low_freq,
                                         high_frequency=high_freq,
                                         entity_type=data.ProtectedEntityType.DPA)

  # DPA Purge algorithm for OOB
  if dpa_type is DpaType.OUT_OF_BAND:
    cbsds_grants_map = defaultdict(list)
    for grant in grants:
      key = grant.uniqueCbsdKey()
      _addMinFreqGrantToFront(cbsds_grants_map[key], grant)
    # Reset the grants to the minimum frequency grant for each CBSDs.
    grants = [cbsd_grants[0] for cbsd_grants in six.itervalues(cbsds_grants_map)]

  # Identify CBSD grants in the neighborhood of the protection constraint
  neighbor_grants, _ = findGrantsInsideNeighborhood(grants, constraint,
                                                    dpa_type,
                                                    neighbor_distances)
  if not neighbor_grants:
    return np.asarray(-1000)
  interf_matrix = np.zeros((num_iter, len(neighbor_grants)))
  bearings = np.zeros(len(neighbor_grants))
  for k, grant in enumerate(neighbor_grants):
    interf, _ = computeInterference(grant, constraint, inc_ant_height,
                                    num_iter, dpa_type)
    interf_matrix[:,k] = interf.randomInterference
    bearings[k] = interf.bearing_c_cbsd

  interf_matrix = 10**(interf_matrix / 10.)
  azimuths = findAzimuthRange(min_azimuth, max_azimuth, beamwidth)

  agg_interf = np.zeros(len(azimuths))
  for k, azi in enumerate(azimuths):
    dpa_gains = antenna.GetRadarNormalizedAntennaGains(bearings, azi, beamwidth)
    dpa_interf = interf_matrix * 10**(dpa_gains / 10.0)
    agg_interf[k] = np.percentile(np.sum(dpa_interf, axis=1),
                                  PROTECTION_PERCENTILE, interpolation='lower')
  agg_interf = 10 * np.log10(agg_interf)
  return np.max(agg_interf) if do_max else agg_interf


class InterferenceCacheManager(cache.CacheManager):
  """Interference cache context manager.

  By running the DPA routines within this context manager, pathloss
  calculation are cached per CBSD. Note that subsequent calls (with exact set
  of parameters) will reuse the same reliability random samples.

  Usage:
    with InterferenceCacheManager() as cm:
      # perform calculations
      interfs = calcAggregatedInterference(...)
      ...
  """
  def __init__(self, maxsize=None):
    """Initialize the cache context manager.

    Args:
      maxsize (int): The maximum cache size (managed in LRU fashion).
        If None, unlimited size.
    """
    cache.CacheManager.__init__(self, computeInterference, maxsize)


#----------------------------------
# Legacy routine, just to support existing client code using old interface.
def findMoveList(protection_specs, protection_points, registration_requests,
                 grant_requests, num_iter, num_processes,
                 pool=None):
  """Main routine to find CBSD indices on the move list.

  Inputs:
    protection_specs:   protection specifications, an object with attributes
                        'lowFreq' (in Hz), 'highFreq' (in Hz),
                        'antHeight' (in meters), 'beamwidth' (in degrees),
                        'threshold' (in dBm/10MHz), 'neighbor_distances' (km),
                        'min_azimuth', 'max_azimuth' (degrees)
                        where `neighbor_distances` are the neighborhood
                        distances (km) as a sequence:
                          [cata_dist, catb_dist, cata_oob_dist, catb_oob_dist]
    protection_points:  a list of protection points, each one being an object
                        providing attributes 'latitude' and 'longitude'
    registration_requests: a list of CBSD registration requests, each one being
                           a dictionary containing CBSD registration information
    grant_requests:     a list of grant requests, each one being a dictionary
                        containing grant information; there is a one-to-one
                        mapping between items in registration_requests and
                        grant_requests; a CBSD with more than one grant will
                        have corresponding duplicate items in registration_requests
    num_iter:           number of Monte Carlo iterations
    num_processes:      number of parallel processes to use
    pool:               optional |multiprocessing.Pool| to use

  Returns:
    result:             a Boolean list (same size as registration_requests/
                        grant_requests) with TRUE elements at indices having
                        grants on the move list
  """
  grants = data.getGrantsFromRequests(registration_requests, grant_requests)
  # Find the move list of each protection constraint with a pool of parallel processes.
  if pool is None:
    mpool.Configure(num_processes)
    pool = mpool.Pool()

  neighbor_distances = protection_specs.neighbor_distances
  try:
    min_azimuth = protection_specs.min_azimuth
    max_azimuth = protection_specs.max_azimuth
  except AttributeError:
    min_azimuth, max_azimuth = 0, 360

  moveListC = partial(moveListConstraint,
                      low_freq=protection_specs.lowFreq,
                      high_freq=protection_specs.highFreq,
                      grants=grants,
                      inc_ant_height=protection_specs.antHeight,
                      num_iter=num_iter,
                      threshold=protection_specs.threshold,
                      beamwidth=protection_specs.beamwidth,
                      min_azimuth=min_azimuth,
                      max_azimuth=max_azimuth,
                      neighbor_distances=neighbor_distances)
  M_c, _ = list(zip(*pool.map(moveListC, protection_points)))

  # Find the unique CBSD indices in the M_c list of lists.
  M = set().union(*M_c)

  # Set to TRUE the elements of the output Boolean array that have grant_index in
  # the move list.
  result = np.zeros(len(grants), bool)
  for k, grant in enumerate(grants):
    if grant in M:
      result[k] = True
  output = result.tolist()
  return output
