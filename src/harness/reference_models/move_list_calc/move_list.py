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

# The main routine is 'moveListConstraint()' which calculates the move list
# for a single protection point.
#==================================================================================

import numpy as np
from operator import attrgetter, iadd
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
from shapely.geometry import MultiPolygon as MPolygon
from collections import namedtuple
from enum import Enum

# Import WINNF reference models including propagation, geo, and CBSD antenna gain models
from reference_models.propagation import wf_itm
from reference_models.geo import drive
from reference_models.geo import vincenty
from reference_models.common import data
from reference_models.antenna import antenna


# Set constant parameters based on requirements in the WINNF-TS-0112 [R2-SGN-24]
CAT_A_NBRHD_DIST = 150          # neighborhood distance for Cat-A CBSD (in km)
CAT_B_NBRHD_DIST = 200          # neighborhood distance for Cat-B CBSD (in km)
CAT_B_NBRHD_DIST_FOR_HT = 300   # neighborhood distance for Cat-B CBSD (in km) in
                                # consideration of antenna height
CAT_B_LONG_HT = 200             # height of Cat_B CBSD (in meters) in consideration of
                                # neighborhood distance Cat_B_NBRHD_DIST_FOR_HT
CAT_B_NBRHD_DIST_OOB = 25       # neighborhood distance for Cat-B CBSD
                                # for out-of-band inland DPA (in km)
PROTECTION_PERCENTILE = 95      # Monte Carlo percentile for protection

# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0

# Frequency range of co-channel DPAs (Hz)
LOW_FREQ_COCH = 3550000000
HIGH_FREQ_COCH = 3700000000

# Out-of-band maximum conducted power (dBm/MHz) (FCC Part 96 Rules (96.41))
OOB_POWER_WITHIN_10MHZ = -13
OOB_POWER_OUTSIDE_10MHZ = -25
OOB_POWER_BELOW_3530MHZ = -40


# Define interference contribution, i.e., a tuple with named fields of
# 'grantIndex', 'medianInterference', 'randomInterference', 'bearing_c_cbsd'
InterferenceContribution = namedtuple('InterferenceContribution',
                                      ['grantIndex', 'medianInterference',
                                       'randomInterference', 'bearing_c_cbsd'])


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


# A Cache for storing the height-above-average-terrain computed for neighborhood
# determination.
HaatCache = {}
def GetHaat(lat_cbsd, lon_cbsd, height_cbsd):

    global HaatCache

    # Simple technique (non-LRU) to prevent the cache size from increasing forever
    if len(HaatCache) > 1e7:
       HaatCache = {}  # Simply restart from scratch

    key = (lat_cbsd, lon_cbsd, height_cbsd)
    if key not in HaatCache:
       HaatCache[key] = wf_itm.ComputeHaat(lat_cbsd, lon_cbsd, height_cbsd)

    return HaatCache[key]


