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

"""A collection of utility routines for simulation purposes.
"""
import copy
import json

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as sgeo

from reference_models.common import data
from reference_models.common import mpool
from reference_models.dpa import dpa_mgr
from reference_models.geo import drive
from reference_models.geo import zones

#----------------------------------------
# Generic plotting routines (in cartopy).
def PlotDpa(ax, dpa, color='m'):
  """Plots a DPA contour and protected points.

  Args:
    ax: A matplotlib `axes`.
    dpa: A |dpa_mgr.Dpa| DPA.
    color: A matplotlib color.
  """
  if hasattr(dpa, 'geometry') and not isinstance(dpa.geometry, sgeo.Point):
    ax.plot(*dpa.geometry.exterior.xy, color='m')
  ax.scatter([pt.longitude for pt in dpa.protected_points],
             [pt.latitude for pt in dpa.protected_points],
             color='b', marker='x', s=20)

def PlotGrants(ax, grants, color='r'):
  """Plots CBSD in move list.
  Args:
    ax: A matplotlib `axes`.
    grants: An iterable of |data.CbsdGrantInfo| grants.
    color: A matplotlib color.
  """
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


# TODO(sbdt): add other kind of entities (PPA, ..). For now only DPAs.
def CreateCbrsPlot(grants, dpa=None):
  """Plots the grants in a map along with other entities (DPA, ..).

  Args:
    grants: An iterable of |CbsdGrantInfo| grants.
    dpa: A |dpa_mgr.Dpa|  DPA.

  Returns:
    ax: the 'matplotlib.axes' object
  """
  ax = plt.axes(projection=ccrs.PlateCarree())
  # Finds the bounding box of all geometries (DPA and CBSDs).
  box = sgeo.box(*sgeo.MultiPoint(
    [(grant.longitude, grant.latitude) for grant in grants]).bounds)
  if hasattr(dpa, 'geometry'):
    box = sgeo.box(*box.union(dpa.geometry).bounds)
  elif dpa is not None:
    box = sgeo.box(*box.union([(pt.longitude, pt.latitude)
                               for pt in dpa.protected_points]).bounds)
  box_margin = 0.1 # about 10km
  box = box.buffer(box_margin)
  # Plot geometries.
  ax.axis([box.bounds[0], box.bounds[2], box.bounds[1], box.bounds[3]])
  ax.coastlines()
  ax.stock_img()
  PlotGrants(ax, grants, color='g')
  if dpa is not None:
    PlotDpa(ax, dpa, color='m')
  ax.set_title('DPA: %s' % dpa.name)
  plt.show(block=False)
  return ax

#----------------------------------------------
# Useful misc functions about environment.

# Configure the environment
def ConfigureRunningEnv(num_process, size_tile_cache):
  """Configures the running environment.

  Optimal performance is obtained by increasing the number of process
  and a geo cache big enough to avoid swapping. Each tile covers about
  100kmx100km. Swapping statistics can be obtaines using the routine:
    `CheckTerrainTileCacheOk()`.

  Args:
    num_process: Number of process. Special values: -1: #cpu/2 ; -2: #cpu-1
    size_tile_cache: Geo cache size in number of tiles. The memory usage is
      about: `num_process * size_tile_cache * 60 MB`
  """
  # Configure the geo drivers to avoid swap
  drive.ConfigureTerrainDriver(cache_size=size_tile_cache)
  drive.ConfigureNlcdDriver(cache_size=size_tile_cache)

  # Configure the global pool of processes
  mpool.Configure(num_process)
  return mpool.GetNumWorkerProcesses()


# Analysis of the terrain cache swap.
def _getTileStats():
  return drive.terrain_driver.stats.ActiveTilesCount()

def _printTileStats():
  drive.terrain_driver.stats.Report()

def CheckTerrainTileCacheOk():
  """Check tiles cache well behaved."""
  print  'Check of tile cache swap:'
  tile_stats = mpool.RunOnEachWorkerProcess(_getTileStats)
  num_active_tiles, cnt_per_tile = tile_stats[np.argmax([tile_stat[0]
                                                        for tile_stat in tile_stats])]
  if not num_active_tiles:
    print '-- Cache ERROR: No active tiles read'
  elif max(cnt_per_tile) > 1:
    print '-- Cache WARNING: cache tile too small - tiles are swapping from cache.'
    pool = mpool.Pool()
    pool.apply_async(_printTileStats)
  else:
    print '-- Cache tile: OK (no swapping)'


#----------------------------------------
# Utility routines to read test harness config files into proper ref model objects.
def MergeConditionalData(registration_requests, conditional_datas):
  """Returns copy of registration_requests with merged conditional datas."""
  cond_data_map = {cond['cbsdSerialNumber']: cond
                   for cond in conditional_datas}
  reg_requests = copy.deepcopy(registration_requests)
  for reg_request in reg_requests:
    cbsd_serial_number = reg_request['cbsdSerialNumber']
    if cbsd_serial_number in cond_data_map:
      reg_request.update(cond_data_map[cbsd_serial_number])
  return reg_requests


def ReadTestHarnessConfigFile(config_file):
  """Reads the input config file in json format and build ref_model entities.

  WARNING: This routine supports for now only the IPR7 config files, building
  the CBSDs and DPAs. Will be extended in the future for others.

  Note that the returned DPAs have additional non standard properties:
    - geometry: the original |shapely| geometry.
    - margin_db: the margin for interference check (in dB).

  Args:
    config_file: The path to a json config file as used by test harness.
       Currently only IPR7 supported.

  Returns:
    A tuple (dpas, grants) where:
      dpas:  a list of objects of type |dpa_mgr.Dpa|.
      grants: a list of |data.CbsdGrantInfo|.
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

  return grants, [dpa]
