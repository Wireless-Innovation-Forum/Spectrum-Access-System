#    Copyright 2020 SAS Project Authors. All Rights Reserved.
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

r"""ESC protection impact (population).

This scripts computes an ESC impact figure based on the population that is
covered by a whisper zone.

Usage:
  # Measure ESC impact for category B, in a reasonably "fast mode".
  # (for all sensors in New Jersey and NYC + Long Island)
  esc_impact --esc_fads=a_fad.json,other_fad.json \
             --grid_arcsec=10 --category=B \
             --filter_box="(39, -75, 41, -72)"  \
             --fast_mode --force_radius_km=50

Notes:
  - One or several ESC fads can be specified. Aggregated statistics will be
    provided, per sensor, per ESC network and total.
  - The analysis resolution is specified in arcsec (1 arcsec ~= 30m). A typical
    resolution is grid_arcsec=10 (faster) or grid_arcsec=5 (slower).
  - the `--filter_box` allows for selecting a subset of the sensors within a
    (lat_min, lon_min, lat_max, lon_max) box.
  - The script is single thread, single process. To speed up the run, one can
    run independently (and in parallel) unconnected areas such as west coast,
    east coast and south-coast. Use --filter_box for that, for example:

  - `--fast_mode` and `--force_radius_km` are provided to speed up the analysis:
    + with fast_mode: heaversine method is used instead of vincenty (no real impact).
    + with force_radius_km: one can specify 50k CatB neighborhood for example
      (instead of regular 80km), as it is usually sufficient to capture the effective
      whisper zones.
"""
import argparse
import ast
import collections
import json
import time

import numpy as np
import shapely.geometry as sgeo

from reference_models.antenna import antenna
from reference_models.geo import utils
from reference_models.geo import zones
from reference_models.propagation import wf_itm
from usgs_pop import usgs_pop_driver
import geo_utils

#----------------------------------------
# Setup the command line arguments
parser = argparse.ArgumentParser(description='ESC Pop Impact')
parser.add_argument('--esc_fads', type=str, default='',
                    help='The ESC network as a FAD JSON files (separated by comma).')
parser.add_argument('--grid_arcsec', type=int, default=10,
                    help='The grid calculation resolution (in arcsec).')
parser.add_argument('--budget_offset_db', type=float, default=0,
                    help='A budget link offset (in dB).')
parser.add_argument('--category', type=str, default='B',
                    choices=['A', 'B', 'indoor'],
                    help='The CBSD category to compute impact for.')
parser.add_argument('--fast_mode', dest='fast_mode', action='store_true',
                    help='Use fast approximate calculation.')
parser.set_defaults(fast_mode=False)
parser.add_argument('--filter_box', type=str, default='',
                    help='A filtering box: (lat_min, lon_min, lat_max, lon_max)'
                    ' for the sensors to be processed')
parser.add_argument('--force_radius_km', type=int, default=0,
                    help='The neighborhood radius forced to a non standard value.')
parser.add_argument('--pop_dir', type=str, default='',
                     help='The USGS population directory. If unspecified, uses the'
                     ' one in default directory')
parser.add_argument('--terrain_dir', type=str, default='',
                    help='Terrain directory. If unspecified use default one.')
parser.add_argument('--lazy_pop', dest='lazy_pop', action='store_true',
                    help='Use lazy population loading.')
parser.add_argument('--nolazy_pop', dest='lazy_pop', action='store_false',
                    help='Disable lazy population loading - Load all at init.')
parser.set_defaults(lazy_pop=True)

FLAGS = parser.parse_args()


# Population resolution database
POP_RES_ARCSEC = 10

# Nominal EIRP per category
EIRP_CATB_MHZ = 37
EIRP_CATA_MHZ = 20
EIRP_INDOOR_MHZ = 20

# A container for ESC sensor params
EscSensor = collections.namedtuple('EscSensor', [
    'name', 'latitude', 'longitude', 'height', 'ant_azimuth', 'ant_pattern',
    'protection_level'
])


