import json
import sys
import time

import numpy as np
import shapely.geometry as sgeo

from reference_models.common import data
from reference_models.geo import drive
from reference_models.geo import nlcd
from reference_models.propagation import wf_hybrid

# The approximate earth radius defined by International Union of Geodesy and
# Geophysics (http://www.iugg.org/).
_EARTH_MEAN_RADIUS_KM = 6371.0088


def ReadFadGrants(fad_file, filter_geom=None):
  """Returns |CbsdGrantInfo| grants from FAD.

  Args:
    fad_file: A JSON FAD file holding CBSD and grants.
    filter_geom: An optional geometry for filtering grants.
  """
  with open(fad_file, 'rb') as fd:
    cbsds = json.load(fd)

  grants = []
  for cbsd in cbsds['recordData']:
    cbsd_id = cbsd['id']
    reg = cbsd['registration']
    if (filter_geom and not sgeo.Point(
        reg['installationParam']['longitude'],
        reg['installationParam']['latitude']).within(filter_geom)):
      continue
    for grant in cbsd['grants']:
      grants.append(
          data.constructCbsdGrantInfo(
              reg, grant, is_managing_sas=True))

  return grants


def GetCbsdStatsStr(grants):
  """Returns basic statistics on `grants` sequence as a str."""
  # Find unique CBSDS
  sites = set((g.latitude, g.longitude, g.cbsd_category, g.indoor_deployment)
              for g in grants)
  cbsds = set((g.latitude, g.longitude, g.antenna_azimuth, g.cbsd_category,
               g.indoor_deployment) for g in grants)
  return '  %d sites [%d CBSDs %d grants]: %d CatB - %d CatA_out - %d CatA_in' % (
      len(sites), len(cbsds), len(grants),
      len([cbsd for cbsd in cbsds if cbsd[3] == 'B'
          ]), len([cbsd for cbsd in cbsds if cbsd[3] == 'A' and not cbsd[4]]),
      len([cbsd for cbsd in cbsds if cbsd[3] == 'A' and cbsd[4]]))


def PrintGrant(grant):
  """Prints a |CbsdGrantInfo| grant."""
  print('  %s: %8.5f,%10.5f @%4.1fm:%3ddB [%4d-%4d] Over %5.2fdB'
        ' : azi %3d  beam %3d gain %2ddB - %s - %s' %
        (grant.cbsd_category, grant.latitude, grant.longitude, grant.height_agl,
         grant.max_eirp, grant.low_frequency * 1e-6,
         grant.high_frequency * 1e-6, grant.data.get('ml_offs', -999),
         grant.antenna_azimuth, grant.antenna_beamwidth, grant.antenna_gain,
         ' Indoor' if grant.indoor_deployment else 'Outdoor', grant.cbsd_id))

# Great Circle methods in replacement of Vincenty methods.
# A good description of Haversine formula in their numerical stable version
# can be found at : https://www.movable-type.co.uk/scripts/latlong.html
def GreatCircleDistanceBearing(lat1, lon1, lat2, lon2, accuracy=None):
  """Calculates distance and bearings between points on earth.

  This uses Haversine method considering the earth as a sphere.
    See: https://en.wikipedia.org/wiki/Haversine_formula
  This routine is designed to be a pure replacement of the similar
  'google3.third_party.winnforum_sas.vincenty.GeodesicDistanceBearing()'
  which uses the more precise Vincenty-based formula but is much slower.
  It also goes beyond the vincenty implementation as it supports sequence
  of points, either on the initial, final points or both.

  Args:
    lat1 (float or iterable of float): The initial point(s) latitude (degrees).
    lon1 (float or iterable of float): The initial point(s) longitude (degrees).
    lat2 (float or iterable of float): The final point(s) latitude (degrees).
    lon2 (float or iterable of float): The final point(s) longitude (degrees).
    accuracy: (unused) For compatibility with vincenty method prototype.

  Returns:
    A tuple of distance (km), direct bearing and back bearing (degrees). If
    an iterable of points are passed as input, ndarray are returned.
  """
  if lat1 == lat2 and lon1 == lon2:
    return 0, 0, -180
  lat1 = np.deg2rad(lat1)
  lat2 = np.deg2rad(lat2)
  delta_lat = lat2 - lat1
  delta_lon = np.deg2rad(lon2) - np.deg2rad(lon1)
  sin_lat1 = np.sin(lat1)
  cos_lat1 = np.cos(lat1)
  sin_lat2 = np.sin(lat2)
  cos_lat2 = np.cos(lat2)

  phi = (
      np.sin(delta_lat / 2)**2 + cos_lat1 * cos_lat2 *
      (np.sin(delta_lon / 2)**2))
  phi = 2 * np.arctan2(np.sqrt(phi), np.sqrt(1 - phi))
  distance = _EARTH_MEAN_RADIUS_KM * phi

  bearing = np.rad2deg(
      np.arctan2(
          np.sin(delta_lon) * cos_lat2,
          cos_lat1 * sin_lat2 - sin_lat1 * cos_lat2 * np.cos(delta_lon)))
  rev_bearing = np.rad2deg(
      np.arctan2(-np.sin(delta_lon) * cos_lat1,
                 cos_lat2 * sin_lat1 - sin_lat2 * cos_lat1 * np.cos(delta_lon)))
  if np.isscalar(bearing):
    if bearing < 0:
      bearing += 360
    if rev_bearing < 0:
      rev_bearing += 360
  else:
    bearing[bearing < 0] += 360
    rev_bearing[rev_bearing < 0] += 360

  return distance, bearing, rev_bearing


