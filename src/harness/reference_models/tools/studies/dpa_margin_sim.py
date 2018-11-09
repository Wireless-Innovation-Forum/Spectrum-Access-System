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
the pass/fail criteria of the test harness. Because it looks at worst case, the
SAS UUT is assumed to be a ref_model-like move list algorithm providing the
smallest move list (ie the most optimal one). The 'ref model' move list can be
chosen to be the biggest move list (default), the median size move list or a
composite move list obtained by taking the intersection of N move lists.

Usage:
  python time_dpa.py <--option1 val1>  <--option2 val2>  config.json
where: config.json is an IPR config file

Notes on modeling capabilties:
-----------------------------
By default will use the exact configuration of the json file for DPA. However
this can be overriden using some options:
  --dpa <dpa_name>: specify an alternative DPA to use from the standard E-DPA/P-DPA.
  --dpa_builder <"default(18,0,0,0,0)">: an alternative protected points builder.
   Required if using --dpa option
  --dpa_builder_uut <"default(25,0,0,0,0)">: an alternative builder for UUT only.
   This is to further simulate a different UUT implementation using different
   protected points.

Example on provided config:
  python dpa_margin_sim.py  --num_process=3 --num_ml 20 --dpa West14  \
                            --dpa_builder "default(18,0,0,0)" data/ipr7_1kCBSDs.config

Other parameters:
-----------------
  --seed <1234>: to specify a random seed.
  --num_ml <10>: number of internal move list to compute for variability analysing,
    both for reference and UUT. Can be individually overriden for uut
    with --num_uut_ml. Note that the UUT movelist is
  --ref_ml_method <number>: for the method used to generate the reference move list:
      'max': use the max move list
      'med' or 'median': use the median move list
      'inter' or 'intersect': use the intersection of move lists (NIST method)
  --ref_ml_num: number of move list to consider in above method.

Misc notes:
-----------
  - multiprocessing facility not tested on Windows. Use single process if experiencing
    issues: `-num_process 1`.
  - if warning reported on cached tiles swapping, increase the cache size with
    option `--size_tile_cache XX`.