def _Pattern(json_pattern):
  """Converts from a JSON pattern to a numpy ndarray."""
  ant_pattern = sorted([(pat['angle'], pat['gain']) for pat in json_pattern])
  _, gains = list(zip(*ant_pattern))
  return np.array(gains)


def _ConvertEsc(esc):
  """Converts an ESC JSON dict into a more proper |EscSensor| representation."""
  name = esc['id'].split('/')[-1]
  params = esc['installationParam']
  height_type = params['heightType']
  if height_type.lower() != 'agl':
    raise ValueError('Unsupported heightType=%s' % height_type)
  return EscSensor(
      name=name,
      latitude=round(params['latitude'], 5),
      longitude=round(params['longitude'], 5),
      height=round(params['height'], 1),
      ant_azimuth=params['antennaAzimuth'],
      ant_pattern=_Pattern(params['azimuthRadiationPattern']),
      protection_level=esc.get('protectionLevel', -109))


def ComputeSensorNeighborhood(latitude, longitude, radius_km, res_arcsec):
  """Computes and grids the neighborhood of a sensor.

  Args:
    latitude: The sensor latitude (deg).
    longitude: The sensor longitude (deg).
    radius_km: The neighborhood radius (km).
    res_arcsec: The gridding resolution (arcsec)

  Returns:
    A tuple (latitudes, longitudes, geometry) representing the neighborhood:
      - latitudes & longitudes: the lists of gridded points.
      - geometry: a |shapely| Polygon (or MultiPolygon).
  """
  us_border = zones.GetUsBorder()
  sensor_nbor = geo_utils.Buffer(sgeo.Point(longitude, latitude), radius_km)
  sensor_nbor = sensor_nbor.intersection(us_border)
  longitudes, latitudes = list(zip(*utils.GridPolygon(sensor_nbor, res_arcsec)))
  return latitudes, longitudes, sensor_nbor


def CalcEscPathLoss(latitude_esc, longitude_esc, height_esc, latitudes_tx,
                    longitudes_tx, height_tx):
  """Computes path loss for sensor protection area.

  This uses the regular Winnforum ITM propagation model parameters.

  Args:
    latitude_esc: The sensor latitude (deg).
    longitude_esc: The sensor longitude (deg).
    height_esc: The sensor height (meters).
    latitudes_tx: A sequence of Tx latitudes (deg).
    longitudes_tx: A sequence of Tx longitudes (deg).
    height_tx: The Tx height (meters).

  Returns:
    A tuple (losses, esc_bearings, tx_bearings) holding the path losses (dB) and
    bearings (in degrees, clockwise from north) for each transmitter location.
    The bearings are provided both for sensor and Tx.
  """
  losses_db = []
  esc_bearings = []
  tx_bearings = []
  for (lat, lon) in zip(latitudes_tx, longitudes_tx):
    res = wf_itm.CalcItmPropagationLoss(
        lat,
        lon,
        height_tx,
        latitude_esc,
        longitude_esc,
        height_esc,
        reliability=-1)
    losses_db.append(res.db_loss)
    tx_bearings.append(res.incidence_angles.hor_cbsd)
    esc_bearings.append(res.incidence_angles.hor_rx)

  return np.array(losses_db), np.array(esc_bearings), np.array(tx_bearings)


def MaskPathLoss(losses_db,
                 bearings,
                 ant_hor_pattern,
                 ant_azimuth,
                 ant_gain_dbi=0,
                 misc_losses=0):
  """Applies antenna and misc losses.

  Args:
    losses_db: A scalar or ndarray of losses (dB).
    bearings: A scalar or ndarray of bearings (degrees), clockwise from north.
    ant_hor_pattern: The antenna horizontal pattern, defined as absolute gain on
      a sequence of 360 values (dB).
    ant_azimuth: The antenna azimuth direction (degrees), clockwise from north.
    ant_gain_dbi: Optional additional antenna gain (dBi). To be specified if the
      `antenna_hor_pattern` is normalized to 0dBi.
    misc_losses: Any additional misc losses (dB).

  Returns:
    The masked antenna losses (dB), as scalar or ndarray.
  """
  gains = antenna.GetAntennaPatternGains(bearings, ant_azimuth, ant_hor_pattern,
                                         ant_gain_dbi)
  return losses_db - gains + misc_losses


