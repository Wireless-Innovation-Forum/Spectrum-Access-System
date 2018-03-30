#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

"""Benchmark the DPA model timing.

This is a simple simulation of the DPA for purpose of estimating time to run.

Usage:
  python time_dpa.py

Notes:
  - multiprocessing facility not tested on Windows (use 1 process if issues)
  - if warning reported on cached tiles swapping, increase the cache size.
"""
# TODO(sbdt): add reporting for memory usage
from collections import namedtuple
import multiprocessing
import time

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from reference_models.move_list_calc import move_list
from reference_models.geo import zones
from reference_models.geo import drive
from reference_models.geo import utils
from reference_models.examples import entities

#------------------------------
# Define simulation parameters
# - DPA to simulate
dpa_name = 'east_dpa_7'

# - Number of sites to distribute within a given range of the DPA
num_sites = 500
max_dist_cat_a = 160
max_dist_cat_b = 320

# - Number of protection points in DPA per category.
# We divide the DPA in 4 buckets: front and back contour, front and back zone
# The front and back are separeted by the us border with some buffering.
# Note:  Keep a ratio as expected in final to get accurate timing estimate
npts_front_dpa_contour = 250    # The mainland facing contour
npts_back_dpa_contour = 100     # The back contour
npts_within_dpa_front = 100     # The front zone
npts_within_dpa_back = 50       # The back zone
front_usborder_buffer_km = 40   # Front contour defined by the extension of the
                                # front border.

# - Do we restrict the sites to be within the census-defined urban areas
do_inside_urban_area = False

# - Ratio of cat B and different catA
ratio_cat_b = 0.2
ratio_cat_a_indoor = 0.4

# - Simulation setup
#   + Number of parallel processes -
#     do not exceed your workstation parallel capabilities (number of core -2)
num_processes = 8
#   + Number of cached tiles (per process)
num_cached_tiles = 32

# - Internal parameters
num_montecarlo_iter = 2000
fmin, fmax = 3560, 3570
ratio_cat_a_outdoor = 1.0 - ratio_cat_b - ratio_cat_a_indoor

#----------------------------------
# Define the Protection points and specification
ProtectionPoint = namedtuple('ProtectionPoint',
                             ['latitude', 'longitude'])
ProtectionSpecs = namedtuple('ProtectionSpecs',
                             ['lowFreq', 'highFreq',
                              'antHeight', 'beamwidth', 'threshold'])

#----------------------------------------
# Configure the geo drivers to avoid swap
drive.ConfigureTerrainDriver(cache_size=num_cached_tiles)
drive.ConfigureNlcdDriver(cache_size=num_cached_tiles)