def findGrantsInsideNeighborhood(grants, constraint,
                                 exclusion_zone, dpa_type):
    """Identify the CBSD grants in the neighborhood of protection constraint.

    Inputs:
        grants:         a list of CBSD |data.CbsdGrantInfo| grants.
        constraint:     protection constraint of type |data.ProtectionConstraint|
        exclusion_zone: a polygon object or a list of locations.
                        If it is a list of locations, each one is a tuple
                        with fields 'latitude' and 'longitude'.
                        Default value is 'None'.
        dpa_type:       an enum member of class DpaType

    Returns:
        grants_inside:  a list of grants, each one being a namedtuple of type CBSDGrant,
                        of all CBSDs inside the neighborhood of the protection constraint.
    """
    # Initialize an empty list
    grants_inside = []

    # For co-channel offshore/inland DPAs, make sure exclusion zone is a polygon
    if dpa_type is not DpaType.OUT_OF_BAND:
        if isinstance(exclusion_zone, SPolygon) or isinstance(exclusion_zone, MPolygon):
            polygon_ex_zone = exclusion_zone
        else:
            polygon_ex_zone = SPolygon(exclusion_zone)

    # Loop over each CBSD grant and filter the ones inside the neighborhood
    for grant in grants:
        freq_check = True
        cbsd_in_nbrhd = False
        # Check frequency range
        low_freq_cbsd = grant.low_frequency
        high_freq_cbsd = grant.high_frequency
        if dpa_type is not DpaType.OUT_OF_BAND:
            low_freq_c = constraint.low_frequency
            high_freq_c = constraint.high_frequency
            overlapping_bw = min(high_freq_cbsd, high_freq_c) \
                             - max(low_freq_cbsd, low_freq_c)
            freq_check = (overlapping_bw > 0)
        else:
            freq_check = True

        if not freq_check:
          continue

        # Check CBSD location
        lat_cbsd = grant.latitude
        lon_cbsd = grant.longitude
        height_cbsd = grant.height_agl

        # Compute distance from CBSD location to protection constraint location
        lat_c = constraint.latitude
        lon_c = constraint.longitude
        dist_km, bearing, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd,
                                                               lat_c, lon_c)
        # Check if CBSD is inside the neighborhood of protection constraint
        if grant.cbsd_category == 'A':
            if dpa_type is not DpaType.OUT_OF_BAND:
                point_cbsd = SPoint(lon_cbsd, lat_cbsd)
                if dist_km <= CAT_A_NBRHD_DIST and polygon_ex_zone.contains(point_cbsd):
                    cbsd_in_nbrhd = True
        elif grant.cbsd_category == 'B':
            if dpa_type is not DpaType.OUT_OF_BAND:
                if dist_km <= CAT_B_NBRHD_DIST:
                    cbsd_in_nbrhd = True
                elif dist_km <= CAT_B_NBRHD_DIST_FOR_HT:
                    height_cbsd_haat = GetHaat(lat_cbsd, lon_cbsd, height_cbsd)
                    if height_cbsd_haat >= CAT_B_LONG_HT:
                        cbsd_in_nbrhd = True
            else:
                if dist_km <= CAT_B_NBRHD_DIST_OOB:
                    cbsd_in_nbrhd = True
        else:
            raise ValueError('Unknown category %s' % grant.cbsd_category)

        if not cbsd_in_nbrhd:
          continue

        grants_inside.append(grant)

    return grants_inside


def ComputeOOBConductedPower(low_freq_cbsd, low_freq_c, high_freq_c):
    """
    Compute maximum conducted power of a CBSD grant to an out-of-band
    protection constraint based on FCC Part 96 Rules (96.41)

    Inputs:
        low_freq_cbsd:  low frequency of CBSD grant channel (Hz)
        low_freq_c:     low frequency of protection constraint (Hz)
        high_freq_c:    high frequency of protection constraint (Hz)

    Returns:
        Maximum out-of-band conducted power (dBm)
    """
    # Compute overlapping bandwidths
    overlap_bw_within_10MHz = min(low_freq_cbsd, high_freq_c) \
                              - max(low_freq_cbsd-10000000.0, low_freq_c)
    overlap_bw_outside_10MHz = min(low_freq_cbsd-10000000.0, high_freq_c) \
                               - max(3530000000.0, low_freq_c)
    overlap_bw_below_3530MHz = min(3530000000.0, high_freq_c) \
                               - low_freq_c

    # Compute total conducted power
    power_within_10MHz_mW = 0
    power_outside_10MHz_mW = 0
    power_below_3530MHz_mW = 0
    if overlap_bw_within_10MHz > 0:
        power_within_10MHz_mW = 10 ** (OOB_POWER_WITHIN_10MHZ / 10.) \
                                * overlap_bw_within_10MHz / 1000000.0

    if overlap_bw_outside_10MHz > 0:
        power_outside_10MHz_mW = 10 ** (OOB_POWER_OUTSIDE_10MHZ / 10.) \
                                 * overlap_bw_outside_10MHz / 1000000.0

    if overlap_bw_below_3530MHz > 0:
        power_below_3530MHz_mW = 10 ** (OOB_POWER_BELOW_3530MHZ / 10.) \
                                 * overlap_bw_below_3530MHz / 1000000.0

    power_mW = power_within_10MHz_mW + power_outside_10MHz_mW + power_below_3530MHz_mW

    return 10 * np.log10(power_mW)


