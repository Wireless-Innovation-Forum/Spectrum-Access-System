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
import csv
import json

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.stats
import shapely.geometry as sgeo
import zipfile

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
    ax.scatter(*xy, c=color, marker='1', s=10)
  xy = ([grant.longitude for grant in grants if grant.cbsd_category=='A'],
        [grant.latitude for grant in grants if grant.cbsd_category=='A'])
  if len(xy[0]):
    ax.scatter(*xy, c=color, marker='.', s=10)


# TODO(sbdt): add other kind of entities (PPA, ..). For now only DPAs.
def CreateCbrsPlot(grants, dpa=None, tag='', color='g',
                   subplot=None, fig=None):
  """Plots the grants in a map along with other entities (DPA, ..).

  Args:
    grants: An iterable of |CbsdGrantInfo| grants.
    dpa: A |dpa_mgr.Dpa|  DPA.

  Returns:
    ax: the 'matplotlib.axes' object
  """
  if not fig:
    fig = plt.figure()
  if not subplot:
    subplot = 111
  ax = fig.add_subplot(subplot, projection=ccrs.PlateCarree())
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
  PlotGrants(ax, grants, color=color)
  if dpa is not None:
    PlotDpa(ax, dpa, color='m')
  ax.set_title('%sDPA: %s' % (tag, dpa.name))
  return ax, fig

#----------------------------------------------
# Useful statistical routines
# Estimate PDF form a set of random samples
#  - using a Smooth kernel estimator
def GetPDFEstimator(s, bw_method=None):
  """Gets a PDF estimator, using gaussian kernel method.

  Args:
    s: The signal samples.
    bw_method: The kernel method to use. See: scipy.stats.gaussian_kde()
  Returns:
    A tuple (x, f(x)) where x is the sample space and f(x) the PDF
    (probability distribution function).
  """
  s_min = np.min(s)
  s_max = np.max(s)
  r = np.linspace(s_min, s_max, 100)
  kde = scipy.stats.gaussian_kde(s, bw_method=bw_method)
  return (r, kde(r))


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
  # Configure the global pool of processes
  mpool.Configure(num_process)

  # Configure the geo drivers to avoid swap
  # - for main process
  drive.ConfigureTerrainDriver(cache_size=size_tile_cache)
  drive.ConfigureNlcdDriver(cache_size=size_tile_cache)
  # - for worker processes
  mpool.RunOnEachWorkerProcess(drive.ConfigureTerrainDriver,
                               terrain_dir=None, cache_size=size_tile_cache)
  mpool.RunOnEachWorkerProcess(drive.ConfigureNlcdDriver,
                               nlcd_dir=None, cache_size=size_tile_cache)
  return mpool.GetNumWorkerProcesses()

# Analysis of the terrain cache swap.
def _getTileStats():
  return drive.terrain_driver.stats.ActiveTilesCount()

def _printTileStats():
  drive.terrain_driver.stats.Report()

def CheckTerrainTileCacheOk():
  """Check tiles cache well behaved."""
  print('Check of tile cache swap:')
  num_workers = mpool.GetNumWorkerProcesses()
  if num_workers:
    tile_stats = mpool.RunOnEachWorkerProcess(_getTileStats)
  else:
    tile_stats = [_getTileStats()]
  num_active_tiles, cnt_per_tile = tile_stats[np.argmax([tile_stat[0]
                                                        for tile_stat in tile_stats])]
  if not num_active_tiles:
    print('-- Cache ERROR: No active tiles read')
  elif max(cnt_per_tile) > 1:
    print('-- Cache WARNING: cache tile too small - tiles are swapping from cache.')
    if num_workers:
      pool = mpool.Pool()
      pool.apply_async(_printTileStats)
    else:
      _printTileStats()
  else:
    print('-- Cache tile: OK (no swapping)')


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