def PopulationImpact(networks,
                     category,
                     res_arcsec,
                     offset_db,
                     popper,
                     filter_box=None,
                     forced_radius_km=None):
  """Analyse some ESC network(s) in terms of population impact.

  Args:
    networks: A sequence of JSON FAD data representing each network.
    category: CBSD category either as 'A', 'B' or 'indoor'.
    res_arcsec: The calculation resolution (in arcsec).
    offset_db: An extra offset to the budget link. Positive value means more
      population impacted.
    popper: The population driver.
    filter_box: A tuple (min_lat, min_lon, max_lat, max_lon) defining a bounding
      box for sensors to be processed.
    forced_radius_km: If set, override the regular radius of the CBSD category.

  Returns:
    A tuple (total_pop, pop_per_network, pop_per_sensor) holding:
      - total_pop: the total population impact of the networks.
      - pop_per_network: a list of each network total population impact (no
      double counting across networks).
      - pop_per_sensor: a dict of each sensor population impact keyed by sensor
      name.
  """

  # Set the parameters depending on type of network to compuet impact for.
  if category == 'B':
    nbor_radius_km = 80
    cbsd_eirp_dbm_per_mhz = EIRP_CATB_MHZ
    cbsd_height = 25
    extra_loss = 0
  elif category == 'A':
    nbor_radius_km = 40
    cbsd_eirp_dbm_per_mhz = EIRP_CATA_MHZ
    cbsd_height = 6
    extra_loss = 0
  elif category == 'indoor':
    nbor_radius_km = 40
    cbsd_eirp_dbm_per_mhz = EIRP_INDOOR_MHZ
    cbsd_height = 5
    extra_loss = 15
  if forced_radius_km:
    nbor_radius_km = forced_radius_km

  total_pop = 0
  pop_per_sensor = {}
  pop_per_network = []
  all_location_processed = set()
  for i, network in enumerate(networks):
    print('ESC Network processing: #%d' % i)
    sensors = sorted([_ConvertEsc(sensor) for sensor in network],
                     key=lambda s: s.name)  # sorting to improve geo locality.
    net_location_processed = set()
    pop_per_network.append(0)
    for sensor in sensors:
      if filter_box and (sensor.latitude < filter_box[0] or
                         sensor.latitude > filter_box[2] or
                         sensor.longitude < filter_box[1] or
                         sensor.longitude > filter_box[3]):
        continue
      print('... processing: %s' % sensor.name)

      # Compute signal level in the whole neighborhood.
      lats, lons, _ = ComputeSensorNeighborhood(sensor.latitude,
                                                sensor.longitude,
                                                nbor_radius_km, res_arcsec)
      lats, lons = np.array(lats), np.array(lons)
      losses_db, esc_bearings, _ = CalcEscPathLoss(sensor.latitude,
                                                   sensor.longitude,
                                                   sensor.height, lats, lons,
                                                   cbsd_height)
      masked_losses_db = MaskPathLoss(losses_db, esc_bearings,
                                      sensor.ant_pattern, sensor.ant_azimuth)
      sig_level_dbm = cbsd_eirp_dbm_per_mhz - masked_losses_db - extra_loss

      # Detect the points that are impacted
      idxs = np.where(sig_level_dbm >= sensor.protection_level - offset_db)[0]

      # Compute the standalone population impact for that sensor.
      pop_per_sensor[sensor.name] = (
          geo_utils.AreaPlateCarreePixel(res_arcsec, sensor.latitude) *
          np.sum(popper.GetPopulationDensity(lats[idxs], lons[idxs])))
      print('      %d pops' % pop_per_sensor[sensor.name])

      # Compute the net and total population impact - avoid double counting.
      total_pop += pop_per_sensor[sensor.name]
      pop_per_network[-1] += pop_per_sensor[sensor.name]
      all_done_lats, all_done_lons = [], []
      net_done_lats, net_done_lons = [], []
      for k in idxs:
        key = round(lats[k], 5), round(lons[k], 5)
        if key in all_location_processed:
          all_done_lats.append(lats[k])
          all_done_lons.append(lons[k])
        else:
          all_location_processed.add(key)
        if key in net_location_processed:
          net_done_lats.append(lats[k])
          net_done_lons.append(lons[k])
        else:
          net_location_processed.add(key)
      if all_done_lats:
        total_pop -= (
            geo_utils.AreaPlateCarreePixel(res_arcsec, sensor.latitude) *
            np.sum(popper.GetPopulationDensity(all_done_lats, all_done_lons)))
      if net_done_lats:
        pop_per_network[-1] -= (
            geo_utils.AreaPlateCarreePixel(res_arcsec, sensor.latitude) *
            np.sum(popper.GetPopulationDensity(net_done_lats, net_done_lons)))

    print('*** Network Total: %d pops' % pop_per_network[-1])

  return total_pop, pop_per_network, pop_per_sensor


