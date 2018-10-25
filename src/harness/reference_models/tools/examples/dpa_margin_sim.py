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
import copy
import json
import time

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as sgeo

from reference_models.common import mpool
from reference_models.tools import sim_utils

#----------------------------------------
# Setup the command line arguments
parser = argparse.ArgumentParser(description='DPA Simulator')
parser.add_argument('--seed', type=int, default=12, help='Random seed.')
parser.add_argument('--num_process', type=int, default=-1,
                    help='Number of parallel process. -2=all-1, -1=50%.')
parser.add_argument('--size_tile_cache', type=int, default=32,
                    help='Number of parallel process. -2=all-1, -1=50%.')
parser.add_argument('--num_ml', type=int, default=10,
                    help='Number of move list to compute.')
parser.add_argument('--dpa', type=str, default='',
                    help='Optional: override DPA to consider. ')
parser.add_argument('--dpa_builder', type=str, default='',
                    help='Optional: override DPA builder to use '
                    'for generating DPA protected points. See BuildDpa().')
parser.add_argument('--log_level', type=str, default='info',
                    help='Logging level: debug, info, warning, error.')
parser.add_argument('config_file', type=str,
                    help='The configuration file (IPR only)')
# Example for a boolean flag:
#parser.add_argument('--do_something', action='store_true', help='An option.')

#----------------------------------------
# Generic DPA-related plotting routines
def PlotDpa(ax, dpa, color='m'):
  if hasattr(dpa, 'geometry') and not isinstance(dpa.geometry, sgeo.Point):
    ax.plot(*dpa.geometry.exterior.xy, color='m')
  ax.scatter([pt.longitude for pt in dpa.protected_points],
             [pt.latitude for pt in dpa.protected_points],
             color='b', marker='x', s=20)

def PlotGrants(ax, grants, color='r'):
  """Plots CBSD in move list."""
  if not len(grants):
    return
  xy = ([grant.longitude for grant in grants if grant.cbsd_category=='B'],
        [grant.latitude for grant in grants if grant.cbsd_category=='B'])
  if len(xy[0]):
    ax.scatter(*xy, c=color, marker='1', s=20)
  xy = ([grant.longitude for grant in grants if grant.cbsd_category=='A'],
        [grant.latitude for grant in grants if grant.cbsd_category=='A'])
  if len(xy[0]):
    ax.scatter(*xy, c=color, marker='.', s=20)


def PlotDpaObjects(dpa, grants):
  """Plots the DPA and grants in a map.

  Returns:
    ax: the 'matplotlib.axes' object
  """
  ax = plt.axes(projection=ccrs.PlateCarree())
  # Finds the bounding box of all geometries (DPA and CBSDs).
  box = sgeo.box(*sgeo.MultiPoint(
    [(grant.longitude, grant.latitude) for grant in grants]).bounds)
  if hasattr(dpa, 'geometry'):
    box = sgeo.box(*box.union(dpa.geometry).bounds)
  else:
    box = sgeo.box(*box.union([(pt.longitude, pt.latitude)
                               for pt in dpa.protected_points]).bounds)
  box_margin = 0.1 # about 10km
  box = box.buffer(box_margin)
  # Plot geometries.
  ax.axis([box.bounds[0], box.bounds[2], box.bounds[1], box.bounds[3]])
  ax.coastlines()
  ax.stock_img()
  PlotGrants(ax, grants, color='g')
  PlotDpa(ax, dpa, color='m')
  ax.set_title('DPA: %s' % dpa.name)
  plt.show(block=False)
  return ax

#----------------------------------------
# Utility routines to read config files into proper ref model objects.
def MergeConditionalData(registration_requests, conditional_datas):
  """Returns registration_requests with merged conditional datas."""
  cond_data_map = {cond['cbsdSerialNumber']: cond
                   for cond in conditional_datas}
  reg_requests = copy.deepcopy(registration_requests)
  for reg_request in reg_requests:
    cbsd_serial_number = reg_request['cbsdSerialNumber']
    if cbsd_serial_number in cond_data_map:
      reg_request.update(cond_data_map[cbsd_serial_number])
  return reg_requests

def ReadConfigFileForDpaAndCbsds(config_file):
  """Reads the input config file in json format and build DPAs/Cbsds.

  This routine supports for now the IPR7 config files.

  Note that the returned DPAs have additional properties:
    - geometry: the original |shapely| geometry.
    - margin_db: the margin for interference check (in dB).
  Returns:
    A tuple (dpas, grants) where:
      dpas:  a list of objects of type |dpa_mgr.Dpa|
      grants: a list of |data.CbsdGrantInfo|
  """
  with open(config_file, 'r') as fd:
    config = json.load(fd)
  # Reads the DPA info.
  if 'portalDpa' in config:
    dpa_tag = 'portalDpa'
  elif 'escDpa' in config:
    dpa_tag = 'escDpa'
  else:
    raise ValueError('Unsupported config file. Please use a IPR7 config file')

  # Build the DPA
  dpa_id = config[dpa_tag]['dpaId']
  try: dpa_kml_file = config['dpaDatabaseConfig']['filePath']
  except KeyError: dpa_kml_file = None
  points_builder = config[dpa_tag]['points_builder']
  dpa = dpa_mgr.BuildDpa(dpa_id, protection_points_method=points_builder,
                         portal_dpa_filename=dpa_kml_file)
  freq_range_mhz = (config[dpa_tag]['frequencyRange']['lowFrequency'] / 1.e6,
                    config[dpa_tag]['frequencyRange']['highFrequency'] / 1.e6)
  dpa.ResetFreqRange([freq_range_mhz])
  # - add extra properties for the geometry and margin
  dpa.margin_db = config[dpa_tag]['movelistMargin']
  try: dpa_zone = zones.GetCoastalDpaZones()[dpa_id]
  except KeyError: dpa_zone = zones.GetPortalDpaZones(kml_path=dpa_kml_file)[dpa_id]
  dpa.geometry = dpa_zone.geometry

  # Read the CBSDs, assuming all granted, into list of |CbsdGrantInfo|.
  grants = []
  #  - first the SAS UUT
  for domain_proxy_config in config['domainProxies']:
    grant_requests = domain_proxy_config['grantRequests']
    reg_requests = MergeConditionalData(domain_proxy_config['registrationRequests'],
                                        domain_proxy_config['conditionalRegistrationData'])
    grants.extend(data.getGrantsFromRequests(reg_requests, grant_requests,
                                             is_managing_sas=True))
  #  - now the peer SASes.
  for th_config in config['sasTestHarnessConfigs']:
    dump_records = th_config['fullActivityDumpRecords'][0]
    grants.extend(data.getAllGrantInfoFromCbsdDataDump(
        dump_records, is_managing_sas=False))

  return [dpa], grants