#----------------------------------------
# Preparing all simulation parameters
def PrepareSimulation():
  # Read the DPA zone
  print 'Preparing Zones'
  dpa_zone = zones.GetDpaZones()[dpa_name]
  us_border = zones.GetUsBorder()
  urban_areas = zones.GetUrbanAreas() if do_inside_urban_area else None
  protection_zone = zones.GetCoastalProtectionZone()

  # Distribute random CBSD of various types around the FSS.
  print 'Distributing random CBSDs in DPA neighborhood'
  # - Find the zone where to distribute the CBSDs
  typical_lat = dpa_zone.centroid.y
  km_per_lon_deg = 111. * np.cos(typical_lat * np.pi / 180)
  extend_cata_deg = max_dist_cat_a / km_per_lon_deg
  extend_catb_deg = max_dist_cat_b / km_per_lon_deg

  zone_cata = dpa_zone.buffer(extend_cata_deg).intersection(us_border)
  zone_catb = dpa_zone.buffer(extend_catb_deg).intersection(us_border)

  if urban_areas is not None:
    urban_areas = urban_areas.intersection(zone_catb)

  # - Distribute the CBSDs
  cbsds_cat_a_indoor = entities.GenerateCbsdsInPolygon(
      num_sites * ratio_cat_a_indoor,
      entities.CBSD_TEMPLATE_CAT_A_INDOOR,
      zone_cata,
      drive.nlcd_driver,
      urban_areas)

  cbsds_cat_a_outdoor = entities.GenerateCbsdsInPolygon(
      num_sites * ratio_cat_a_outdoor,
      entities.CBSD_TEMPLATE_CAT_A_OUTDOOR,
      zone_cata,
      drive.nlcd_driver,
      urban_areas)

  cbsds_cat_b = entities.GenerateCbsdsInPolygon(
      num_sites * ratio_cat_b,
      entities.CBSD_TEMPLATE_CAT_B,
      zone_catb,
      drive.nlcd_driver,
      urban_areas)

  all_cbsds = cbsds_cat_a_indoor + cbsds_cat_a_outdoor + cbsds_cat_b

  # - Convert them into proper registration and grant requests
  reg_requests = [entities.GetCbsdRegistrationRequest(cbsd)
                  for cbsd in all_cbsds]
  grant_requests = [entities.GetCbsdGrantRequest(cbsd, fmin, fmax)
                    for cbsd in all_cbsds]

  # Distribute points in DPA.
  # The idea is to keep a good ratio  typical of what would be used with the
  # actual implementation, so that the timing number can be scaled up.
  def SampleLine(line, num_points):
    step = line.length / (num_points-1)
    return [line.interpolate(dist) for dist in np.arange(0, line.length, step)]

  us_border_ext = us_border.buffer(front_usborder_buffer_km / 111.)
  front_line = dpa_zone.exterior.intersection(us_border_ext)
  back_line = dpa_zone.exterior.difference(us_border_ext)
  front_zone = dpa_zone.intersection(us_border_ext)
  back_zone = dpa_zone.difference(us_border_ext)
  step_front_dpa_arcsec = np.sqrt(front_zone.area / npts_within_dpa_front) * 3600.
  step_back_dpa_arcsec = np.sqrt(back_zone.area / npts_within_dpa_back) * 3600.

  protection_points = (
      [ProtectionPoint(longitude=pt.x, latitude=pt.y)
       for pt in SampleLine(front_line, npts_front_dpa_contour)] +
      [ProtectionPoint(longitude=pt.x, latitude=pt.y)
       for pt in SampleLine(back_line, npts_back_dpa_contour)] +
      [ProtectionPoint(longitude=pt[0], latitude=pt[1])
       for pt in utils.GridPolygon(front_zone, step_front_dpa_arcsec)] +
      [ProtectionPoint(longitude=pt[0], latitude=pt[1])
       for pt in utils.GridPolygon(back_zone, step_back_dpa_arcsec)])

  # Plot on screen the elements of calculation
  ax = plt.axes(projection=ccrs.PlateCarree())
  margin = 0.1
  box = zone_catb.union(dpa_zone)
  ax.axis([box.bounds[0]-margin, box.bounds[2]+margin,
           box.bounds[1]-margin, box.bounds[3]+margin])
  ax.coastlines()
  ax.stock_img()
  ax.scatter([pt.longitude for pt in protection_points],
             [pt.latitude for pt in protection_points],
             color='k', marker='*')
  ax.plot(*dpa_zone.exterior.xy, color='r')
  ax.plot(*zone_cata.exterior.xy, color='b', linestyle='--')
  ax.plot(*zone_catb.exterior.xy, color='g', linestyle='--')
  ax.plot(*protection_zone[0].exterior.xy, color='m', linestyle=':')
  ax.plot(*protection_zone[1].exterior.xy, color='m', linestyle=':')
  ax.scatter([cbsd.longitude for cbsd in all_cbsds],
             [cbsd.latitude for cbsd in all_cbsds],
             color='g', marker='.')

  ax.set_title('DPA: %s' % dpa_name)
  plt.show(block=False)

  return (protection_points,
          all_cbsds,
          reg_requests,
          grant_requests,
          protection_zone,
          ax)

# Useful functions
def get_tile_stats(dummy):
  return drive.terrain_driver.stats.ActiveTilesCount()

def print_tile_stats():
  drive.terrain_driver.stats.Report()

#--------------------------------------------------
# The simulation
if __name__ == '__main__':
  # reset the random seed
  np.random.seed(12345)

  # Create the pool of process
  # Done externally from the move_list function to keep terrains in cache
  pool = multiprocessing.Pool(num_processes)

  (protection_points, all_cbsds,
   reg_requests, grant_requests,
   protection_zone, ax) = PrepareSimulation()

  # The protection specification
  protection_spec = ProtectionSpecs(lowFreq=fmin*1e6, highFreq=fmax*1e6,
                                    antHeight=50, beamwidth=3, threshold=-144)

  # Run the move list algorithm a first time to fill up geo cache
  print 'Running Move List algorithm'
  print '  + once to populate the terrain cache'
  result = move_list.findMoveList(protection_spec, protection_points[:num_processes],
                                  reg_requests[0:100], grant_requests[0:100],
                                  num_montecarlo_iter, num_processes,
                                  protection_zone, pool)

  # Run it for real and measure time
  print '  + actual run'
  start_time = time.time()
  result = move_list.findMoveList(protection_spec, protection_points,
                                  reg_requests, grant_requests,
                                  num_montecarlo_iter, num_processes,
                                  protection_zone, pool)
  end_time = time.time()

  # Print results
  len_move_list = np.sum(result)
  print ''
  print 'Num Cores (Parallelization): %d' % num_processes
  print 'Num Protection Points: %d' % len(protection_points)
  print 'Num CBSD: %d' % len(reg_requests)
  print 'Move list size: %d' % len_move_list
  print 'Computation time: %.1fs' % (end_time - start_time)

  # Check tiles cache well behaved
  print  ''
  tile_stats = pool.map(get_tile_stats, [None]*num_processes)
  num_active_tiles, cnt_per_tile = tile_stats[0]
  if not num_active_tiles:
    print '-- Cache ERROR: No active tiles read'
  elif max(cnt_per_tile) > 1:
    print '-- Cache WARNING: cache tile too small - tiles are swapping from cache.'
    pool.apply_async(print_tile_stats, ())
  else:
    print '-- Cache tile: OK (no swapping)'

  # Plot the move list
  if len_move_list:
    ax.scatter([cbsd.longitude for k, cbsd in enumerate(all_cbsds) if result[k]],
               [cbsd.latitude for k, cbsd in enumerate(all_cbsds) if result[k]],
               color='r', marker='.')
    plt.show()