def GreatCirclePoint(lat, lon, dist_km, bearing, accuracy=None):
  """Computes the coordinates of a point towards a bearing at given distance.

  This uses Haversine method considering the earth as a sphere.
    See: https://en.wikipedia.org/wiki/Haversine_formula
  This routine is designed to be a pure replacement of the similar
  'google3.third_party.winnforum_sas.vincenty.GeodesicDistanceBearing()'
  which uses the more precise Vincenty-based formula but is much slower.

  Args:
    lat (float): The initial point latitude (degrees).
    lon (float): The initial point longitude (degrees).
    dist_km (float): The distance of the target point (km).
    bearing (float): The bearing angle (in degrees)
    accuracy (unused): For compatibility with vincenty method prototype.

  Returns:
    A tuple of the final point latitude, longitude and final reverse bearing,
    all in degrees.
  """
  tgt_lat, tgt_lon, rev_bearing = GreatCirclePoints(lat, lon, [dist_km],
                                                    bearing)
  return tgt_lat[0], tgt_lon[0], rev_bearing[0]


def GreatCirclePoints(lat, lon, distances_km, bearing, accuracy=None):
  """Computes the coordinates of points towards a bearing at several distances.

  This uses Haversine method considering the earth as a sphere.
    See: https://en.wikipedia.org/wiki/Haversine_formula
  This routine is designed to be a pure replacement of the similar
  'google3.third_party.winnforum_sas.vincenty.GeodesicPoints()'
  which uses the more precise Vincenty-based formula but is much slower.

  This routine is similar to `GreatCirclePoint` but can take any coherent
  sequence of values for the initial point, distances or bearing, and
  perform an efficient vectorized operation internally. 'Coherent' means that
  either only one of the input is a sequence, or several are with the same
  shapes.

  Args:
    lat: The initial point latitude (degrees).
    lon: The initial point longitude (degrees).
    distances_km (iterable of float): A sequence of distance of the target
      points (in km). Can be for example a ndarray or a list.
    bearing (float or iterable of float): The bearing angle (in degrees).
    accuracy (unused): For compatibility with vincenty method prototype.

  Returns:
    A tuple of the points latitude, longitude and reverse bearing, all in
    degrees. If one of the input is a ndarray, ndarray are returned,
    otherwise lists are returned.
  """
  is_array = (
      isinstance(distances_km, np.ndarray) or isinstance(bearing, np.ndarray) or
      isinstance(lat, np.ndarray))
  lat = np.deg2rad(lat)
  lon = np.deg2rad(lon)
  bearing = np.deg2rad(bearing)
  norm_distances = np.asarray(distances_km) / _EARTH_MEAN_RADIUS_KM
  tgt_lat = np.arcsin(
      np.sin(lat) * np.cos(norm_distances) +
      np.cos(lat) * np.sin(norm_distances) * np.cos(bearing))
  tgt_lon = lon + np.arctan2(
      np.sin(bearing) * np.sin(norm_distances) * np.cos(lat),
      np.cos(norm_distances) - np.sin(lat) * np.sin(tgt_lat))
  rev_bearing = np.rad2deg(
      np.arctan2(-np.sin(tgt_lon - lon) * np.cos(lat),
                 np.cos(tgt_lat) * np.sin(lat) -
                 np.sin(tgt_lat) * np.cos(lat) * np.cos(tgt_lon - lon)))
  tgt_lat = np.rad2deg(tgt_lat)
  tgt_lon = np.rad2deg(tgt_lon)
  rev_bearing[rev_bearing < 0] += 360

  if is_array:
    return tgt_lat, tgt_lon, rev_bearing
  else:
    return list(tgt_lat), list(tgt_lon), list(rev_bearing)