def computeInterference(grant, constraint, inc_ant_height, num_iteration, dpa_type):
    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.

    Inputs:
        cbsd_grant:     a |CbsdGrantInfo| grant
        constraint: 	protection constraint of type |data.ProtectionConstraint|
        inc_ant_height: reference incumbent antenna height (in meters)
        num_iteration:  a number of Monte Carlo iterations
        dpa_type:       an enum member of class DpaType

    Returns:
        interference: 	interference contribution, a tuple with named fields
                        'grantIndex', 'medianInterference', 'randomInterference'
                        (K random interference contributions of the grant to
                        protection constraint c), and 'bearing_c_cbsd'
                        (bearing from c to CBSD grant location).
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
                     + 10 * np.log10(co_channel_bw / 1000000.0))

        # Overlapping bandwidth between the first 10 MHz adjacent-channel of CBSD grant and
        # the frequency range of protection constraint
        adj_channel_bw = min(10.e6, high_freq_c - low_freq_c - co_channel_bw)

        # Incorporate EIRP within the adjacent-bandwidth into the total EIRP
        if adj_channel_bw != 0:
            # Compute EIRP within the adjacent-bandwidth
            eirp_adj_channel_bw = (OOB_POWER_WITHIN_10MHZ + ant_gain
                                   + 10 * np.log10(adj_channel_bw / 1000000.0))
            # Compute total EIRP
            eirp_cbsd = 10 * np.log10(10**(eirp_cbsd/10.) + 10**(eirp_adj_channel_bw/10.))

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
    interference = InterferenceContribution(grantIndex=grant.grant_index,
                                            medianInterference=median_interf,
                                            randomInterference=K_interf,
                                            bearing_c_cbsd=results.incidence_angles.hor_rx)
    return interference


def formInterferenceMatrix(grants, constraint, inc_ant_height, num_iter, dpa_type):
    """
    Form the matrix of interference contributions to protection constraint c.

    Inputs:
        grants:             a list of |CbsdGrantInfo| grants of all CBSDs inside the
                            neighborhood of the protection constraint.
        constraint:         protection constraint of type |data.ProtectionConstraint|
        inc_ant_height:     reference incumbent antenna height (in meters)
        num_iter:           number of random iterations
        dpa_type:           an enum member of class DpaType

    Returns:
        I:                  a matrix of interference contributions to protection
                            constraint (c) with dimensions (num_iter . len(grants))
        sorted_grant_indices: a list of indices of the sorted grant list
        sorted_bearings:    a list of bearings from protection point to CBSDs of the
                            sorted grant list
    """
    # Compute interference contributions of each grant to the protection constraint
    interf_list = []
    for cbsd_grant in grants:
        interf = computeInterference(cbsd_grant, constraint, inc_ant_height,
                                     num_iter, dpa_type)
        interf_list.append(interf)

    # Sort grants by their median interference contribution, smallest to largest
    interf_list.sort(key=attrgetter('medianInterference'))

    # Get indices, bearings, interference contributions of the sorted grants
    sorted_grant_indices = [interf.grantIndex for interf in interf_list]
    sorted_bearings = [interf.bearing_c_cbsd for interf in interf_list]
    I = np.array([interf.randomInterference for interf in interf_list]).transpose()

    return I, sorted_grant_indices, sorted_bearings


def find_nc(I, bearings, t, beamwidth):
    """
    Return the index (nc) of the grant in the ordered list of grants such that
    the protection percentile of the interference from the first nc grants is below the
    threshold for all azimuths of the receiver antenna.

    Inputs:
        I:      2D array of interference contributions (dBm/10 MHz); columns
                correspond to grants, and rows correspond to Monte Carlo iterations
        bearings: a list of bearings from protection point to CBSDs
        t:      protection percentile threshold (dBm/10 MHz)
        beamwidth: protection antenna beamwidth (degree)

    Returns:
        nc:     index nc that defines the move list to be {G_nc+1, G_nc+2, ..., G_Nc}
    """
    # Create array of incumbent antenna azimuth angles (degrees).
    if beamwidth == 360.0:
        azimuths = [0]
    else:
        azimuths = np.arange(0.0, 360.0, beamwidth/2.0)

    # Initialize nc to Nc.
    Nc = I.shape[1]
    nc = Nc

    # Convert protection threshold and interference matrix to linear units.
    t_mW = np.power(10.0, t/10.0)
    I_mW = np.power(10.0, I/10.0)

    # Loop through every azimuth angle.
    for azi in azimuths:

        # Calculate interference contributions at output of receiver antenna.
        if beamwidth == 360.0:
            dpa_gains = 0
        else:
            dpa_gains = antenna.GetRadarNormalizedAntennaGains(bearings, azi)
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
            mid = (hi + lo) / 2
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


