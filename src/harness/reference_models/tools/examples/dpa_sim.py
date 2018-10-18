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

"""DPA move list and TH interference check simulator based on IPR configs.

This is a simulation of the DPA test harness process for purpose of analyzing
the pass/fail criteria of the test harness.

Usage:
  python time_dpa.py --option1 --option2 <config.json>
where: config.json is an IPR config file

Notes:
  - multiprocessing facility not tested on Windows (use 1 process if issues)
  - if warning reported on cached tiles swapping, increase the cache size.
"""

from collections import namedtuple
import argparse
import json
import time

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from reference_models.dpa import dpa_mgr
from reference_models.common import data
from reference_models.common import mpool
from reference_models.geo import zones
from reference_models.geo import drive
from reference_models.geo import utils
from reference_models.tools import entities

#----------------------------------------
# Setup the command line arguments
parser = argparse.ArgumentParser(description='DPA Simulator')
parser.add_argument('--seed', type=int, help='Random seed.')
parser.add_argument('--num_process', type=int, default=-1,
                    help='Number of parallel process. -2=all-1, -1=50%.')
#parser.add_argument('--option', action='store_true', help='An option.')
parser.add_argument('config_file', type=str,
                    help='The configuration file (IPR only)')

#----------------------------------------
# Generic initialization
#
# Number of cached tiles (per process) in the geo drivers.
num_cached_tiles = 32

# Configure the geo drivers to avoid swap
drive.ConfigureTerrainDriver(cache_size=num_cached_tiles)
drive.ConfigureNlcdDriver(cache_size=num_cached_tiles)




#------------------------------
# Define simulation parameters
# - DPA to simulate
dpa_name = 'East7'

# - Number of sites to distribute within a given range of the DPA
num_sites = 100
max_dist_cat_a = 160
max_dist_cat_b = 320

# - Number of protection points in DPA per category.
# We divide the DPA in 4 buckets: front and back contour, front and back zone
# The front and back are separeted by the us border with some buffering.
# Note:  Keep a ratio as expected in final to get accurate timing estimate
npts_front_dpa_contour = 50    # The mainland facing contour
npts_back_dpa_contour = 20     # The back contour
npts_within_dpa_front = 20     # The front zone
npts_within_dpa_back = 10       # The back zone
front_usborder_buffer_km = 40   # Front contour defined by the extension of the
                                # us border.

# - Do we restrict the sites to be within the census-defined urban areas ?
do_inside_urban_area = True

# - Ratio of cat B and different catA
ratio_cat_b = 0.2
ratio_cat_a_indoor = 0.4

# - Internal parameters
num_montecarlo_iter = 2000
fmin, fmax = 3560, 3570
ratio_cat_a_outdoor = 1.0 - ratio_cat_b - ratio_cat_a_indoor


def ReadConfigFile(config_file):
  """Reads the input config file in json format.

  This routine supports for now the IPR7 config files.

  Returns:
    A tuple (dpa, grants) where:
      dpa:  an object of type |dpa_mgr.Dpa|
      grants: a list of |data.CbsdGrantInfo|
  """
  with open(config_file, 'r') as fd:
    data = json.load(fd)
  if 'portalDpa' in data:
    margin_db = data['portalDpa']['movelistMargin']
    freq_range_mhz = [data['portalDpa']['frequencyRange']['lowFrequency'],
                      data['portalDpa']['frequencyRange']['highFrequency']]
    dpa_id = data['portalDpa']['dpaId']
    dpa_points_kml_file = data['dpaDatabaseConfig']['filePath']


def DpaSimulate(config_file, options):
  """Performs the DPA simulation."""

  if options.seed is not None:
    # reset the random seed
    np.random.seed(options.seed)

  # Configure the global pool of processes
  mpool.Configure(num_processes)
  num_workers = mpool.GetNumWorkerProcesses()

  # Read the input config file
  dpa, grants = ReadConfigFile(config_file)

  ....

  (all_cbsds, reg_requests, grant_requests, protection_zone,
   (n_a_indoor, n_a_outdoor, n_b), ax) = PrepareSimulation()

  # Build the grants
  grants = data.getGrantsFromRequests(reg_requests, grant_requests)

  # Build the DPA manager
  dpa = dpa_mgr.BuildDpa(dpa_name,
                         'default (%d,%d,%d,%d,%d)' % (
                             npts_front_dpa_contour,
                             npts_back_dpa_contour,
                             npts_within_dpa_front,
                             npts_within_dpa_back,
                             front_usborder_buffer_km))
  dpa.ResetFreqRange([(fmin, fmax)])

  # Plot the protection points
  ax.scatter([pt.longitude for pt in dpa.protected_points],
             [pt.latitude for pt in dpa.protected_points],
             color='k', marker='*')
  plt.show(block=False)

  # Run the move list algorithm a first time to fill up geo cache
  print 'Running Move List algorithm (%d workers)' % num_workers
  print '  + once to populate the terrain cache (small run)'
  dpa.SetGrantsFromList(grants[0:50])
  dpa.ComputeMoveLists()

  # Run it for real and measure time
  print '  + actual run (timed)'
  dpa.SetGrantsFromList(grants)
  start_time = time.time()
  dpa.ComputeMoveLists()
  end_time = time.time()

  # Print results
  print 'Move List mask:'
  print dpa.GetMoveListMask((fmin, fmax))
  len_move_list = len(dpa.move_lists[0])
  print ''
  print 'Num Cores (Parallelization): %d' % num_workers
  print 'Num Protection Points: %d' % len(dpa.protected_points)
  print 'Num CBSD: %d (A: %d %d - B %d)' % (
      len(grants), n_a_indoor, n_a_outdoor, n_b)
  print 'Distribution: %s' % ('uniform' if not do_inside_urban_area
                              else 'urban areas only')
  print 'Move list size: %d' % len_move_list
  print 'Computation time: %.1fs' % (end_time - start_time)

  # Check tiles cache well behaved
  print  ''
  tile_stats = mpool.RunOnEachWorkerProcess(getTileStats)
  num_active_tiles, cnt_per_tile = tile_stats[0]
  if not num_active_tiles:
    print '-- Cache ERROR: No active tiles read'
  elif max(cnt_per_tile) > 1:
    print '-- Cache WARNING: cache tile too small - tiles are swapping from cache.'
    pool = mpool.Pool()
    pool.apply_async(printTileStats)
  else:
    print '-- Cache tile: OK (no swapping)'

  # Plot the move list
  if len_move_list:
    result = dpa.GetMoveListMask((fmin, fmax))
    ax.scatter([cbsd.longitude for k, cbsd in enumerate(all_cbsds) if result[k]],
               [cbsd.latitude for k, cbsd in enumerate(all_cbsds) if result[k]],
               color='r', marker='.')
  plt.show()