"""

import argparse
import copy
import logging
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

from reference_models.common import mpool
from reference_models.dpa import dpa_mgr
from reference_models.dpa import dpa_builder
from reference_models.geo import zones
from reference_models.tools import sim_utils

# Utility functions
Db2Lin = dpa_mgr.Db2Lin
Lin2Db = dpa_mgr.Lin2Db

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
parser.add_argument('--num_uut_ml', type=int, default=0,
                    help='Number of move list to use for UUT.'
                    ' Optional: if unset uses num_ml instead')
parser.add_argument('--dpa', type=str, default='',
                    help='Optional: override DPA to consider. Needs to specify '
                    'also the --dpa_builder')
parser.add_argument('--dpa_builder', type=str, default='',
                    help='Optional: override DPA builder to use '
                    'for generating DPA protected points. See BuildDpa().')
parser.add_argument('--dpa_builder_uut', type=str, default='',
                    help='Optional: override DPA builder to use '
                    'for generating DPA protected points for UUT.')
parser.add_argument('--ref_ml_method', type=str, default='max',
                    help='Method of reference move list: '
                    '`max`: max size move list, `med`: median size move list, '
                    '`inter`: intersection of move lists')
parser.add_argument('--ref_ml_num', type=int, default=0,
                    help='Number of move list to use in method.'
                    '0 means all, otherwise the specified number.')
parser.add_argument('--margin_db', type=str, default='',
                    help='Optional: override `movelistMargin`, for ex:`linear(1.5)`.')
parser.add_argument('--log_level', type=str, default='info',
                    help='Logging level: debug, info, warning, error.')
parser.add_argument('--do_extensive', action='store_true',
                    help='Do extensive aggregate interference analysis. '
                    'By checking all possible ref move list')
parser.add_argument('config_file', type=str,
                    help='The configuration file (IPR only)')
# Example for a boolean flag:
#parser.add_argument('--do_something', action='store_true', help='An option.')

_LOGGER_MAP = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

def SyntheticMoveList(ml_list, method, num, chan_idx):
  """Gets a synthetic move list from a list of them according to some criteria.

  See options `ref_ml_method` and `ref_ml_num`.
  """
  if num == 0: num = len(ml_list)
  ml_size = [len(ml[chan_idx]) for ml in ml_list]
  if method.startswith('med'):
    # Median method (median size keep list)
    median_idx = ml_size.index(np.percentile(ml_size[:num], 50,
                                             interpolation='nearest'))
    ref_ml = ml_list[median_idx]
  elif method.startswith('max'):
    # Max method (bigger move list, ie smallest keep list).
    max_idx = np.argmax(ml_size[:num])
    ref_ml = ml_list[max_idx]
  elif method.startswith('min'):
    # Min method (smaller move list, ie bigger keep list).
    min_idx = np.argmin(ml_size[:num])
    ref_ml = ml_list[min_idx]
  elif method.startswith('int'):
    # Intersection method (similar to method of Michael Souryal - NIST).
    # One difference is that we do not remove xx% of extrema.
    ref_ml = []
    for chan in xrange(len(ml_list[0])):
      ref_ml.append(set.intersection(*[ml_list[k][chan]
                                       for k in xrange(num)]))
  else:
    raise ValueError('Ref ML method %d unsupported' % method)
  return ref_ml


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
  if dpas is None:
    if not options.dpa:
      raise ValueError('Config file not defining a DPA and no --dpa option used.')
    dpa = dpa_mgr.Dpa(None)
    dpa.margin_db = 1.5
  else:
    dpa = dpas[0]

  # Apply the DPA modifications (DPA, builders)
  if options.dpa:  # Override with new DPA.
    margin_db = dpa.margin_db
    if not options.dpa_builder:
      raise ValueError('Missing the --dpa_builder specification.')
    dpa = dpa_mgr.BuildDpa(options.dpa, options.dpa_builder)
    try: dpa_geometry = zones.GetCoastalDpaZones()[options.dpa]
    except KeyError: dpa_geometry = zones.GetPortalDpaZones()[options.dpa]
    dpa.geometry = dpa_geometry.geometry
    dpa.margin_db = margin_db
  elif options.dpa_builder:  # Override the points_builder
    dpa.protection_points = dpa_builder.DpaProtectionPoints(
        dpa.name, dpa.geometry, options.dpa_builder)

  if options.margin_db:  # Override `movelistMargin` directive.
    try: dpa.margin_db = float(options.margin_db)
    except ValueError: dpa.margin_db = options.margin_db

  print ('Simulation with DPA `%s` (ref: %d pts):\n'
         '  %d granted CBSDs: %d CatB - %d CatA_out - %d CatA_in' % (
         dpa.name, len(dpa.protected_points),
         len(grants),
         len([grant for grant in grants if grant.cbsd_category == 'B']),
         len([grant for grant in grants
              if grant.cbsd_category == 'A' and not grant.indoor_deployment]),
         len([grant for grant in grants
              if grant.cbsd_category == 'A' and grant.indoor_deployment]))
  )

  # Plot the entities.
  ax = sim_utils.CreateCbrsPlot(grants, dpa=dpa)

  # Set the grants into DPA.
  dpa.SetGrantsFromList(grants)

  # Manages the number of move list
  num_ref_ml = options.num_ml
  num_uut_ml = options.num_uut_ml or options.num_ml
  # Run the move list N times on ref DPA
  print 'Running Move List algorithm (%d workers): %d times' % (
      num_workers, num_ref_ml)
  start_time = time.time()
  ref_move_list_runs = []  # Save the move list of each run
  num_base_ml = (num_ref_ml if options.dpa_builder_uut
                 else max(num_ref_ml, num_uut_ml))
  for k in xrange(num_base_ml):
    dpa.ComputeMoveLists()
    ref_move_list_runs.append(copy.copy(dpa.move_lists))
    sys.stdout.write('.')

  # Plot the last move list on map.
  for channel in dpa._channels:
    move_list = dpa.GetMoveList(channel)
    sim_utils.PlotGrants(ax, move_list, color='r')

  # Now build the UUT dpa and move lists
  dpa_uut = copy.copy(dpa)
  uut_move_list_runs = ref_move_list_runs[:num_uut_ml]
  if options.dpa_builder_uut:
    dpa_uut.protection_points = dpa_builder.DpaProtectionPoints(
        dpa_uut.name, dpa_uut.geometry, options.dpa_builder_uut)
    # If UUT has its own parameters, simulate it by running it,
    # otherwise reuse the move lists of the ref model.
    uut_move_list_runs = []
    for k in xrange(options.num_uut_ml):
      dpa_uut.ComputeMoveLists()
      uut_move_list_runs.append(copy.copy(dpa_uut.move_lists))
      sys.stdout.write('+')

  print '\n   Computation time: %.1fs' % (time.time() - start_time)
  ref_move_list_runs = ref_move_list_runs[:num_ref_ml]

  # Analyse the move_list aggregate interference margin:
  #  - find a good channel to check: the one with maximum CBSDs.
  chan_idx = np.argmax([len(dpa.GetNeighborList(chan)) for chan in dpa._channels])
  channel = dpa._channels[chan_idx]
  # - plot the move list sizes histogram for that channel.
  ref_ml_size = [len(move_list[chan_idx]) for move_list in ref_move_list_runs]
  plt.figure()
  plt.hist(ref_ml_size)
  plt.grid(True)
  plt.xlabel('Count')
  plt.ylabel('')
  plt.title('Histogram of move list size across %d runs' % options.num_ml)

  # Analyze aggregate interference. By default:
  #   + uut: taking smallest move list (ie bigger keep list)
  #   + ref: taking biggest move list (ie smallest keep list)
  #      or  taking a median or intersection move list
  # Hopefully (!) this is a good proxy for worst case scenarios.
  #
  #  - enable log level - usually 'info' allows concise report.
  logging.getLogger().setLevel(_LOGGER_MAP[options.log_level])
  # - The ref case first
  dpa.move_lists = SyntheticMoveList(ref_move_list_runs,
                                     options.ref_ml_method, options.ref_ml_num, chan_idx)

  # - The UUT case
  dpa_uut.move_lists = SyntheticMoveList(uut_move_list_runs, 'min', 0, chan_idx)
  uut_keep_list = dpa_uut.GetKeepList(channel)

  start_time = time.time()
  print '*****  CHECK INTERFERENCE size ref_ML=%d vs %d *****' % (
      len(dpa.move_lists[chan_idx]), len(dpa_uut.move_lists[chan_idx]))

  success = dpa.CheckInterference(uut_keep_list, dpa.margin_db, channel=channel,
                                  extensive_print=True)
  print '   Computation time: %.1fs' % (time.time() - start_time)

  # Extensive mode
  if options.do_extensive:
    logging.getLogger().setLevel(logging.ERROR)
    num_success = 0
    ref_levels = []
    diff_levels = []
    print '*****  EXTENSIVE CHECK/SCATTER *****'
    start_time = time.time()
    num_synth_ml = 1 if not options.ref_ml_num else options.ref_ml_num
    num_check = len(ref_move_list_runs) - num_synth_ml + 1
    for k in xrange(num_check):
      dpa.move_lists = SyntheticMoveList(ref_move_list_runs[k:],
                                         options.ref_ml_method, options.ref_ml_num,
                                         chan_idx)
      interf_results = []
      num_success += dpa.CheckInterference(uut_keep_list, dpa.margin_db, channel=channel,
                                           extensive_print=False,
                                           output_data=interf_results)
      for pt_res in interf_results:
        ref_levels.extend(pt_res.A_DPA_ref)
        diff_levels.extend(pt_res.A_DPA - pt_res.A_DPA_ref)

    ref_levels, diff_levels = np.asarray(ref_levels), np.asarray(diff_levels)
    print '   Computation time: %.1fs' % (time.time() - start_time)
    print 'Extensive Interference Check:  %d success / %d (%.3f%%)' % (
        num_success, len(ref_move_list_runs),
        (100. * num_success) / len(ref_move_list_runs))
    # Find the maximum variation in mw
    max_diff_mw = np.max(Db2Lin(ref_levels + diff_levels) - Db2Lin(ref_levels))
    max_margin_db = Lin2Db(max_diff_mw + Db2Lin(dpa.threshold)) - dpa.threshold
    print 'Max difference: %g mw ==> %.3fdB' % (max_diff_mw, max_margin_db)
    # Plot the scatter plot
    plt.figure()
    plt.grid(True)
    plt.title('Aggregate interference difference - DPA: %s' % dpa.name)
    plt.xlabel('Reference aggregate interference (dBm/10MHz)')
    plt.ylabel('SAS UUT difference (dB)')
    plt.scatter(ref_levels, diff_levels, c = 'r', marker='.', s=10)
    margin_mw = Db2Lin(dpa.threshold + 1.5) - Db2Lin(dpa.threshold)
    x_data = np.arange(min(ref_levels), max(ref_levels), 0.01)
    plt.plot(x_data, Lin2Db(Db2Lin(x_data) + margin_mw) - x_data, 'b',
             label='Fixed Linear Margin @1.5dB')
    plt.plot(x_data, Lin2Db(Db2Lin(x_data) + max_diff_mw) - x_data, 'g',
             label='Fixed Linear Margin @%.3fdB' % max_margin_db)
    plt.legend()

  # Simulation finalization
  print ''
  sim_utils.CheckTerrainTileCacheOk()  # Cache analysis and report


#--------------------------------------------------
# The simulation
if __name__ == '__main__':
  options = parser.parse_args()
  print 'Running DPA simulator'
  DpaSimulate(options.config_file, options)
  plt.show(block=True)