def moveListConstraint(protection_point, low_freq, high_freq,
                       grants,
                       exclusion_zone, inc_ant_height,
                       num_iter, threshold, beamwidth):
    """Returns the move list for a given protection constraint.

    The move listsNote that the returned indexes corresponds to the grant.grant_index

    Inputs:
        protection_point:  A protection point location, having attributes 'latitude' and
                           'longitude'.
        low_freq:          The low frequency of protection constraint (Hz).
        high_freq:         The high frequency of protection constraint (Hz).
        grants:            A list of CBSD |data.CbsdGrantInfo| grants.
        exclusion_zone:    The protection zone as a shapely Polygon/MultiPolygon or
                           a list of locations with attributes 'latitude' and 'longitude'.
        inc_ant_height:    The reference incumbent antenna height (meters).
        num_iter:          The number of Monte Carlo iterations.
        threshold:         The protection threshold (dBm/10 MHz).
        beamwidth:         The protection antenna beamwidth (degree).

    Returns:
        A tuple of (move_list_idx, neighbor_list_idx) for that protection constraint:
          + the list of indices of grants on the move list.
          + the list of indices of grants in the neighborhood list.
    """
    dpa_type = findDpaType(low_freq, high_freq)

    # Assign values to the protection constraint
    constraint = data.ProtectionConstraint(latitude=protection_point.latitude,
                                           longitude=protection_point.longitude,
                                           low_frequency=low_freq,
                                           high_frequency=high_freq,
                                           entity_type=data.ProtectedEntityType.DPA)

    # Identify CBSD grants in the neighborhood of the protection constraint
    neighbor_grants = findGrantsInsideNeighborhood(grants, constraint,
                                                   exclusion_zone, dpa_type)
    neighbor_idx = [grant.grant_index for grant in neighbor_grants]

    if len(neighbor_grants):  # Found CBSDs in the neighborhood
        # Form the matrix of interference contributions
        I, sorted_grant_indices, bearings = formInterferenceMatrix(
            neighbor_grants, constraint, inc_ant_height, num_iter, dpa_type)

        # Find the index (nc) of the grant in the ordered list of grants such that
        # the protection percentile of the interference from the first nc grants is below
        # the threshold for all azimuths of the receiver antenna.
        nc = find_nc(I, bearings, threshold, beamwidth)

        # Determine the associated move list (Mc)
        movelist_idx = sorted_grant_indices[nc:]
        return (movelist_idx, neighbor_idx)

    return ([], neighbor_idx)


def calcInterference(protection_point, low_freq, high_freq,
                     grants,
                     exclusion_zone, inc_ant_height,
                     num_iter, beamwidth):
  """Computes the 95% interference quantile on a protected point.

    Inputs:
        protection_point:  A protection point location, having attributes 'latitude' and
                           'longitude'.
        low_freq:          The low frequency of protection constraint (Hz).
        high_freq:         The high frequency of protection constraint (Hz).
        grants:            A list of CBSD |data.CbsdGrantInfo| active grants.
        exclusion_zone:    The protection zone as a shapely Polygon/MultiPolygon or
                           a list of locations with attributes 'latitude' and 'longitude'.
        inc_ant_height:    The reference incumbent antenna height (meters).
        num_iter:          The number of Monte Carlo iterations.
        beamwidth:         The protection antenna beamwidth (degree).

    Returns:
        A vector of interference values (ndarray) of length N, where the element k
        corresponds to azimuth k * (beamwith/2).
        The length N is thus equal to 2 * 360 / beamwith.
  """
  dpa_type = findDpaType(low_freq, high_freq)

  # Assign values to the protection constraint
  constraint = data.ProtectionConstraint(latitude=protection_point.latitude,
                                         longitude=protection_point.longitude,
                                         low_frequency=low_freq,
                                         high_frequency=high_freq,
                                         entity_type=data.ProtectedEntityType.DPA)

  # Identify CBSD grants in the neighborhood of the protection constraint
  neighbor_grants = findGrantsInsideNeighborhood(grants, constraint,
                                                 exclusion_zone, dpa_type)
  interf_matrix = np.zeros((num_iter, len(neighbor_grants)))
  bearings = np.zeros(len(neighbor_grants))
  for grant in neighbor_grants:
    interf = computeInterference(grant, constraint, inc_ant_height,
                                 num_iter, dpa_type)
    interf_matrix[:,k] = inter.randomInterference
    bearings[k] = interf.bearing_c_cbsd

  interf_matrix = 10**(interf_matrix / 10.)
  if beamwidth == 360.0:
    azimuths = [0]
  else:
    azimuths = np.arange(0.0, 360.0, beamwidth/2.0)

  agg_interf = np.zeros(len(azimuths))
  for k, azi in enumerate(azimuths):
    if beamwidth == 360.0:
      dpa_gains = 0
    else:
      dpa_gains = antenna.GetRadarNormalizedAntennaGains(bearings, azi)
    dpa_interf = interf_matrix * 10**(dpa_gains / 10.0)
    agg_interf[k] = np.percentile(np.sum(dpa_interf, axis=1),
                                  PROTECTION_PERCENTILE, interpolation='lower')

  return 10 * np.log10(agg_interf)