def _IprConfigRead(config):
  """Extracts DPA and grants from IPR config JSON.

  Note: All IPT suppprted except IPR1.

  Args:
    config: A JSON dictionary.

  Returns:
    A tuple (dpas, grants) where:
      dpas:  a list of objects of type |dpa_mgr.Dpa|.
      grants: a list of |data.CbsdGrantInfo|.
  """
  dpa_cfgs = None
  if 'portalDpa' in config:
    dpa_cfgs = [config['portalDpa']]
  elif 'escDpa' in config:
    dpa_cfgs = [config['escDpa']]
  if dpa_cfgs is None:
    if 'dpas' in config:
      dpa_cfgs = config['dpas']
    elif 'dpa' in config:
      dpa_cfgs = [config['dpa']]
  if dpa_cfgs is None or (
      'domainProxies' not in config and 'registrationRequest' not in config):
    raise ValueError('Unsupported config file. Please use a IPR config file')

  # Build the DPAs
  dpas = []
  for dpa_cfg in dpa_cfgs:
    dpa_id = dpa_cfg['dpaId']
    try: dpa_kml_file = config['dpaDatabaseConfig']['filePath']
    except KeyError: dpa_kml_file = None
    try: points_builder = dpa_cfg['points_builder']
    except KeyError: points_builder = None
    try:
      dpa = dpa_mgr.BuildDpa(dpa_id, protection_points_method=points_builder,
                             portal_dpa_filename=dpa_kml_file)
    except IOError:
      print('Portal KML File not found: %s ' % dpa_kml_file)
      raise
    try:
      freq_range_mhz = (dpa_cfg['frequencyRange']['lowFrequency'] / 1.e6,
                        dpa_cfg['frequencyRange']['highFrequency'] / 1.e6)
      dpa.ResetFreqRange([freq_range_mhz])
    except KeyError:
      pass
    # - add extra properties for the geometry and margin
    try: dpa.margin_db = dpa_cfg['movelistMargin']
    except KeyError: dpa_margin_db = 'linear(1.5)'
    try: dpa_zone = zones.GetCoastalDpaZones()[dpa_id]
    except KeyError: dpa_zone = zones.GetPortalDpaZones(kml_path=dpa_kml_file)[dpa_id]
    dpa.geometry = dpa_zone.geometry
    dpas.append(dpa)

  # Read the CBSDs, assuming all granted, into list of |CbsdGrantInfo|.
  grants = []
  if 'domainProxies' in config:
    #  - first the SAS UUT
    for domain_proxy_config in config['domainProxies']:
      grant_requests = domain_proxy_config['grantRequests']
      reg_requests = MergeConditionalData(domain_proxy_config['registrationRequests'],
                                          domain_proxy_config['conditionalRegistrationData'])
      grants.extend(data.getGrantsFromRequests(reg_requests, grant_requests,
                                               is_managing_sas=True))
    #  - now the peer SASes.
    if 'sasTestHarnessConfigs' in config:
      for th_config in config['sasTestHarnessConfigs']:
        dump_records = th_config['fullActivityDumpRecords'][0]
        grants.extend(data.getAllGrantInfoFromCbsdDataDump(
            dump_records, is_managing_sas=False))

  elif 'registrationRequest' in config:
    grants.extend(data.getGrantsFromRequests(
        MergeConditionalData([config['registrationRequest']],
                             [config['conditionalRegistrationData']]),
        [config['grantRequest']],
        is_managing_sas=True))

  return grants, dpas


def _McpConfigRead(config):
  """Extracts DPA and grants from MCP config JSON.

  Note: returns all grants involved in the test irrespective of iteration
  process.

  Args:
    config: A JSON dictionary.

  Returns:
    A tuple (dpas, grants) where:
      dpas:  a list of objects of type |dpa_mgr.Dpa|.
      grants: a list of |data.CbsdGrantInfo|.
  """
  if ('iterationData' not in config or
      'dpas' not in config or
      'initialCbsdRequestsWithDomainProxies' not in config):
    raise ValueError('Unsupported config file. Please use a MCP1 config file')

  # Build the DPAs.
  dpas = []
  for dpa_id, dpa_data in config['dpas'].items():
    dpa = dpa_mgr.BuildDpa(dpa_id,
                           protection_points_method=dpa_data['points_builder'])
    # - add extra properties for the geometry and margin.
    dpa.margin_db = dpa_data['movelistMargin']
    try: dpa_zone = zones.GetCoastalDpaZones()[dpa_id]
    except KeyError: dpa_zone = zones.GetPortalDpaZones(kml_path=dpa_kml_file)[dpa_id]
    dpa.geometry = dpa_zone.geometry

    # - read also the activation list and freq range.
    dpa.activation = None
    for iter_data in config['iterationData']:
      for activation in iter_data['dpaActivationList']:
        if activation['dpaId'] == dpa_id:
          dpa.activation = activation['frequencyRange']
          break

    dpas.append(dpa)

  # Read the CBSDs, assuming all granted, into list of |CbsdGrantInfo|.
  # - initial stuff into SAS UUT
  grants = []
  for records in config['initialCbsdRequestsWithDomainProxies']:
    grant_requests = records['grantRequests']
    reg_requests = MergeConditionalData(records['registrationRequests'],
                                        records['conditionalRegistrationData'])
    grants.extend(data.getGrantsFromRequests(reg_requests, grant_requests,
                                             is_managing_sas=True))
  for record in config['initialCbsdRecords']:
    grant_request = [record['grantRequest']]
    reg_request = MergeConditionalData([record['registrationRequest']],
                                       [record['conditionalRegistrationData']])
    grants.append(data.getGrantsFromRequests(reg_requests, grant_requests,
                                             is_managing_sas=True))

  # - then iterations for TH and UUT
  for iter_data in config['iterationData']:
    for th_data in iter_data['sasTestHarnessData']:
      th_grants = data.getAllGrantInfoFromCbsdDataDump(
          th_data['cbsdRecords'], is_managing_sas=False)
      grants.extend([g for g in th_grants])

    for records in iter_data['cbsdRequestsWithDomainProxies']:
      grant_requests = records['grantRequests']
      reg_requests = MergeConditionalData(records['registrationRequests'],
                                          records['conditionalRegistrationData'])
      uut_grants = data.getGrantsFromRequests(reg_requests, grant_requests,
                                              is_managing_sas=True)
      grants.extend([g for g in uut_grants])

    for record in iter_data['cbsdRecords']:
      grant_request = [record['grantRequest']]
      reg_request = MergeConditionalData([record['registrationRequest']],
                                         [record['conditionalRegistrationData']])
      uut_grant = data.getGrantsFromRequests(reg_requests, grant_requests,
                                             is_managing_sas=True)
      grants.append(uut_grant)

  return grants, dpas