#-----------------------------------------------------
# DPA aggregate interference variation simulator
def DpaSimulate(config_file, options):
  """Performs the DPA simulation."""
  if options.seed is not None:
    # reset the random seed
    np.random.seed(options.seed)

  logging.getLogger().setLevel(logging.WARNING)
  num_workers = sim_utils.ConfigureRunningEnv(num_process=options.num_process,
                                              size_tile_cache=options.size_tile_cache)

  # Read the input config file into ref model entities.
  grants, dpas = sim_utils.ReadTestHarnessConfigFile(config_file)
  dpa = dpas[0]
  if options.dpa:  # Override with new DPA.
    dpa = dpa_mgr.BuildDpa(options.dpa)
  if options.dpa_builder:  # Override the points_builder
    dpa.protection_points = dpa_builder.DpaProtectionPoints(
        dpa.name, dpa.geometry, options.builder)
  print ('Simulation with DPA `%s` (%d points):\n'
         '  %d granted CBSDs: %d CatB - %d CatA_out - %d CatA_in' % (
         dpa.name, len(dpa.protected_points), len(grants),
         len([grant for grant in grants if grant.cbsd_category == 'B']),
         len([grant for grant in grants
              if grant.cbsd_category == 'A' and not grant.indoor_deployment]),
         len([grant for grant in grants
              if grant.cbsd_category == 'A' and grant.indoor_deployment]))
  )

  # Plot the entities.
  ax = sim_utils.CreateCbrsPlot(grants, dpa=dpa)

  # Run the move list N times
  print 'Running Move List algorithm (%d workers): %d times' % (num_workers,
                                                                options.num_ml)
  dpa.SetGrantsFromList(grants)
  start_time = time.time()
  move_list_runs = []  # Save the move list of each run
  for k in xrange(options.num_ml):
    dpa.ComputeMoveLists()
    move_list_runs.append(copy.copy(dpa.move_lists))
  end_time = time.time()

  # Plot the last move list
  for channel in dpa._channels:
    move_list = dpa.GetMoveList(channel)
    PlotGrants(ax, move_list, color='r')

  # Analyse the move_list aggregate interference margin
  #  - find a good channel to check: the one with maximum CBSDs
  chan_idx = np.argmax([len(dpa.GetNeighborList(chan)) for chan in dpa._channels])
  channel = dpa._channels[chan_idx]

  #  - gets and plots the move lists size.
  ml_size = [len(move_list[chan_idx]) for move_list in move_list_runs]
  plt.figure()
  plt.hist(ml_size)
  plt.grid(True)
  plt.xlabel('Count')
  plt.ylabel('')
  plt.title('Histogram of move list size across %d runs' % options.num_ml)

  # - analyze aggregate interference:
  #   + ref: taking biggest move list (ie smallest keep list)
  #   + uut: taking smallest move list (ie bigger keep list)
  # Hopefully (!) this is a good proxy for worst case scenarios.
  max_ml_idx = np.argmax(ml_size)
  ref_ml = move_list_runs[max_ml_idx]  # smallest keep list
  dpa.move_lists = ref_ml
  min_ml_idx = np.argmin(ml_size)
  uut_ml = move_list_runs[min_ml_idx]  # largest keep list
  uut_keep_list = dpa.GetNeighborList(channel).difference(uut_ml[chan_idx])
  start_time = time.time()
  print '*****  CHECK INTERFERENCE ML=%d vs %d (size: %d vs %d) *****' % (
      max_ml_idx, min_ml_idx, ml_size[max_ml_idx], ml_size[min_ml_idx])

  success = dpa.CheckInterference(uut_keep_list, dpa.margin_db, channel=channel)
  end_time = time.time()
  print 'Check Interf Computation time: %.1fs' % (end_time - start_time)

  # Finalization
  print 'Computation time: %.1fs' % (end_time - start_time)
  CheckTileCacheOk()

#----------------------------------------------
# Useful functions
def getTileStats():
  return drive.terrain_driver.stats.ActiveTilesCount()

def printTileStats():
  drive.terrain_driver.stats.Report()

def CheckTileCacheOk():
  """Check tiles cache well behaved."""
  print  '\nCheck of tile cache swap:'
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




#--------------------------------------------------
# The simulation
if __name__ == '__main__':
  options = parser.parse_args()
  print 'Running DPA simulator'
  DpaSimulate(options.config_file, options)