def AnalyzeCbsd(tx_lat, tx_lon, tx_height, indoor, category):
  # Find the landcover type
  azimuths = np.arange(0., 360., 4)
  distances = np.arange(0., 1.0, 0.05)
  points = []
  for azimuth in azimuths:
    lats, lons, _ = GreatCirclePoints(tx_lat, tx_lon, distances, azimuth)
    points.extend([(lat, lon) for lat,lon in zip(lats, lons)])
  tx_region = drive.nlcd_driver.RegionNlcdVote(points)
  if tx_region == 'RURAL':
    return None

  # Find evaluatio radial points around the tx
  azimuths = np.arange(0, 360., 2)
  orig_loss = []
  corr_loss = []
  num_links = 0
  if 0:
    inland_points = []
    distances = np.arange(4., 40., 2) if category=='A' else np.arange(4., 80., 2.)
    for azimuth in azimuths:
      lats, lons, _ = GreatCirclePoints(tx_lat, tx_lon, distances, azimuth)
      inland_points.extend([(lat, lon) for lat,lon in zip(lats, lons)])
      land_covers = drive.nlcd_driver.GetLandCoverCodes(*list(zip(*inland_points)))

    inland_points = [pt for idx, pt in enumerate(inland_points)
                     if land_covers[idx] > nlcd.LandCoverCodes.OPEN_WATER]
    num_links += len(inland_points)
    for lat, lon in inland_points:
      its_elev = drive.terrain_driver.TerrainProfile(
          lat1=tx_lat, lon1=tx_lon,
          lat2=lat, lon2=lon,
          target_res_meter=30.,
          do_interp=True, max_points=1501)
      orig_loss.append(wf_hybrid.CalcHybridPropagationLoss(
          tx_lat, tx_lon, tx_height,
          lat, lon, 1.5,
          cbsd_indoor=indoor,
          reliability=-1,
          freq_mhz=3625,
          region=tx_region,
          its_elev=its_elev).db_loss)
      corr_loss.append(wf_hybrid.CalcHybridPropagationLoss(
          tx_lat, tx_lon, tx_height,
          lat, lon, 1.5,
          cbsd_indoor=indoor,
          reliability=-1,
          freq_mhz=-3625,
          region=tx_region,
          its_elev=its_elev).db_loss)
  else:
    distance = 40 if category=='A' else 80
    for azimuth in azimuths:
      # Avoid end point at sea
      lats, lons, _ = GreatCirclePoints(tx_lat, tx_lon, np.arange(1.0, distance), azimuth)
      land_covers = drive.nlcd_driver.GetLandCoverCodes(lats, lons)
      eff_dist = distance
      for cover in reversed(land_covers):
        if cover != nlcd.LandCoverCodes.OPEN_WATER:
          break
        eff_dist -= 1
      rx_lat, rx_lon, _ = GreatCirclePoint(tx_lat, tx_lon, eff_dist, azimuth)
      its_elev = drive.terrain_driver.TerrainProfile(
          lat1=tx_lat, lon1=tx_lon,
          lat2=rx_lat, lon2=rx_lon,
          target_res_meter=30.,
          do_interp=True, max_points=2700)
      span_dists = np.arange(eff_dist, 2, -2)
      rx_lats, rx_lons, _ = GreatCirclePoints(tx_lat, tx_lon, span_dists, azimuth)
      profile = its_elev
      for k,dist in enumerate(span_dists):
        num_links += 1
        profile = profile[0:(2+(len(its_elev)-2)*dist//eff_dist)]
        profile[0] = len(profile)-2-1
        orig_loss.append(wf_hybrid.CalcHybridPropagationLoss(
            tx_lat, tx_lon, tx_height,
            rx_lats[k], rx_lons[k], 1.5,
            cbsd_indoor=indoor,
            reliability=-1,
            freq_mhz=3625,
            region=tx_region,
            its_elev=profile).db_loss)
        corr_loss.append(wf_hybrid.CalcHybridPropagationLoss(
            tx_lat, tx_lon, tx_height,
            rx_lats[k], rx_lons[k], 1.5,
            cbsd_indoor=indoor,
            reliability=-1,
            freq_mhz=-3625,
            region=tx_region,
            its_elev=profile).db_loss)

  diffs = np.array(orig_loss) - np.array(corr_loss)
  num_points = len(diffs)
  pos_diffs = diffs[diffs > 0.1]
  neg_diffs = diffs[diffs < -0.1]
  num_pos_diffs = len(pos_diffs)
  num_neg_diffs = len(neg_diffs)
  ratio_pos = num_pos_diffs / float(num_points)
  diff_pos_avg = np.mean(pos_diffs) if num_pos_diffs else 0
  diff_pos_min = np.min(pos_diffs) if num_pos_diffs else 0
  diff_pos_max = np.max(pos_diffs) if num_pos_diffs else 0
  ratio_neg = num_neg_diffs / float(num_points)
  diff_neg_avg = np.mean(neg_diffs) if num_neg_diffs else 0
  diff_neg_min = np.min(neg_diffs) if num_neg_diffs else 0
  diff_neg_max = np.max(neg_diffs) if num_neg_diffs else 0
  return (num_links, num_pos_diffs, num_neg_diffs,
          (ratio_pos, diff_pos_avg, diff_pos_min, diff_pos_max, pos_diffs),
          (ratio_neg, diff_neg_avg, diff_neg_min, diff_neg_max, neg_diffs))




def SimHybridCorr(fad_files):
  print('.. Read FAD grants')
  grants = []
  for fad_file in fad_files:
    grants.extend(ReadFadGrants(fad_file))

  print('.. Extract unique CBSDs locations')
  cbsds = set((g.latitude, g.longitude, g.height_agl,
               g.indoor_deployment, g.cbsd_category)
              for g in grants)
  print('   Total sites = %d' % len(cbsds))

  # Sort the CBSDs for better locality
  # cbsds = sorted(cbsds, key = lambda c: return (c.latitude, c.longitude)))

  num_rural = 0
  num_mod = 0
  num_pos_mod = 0
  num_neg_mod = 0
  num_links = 0
  mod_pos_avgs = []
  mod_pos_ratios = []
  mod_pos_mins = []
  mod_pos_maxs = []
  mod_neg_avgs = []
  mod_neg_ratios = []
  mod_neg_mins = []
  mod_neg_maxs = []
  mod_diffs =[]

  try:
    for k, cbsd in enumerate(cbsds):
      if k % 10 == 0:
        sys.stdout.write('*')
        sys.stdout.flush()
      if k % 500 == 0:
        sys.stdout.write('\n')
        # Analyse
      res = AnalyzeCbsd(*cbsd)
      if res is None:
        num_rural += 1
        continue
      num_links += res[0]
      if res[1]+res[2] != 0:
        num_mod += 1
        mod_diffs.extend(res[3][-1])
        mod_diffs.extend(res[4][-1])
      if res[1] != 0:
        num_pos_mod += 1
        mod_pos_ratios.append(res[3][0])
        mod_pos_avgs.append(res[3][1])
        mod_pos_mins.append(res[3][2])
        mod_pos_maxs.append(res[3][3])
      if res[2] != 0:
        num_neg_mod += 1
        mod_neg_ratios.append(res[4][0])
        mod_neg_avgs.append(res[4][1])
        mod_neg_mins.append(res[4][2])
        mod_neg_maxs.append(res[4][3])
  except KeyboardInterrupt:
    pass

  num_non_rural = k-num_rural
  print('STATS:')
  print('Num Rural: %d / %d (%.2f%%)' %
        (num_rural, k, 100.*num_rural/k))
  print('Num Non Rural: %d / %d (%.2f%%)\n' %
        (num_non_rural, k, 100.*num_non_rural/k))
  print('Num Tx with modified links:\n'
        '  Tot: %d / %d (%.2f%%)\n'
        '       pos= %d (%.2f%%)\n'
        '       neg= %d (%.2f%%)\n' %
        (num_mod, k, 100.*num_mod/k,
         num_pos_mod, 100.*num_pos_mod/k,
         num_neg_mod, 100.*num_neg_mod/k))
  print('Num modified links: %d / %d (%.2f%%)\n' %
        (len(mod_diffs), num_links, 100.*len(mod_diffs)/num_links))

  return {'num_cbsd':len(cbsds),
          'num_rural': num_rural,
          'num_non_rural': num_non_rural,
          'num_mod': num_mod,
          'num_pos_mod': num_pos_mod,
          'num_neg_mod': num_neg_mod,
          'mod_diffs': mod_diffs,
          'mod_pos_ratios': mod_pos_ratios,
          'mod_pos_avgs': mod_pos_avgs,
          'mod_pos_mins': mod_pos_mins,
          'mod_pos_maxs': mod_pos_maxs,
          'mod_neg_ratios': mod_pos_ratios,
          'mod_neg_avgs': mod_pos_avgs,
          'mod_neg_mins': mod_pos_mins,
          'mod_neg_maxs': mod_pos_maxs}

if __name__ == '__main__':
  print('Running Hybrid corr simulation')
  start_time = time.time()
  #res = SimHybridCorr(['cbsd_net/goo/cbsd_google.json'])
  res = SimHybridCorr(['cbsd_net/red/cbsd_red.json'])
  print('Run in %ds' % (time.time() - start_time))