def _RegGrantsRead(config):
  """Extracts DPA and grants from Reg/Grants config JSON.

  Args:
    config: A JSON dictionary.

  Returns:
    A list of |data.CbsdGrantInfo|.
  """
  grants = [data.constructCbsdGrantInfo(reg_request, grant_request, is_managing_sas=True)
            for reg_request, grant_request in zip(
                config['registrationRequests'], config['grantRequests'])]
  return grants


def ReadTestHarnessConfigFile(config_file):
  """Reads the input config file in json format and build ref_model entities.

  This routine builds the CBSDs and possibly the DPAs (if defined in the config file).
  Currently only IPR7 and reg/grant json file are supported.

  Note that the returned DPAs have additional non standard properties:
    - geometry: the original |shapely| geometry.
    - margin_db: the margin for interference check (in dB).

  Args:
    config_file: The path to a json config file as used by test harness.
      Can be raw or zipped. Currently supported config files are:
       - IPR7 config file
       - reg_grant type file

  Returns:
    A tuple (grants, dpas) where:
      grants: a list of |data.CbsdGrantInfo|.
      dpas:  a list of objects of type |dpa_mgr.Dpa| or None if the confg file
        does not support DPAs.
  """
  # Read input JSON file (even if zipped).
  if config_file.endswith('zip'):
    with zipfile.ZipFile(config_file) as zip:
      file_name = [info.filename for info in zip.infolist()
                   if os.path.splitext(info.filename)[1] == '.json'][0]
      with zip.open(file_name) as fd:
        config = json.load(fd)
  else:
    with open(config_file, 'r') as fd:
      config = json.load(fd)

  # Supports the `reg_grant` raw format (no DPA defined).
  try:
    grants = _RegGrantsRead(config)
    return grants, None
  except Exception:
    pass

  # Supports IPR config format.
  try:
    grants, dpas = _IprConfigRead(config)
    return grants, dpas
  except Exception:
    pass

  # Support MCP1 config format.
  try:
    grants, dpas = _McpConfigRead(config)
    return grants, dpas
  except Exception:
    pass

  raise ValueError('Unsupported config file: %s' % config_file)


def ReadDpaLogFile(csv_file):
  """Reads a set of DPA CSV logs produced by |dpa_mgr.CheckInterference|.

  The log file contains neighbor and keep lists of the SAS UUT and ref model.

  Args:
    csv_file: One of the CSV file of the log set of files. Other related files will
      be read automatically.

  Returns:
    A tuple (nbor_grants, ref_keep_list_grants, uut_keep_list_grants) where:
      nbor_grants: the list of all neighborhood grants |data.CbsdGrantInfo|.
      ref/uut_keep_list_grants: the list of all neighborhood grants within the keep list.
  """
  if not csv_file.endswith('csv'):
    raise ValueError('File should be a valid CSV DPA log file: %s' % csv_file)

  postfixes = {'nbor': '(neighbor list)',
               'peer': '(combined peer SAS keep list)',
               'sas_th': '(SAS UUT keep list, according to test harness)',
               'sas_uut': '(SAS UUT keep list, according to SAS UUT)'}
  idx_postfix = max(csv_file.find(postfix) for postfix in postfixes.values())
  base_file = csv_file[:idx_postfix]
  # Now read every file and build corresponding grant list
  grants = {}
  for key, postfix in postfixes.items():
    grants[key] = []
    with open(base_file + postfix + '.csv') as fd:
      csv_reader = csv.DictReader(fd, delimiter=',')
      for row in csv_reader:
        grants[key].append(data.CbsdGrantInfo(
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            height_agl=float(row['height_agl']),
            indoor_deployment=(row['indoor_deployment']=='True'),
            cbsd_category=row['cbsd_category'],
            antenna_azimuth=float(row['antenna_azimuth']),
            antenna_gain=float(row['antenna_gain']),
            antenna_beamwidth=float(row['antenna_beamwidth']),
            max_eirp=float(row['max_eirp']),
            low_frequency=float(row['low_frequency']),
            high_frequency=float(row['high_frequency']),
            is_managed_grant=(row['is_managed_grant'] == 'True')))
  return grants['nbor'], grants['peer'] + grants['sas_th'], grants['sas_uut']