#----------------------------------------
# Preparing all simulation parameters
def PrepareSimulation():
  # Read the DPA zone
  print 'Preparing Zones'
  dpa_zone = zones.GetCoastalDpaZones()[dpa_name]
  dpa_geometry = dpa_zone.geometry
  us_border = zones.GetUsBorder()
  urban_areas = zones.GetUrbanAreas() if do_inside_urban_area else None
  protection_zone = zones.GetCoastalProtectionZone()

  # Distribute random CBSD of various types around the FSS.
  print 'Distributing random CBSDs in DPA neighborhood'
  # - Find the zone where to distribute the CBSDs
  typical_lat = dpa_geometry.centroid.y
  km_per_lon_deg = 111. * np.cos(typical_lat * np.pi / 180)
  extend_cata_deg = max_dist_cat_a / km_per_lon_deg
  extend_catb_deg = max_dist_cat_b / km_per_lon_deg

  zone_cata = dpa_geometry.buffer(extend_cata_deg).intersection(us_border)
  zone_catb = dpa_geometry.buffer(extend_catb_deg).intersection(us_border)

  if urban_areas is not None:
    # simplify the huge urban_areas for quicker inclusion tests
    urban_areas = urban_areas.intersection(zone_catb)

  # - Distribute the CBSDs
  print ' - Cat A indoor'
  cbsds_cat_a_indoor = entities.GenerateCbsdsInPolygon(
      num_sites * ratio_cat_a_indoor,
      entities.CBSD_TEMPLATE_CAT_A_INDOOR,
      zone_cata,
      drive.nlcd_driver,
      urban_areas)
  print ' - Cat A outdoor'
  cbsds_cat_a_outdoor = entities.GenerateCbsdsInPolygon(
      num_sites * ratio_cat_a_outdoor,
      entities.CBSD_TEMPLATE_CAT_A_OUTDOOR,
      zone_cata,
      drive.nlcd_driver,
      urban_areas)
  print ' - Cat B'
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

  # Plot on screen the elements of calculation
  ax = plt.axes(projection=ccrs.PlateCarree())
  margin = 0.1
  box = zone_catb.union(dpa_geometry)
  ax.axis([box.bounds[0]-margin, box.bounds[2]+margin,
           box.bounds[1]-margin, box.bounds[3]+margin])
  ax.coastlines()
  ax.stock_img()
  ax.plot(*dpa_geometry.exterior.xy, color='r')
  ax.plot(*zone_cata.exterior.xy, color='b', linestyle='--')
  ax.plot(*zone_catb.exterior.xy, color='g', linestyle='--')
  ax.plot(*protection_zone[0].exterior.xy, color='m', linestyle=':')
  ax.plot(*protection_zone[1].exterior.xy, color='m', linestyle=':')
  ax.scatter([cbsd.longitude for cbsd in all_cbsds],
             [cbsd.latitude for cbsd in all_cbsds],
             color='g', marker='.')
  ax.set_title('DPA: %s' % dpa_name)
  plt.show(block=False)

  return (all_cbsds,
          reg_requests,
          grant_requests,
          protection_zone,
          (len(cbsds_cat_a_indoor), len(cbsds_cat_a_outdoor), len(cbsds_cat_b)),
          ax)

# Useful functions
def getTileStats():
  return drive.terrain_driver.stats.ActiveTilesCount()

def printTileStats():
  drive.terrain_driver.stats.Report()

#--------------------------------------------------
# The simulation
if __name__ == '__main__':
  options = parser.parse_args()
  print 'Running DPA simulator'
  DpaSimulate(args.config_file, options)