if __name__ == '__main__':
  print('## Measuring impact of ESC networks')

  # Special configuration.
  if FLAGS.terrain_dir:
    wf_itm.drive.ConfigureTerrainDriver(
        terrain_dir=FLAGS.terrain_dir, cache_size=16)
  if FLAGS.fast_mode:
    # Replace all Vincenty by simpler great circle for improving speed.
    geo_utils.ReplaceVincentyDistanceByHaversine()

  # Load the ESC sensors within the optional bounding box.
  print('Loading ESC networks')
  networks = []
  filter_box = None
  if FLAGS.filter_box:
    filter_box = ast.literal_eval(FLAGS.filter_box)
  esc_fads = FLAGS.esc_fads.split(',')
  for esc_fad in esc_fads:
    if not esc_fad:
      continue
    with open(esc_fad, 'r') as fd:
      sensors = json.load(fd)['recordData']
      networks.append(sensors)

  # Initialize popper, a population driver.
  print('** Init population raster: %s **' %
        'Lazy loading' if FLAGS.lazy_pop else 'Loading in memory')
  start_time = time.time()
  popper = usgs_pop_driver.UsgsPopDriver(FLAGS.pop_dir, FLAGS.lazy_pop)
  if not FLAGS.lazy_pop:
    popper.LoadRaster()
  print('.. done in %ds' % int(time.time() - start_time))

  # Compute the population impact
  print('** Evaluating population impact **')
  start_time = time.time()
  total_pop, pop_per_network, pop_per_sensor = PopulationImpact(
      networks, FLAGS.category, FLAGS.grid_arcsec, FLAGS.budget_offset_db,
      popper, filter_box, FLAGS.force_radius_km)
  print('.. done in %ds' % int(time.time() - start_time))

  # Ouput final statistics
  print('** Final results **')
  print('Total Population: {total_pop:.3f} kpops (1000s)'.format(
      total_pop=total_pop / 1000.))
  print('Network:')
  for k, pop_impact in enumerate(pop_per_network):
    print('    {k} : {pop_impact:.3f} kpops (1000s)'.format(
        k=k, pop_impact=pop_impact / 1000.))
  print('Sensors:')
  for sensor_name in sorted(pop_per_sensor):
    print('    {sensor_name} : {num_pop:.3f} kpops (1000s)'.format(
        sensor_name=sensor_name, num_pop=pop_per_sensor[sensor_name] / 1000.))
