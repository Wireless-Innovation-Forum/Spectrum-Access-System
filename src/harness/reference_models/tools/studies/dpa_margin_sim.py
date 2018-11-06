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
SAS UUT is assumed to be a ref_model-like move list algorithm providing the smallest
move list (ie the most optimal one). The 'ref model' move list can be chosen to be
the biggest move list (default), the median size move list or a composite move list
obtained by taking the intersection of xx%


Usage:
  python time_dpa.py <--option1 val1>  <--option2 val2>  config.json
where: config.json is an IPR config file

Notes on modeling capabilties:
-----------------------------
By default will use the exact configuration of the json file for DPA. However this
can be overriden using some options:
  --dpa <dpa_name>: specify an alternative DPA to use from the standard E-DPA/P-DPA.
  --dpa_builder <"default(18,0,0,0,0)">: an alternative protected points builder.
   Required if using --dpa option
  --dpa_builder_uut <"default(25,0,0,0,0)">: an alternative builder for UUT only. This is to
    further simulate a different UUT implementation using different protected points.

Example on provided config:
  python dpa_margin_sim.py  --num_process=3 --num_ml 20 --dpa West14  \
                            --dpa_builder "default(18,0,0,0)" data/ipr7_1kCBSDs.config

Other parameters:
-----------------
  --seed <1234>: to specify a random seed.
  --num_ml <10>: number of internal move list to compute for variability analysing.
  --ref_ml_method <number>: for the method used to generate the reference move list:
      0 (default): the biggest move list (ie smallest keep list)  - worst case
     -1: one median size move list
     xx>0: an intersection move list made by using the [xx%;100-xx%] move list (NIST
           Michael Souryal method).

Misc notes:
-----------
  - multiprocessing facility not tested on Windows (use 1 process if issues) using
    otion `--num_process 1`.
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
                    help='Optional: override DPA to consider. Needs to specify '
                    'also the --dpa_builder')
parser.add_argument('--dpa_builder', type=str, default='',
                    help='Optional: override DPA builder to use '
                    'for generating DPA protected points. See BuildDpa().')
parser.add_argument('--dpa_builder_uut', type=str, default='',
                    help='Optional: override DPA builder to use '
                    'for generating DPA protected points for UUT.')
parser.add_argument('--ref_ml_method', type=int, default=-1,
                    help='Method of reference move list: '
                    '-1=max size, -2:median size, >0: intersection [xx%-100-xx%]')
parser.add_argument('--log_level', type=str, default='info',
                    help='Logging level: debug, info, warning, error.')
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

  # Run the move list N times on ref DPA
  print 'Running Move List algorithm (%d workers): %d times' % (
      num_workers, options.num_ml)
  start_time = time.time()
  ref_move_list_runs = []  # Save the move list of each run
  for k in xrange(options.num_ml):
    dpa.ComputeMoveLists()
    ref_move_list_runs.append(copy.copy(dpa.move_lists))
    sys.stdout.write('.')
  end_time = time.time()

  # Plot the last move list on map.
  for channel in dpa._channels:
    move_list = dpa.GetMoveList(channel)
    sim_utils.PlotGrants(ax, move_list, color='r')

  # Now build the UUT dpa and move lists
  dpa_uut = copy.copy(dpa)
  uut_has_diff_points = False
  if options.dpa_builder_uut:
    dpa_uut.protection_points = dpa_builder.DpaProtectionPoints(
        dpa_uut.name, dpa_uut.geometry, options.dpa_builder_uut)
    uut_has_diff_points = True

  # If UUT has its own parameters, simulate it by running it,
  # otherwise reuse the move lists of the ref model.
  uut_move_list_runs = ref_move_list_runs
  if uut_has_diff_points:
    uut_move_list_runs = []
    for k in xrange(options.num_ml):  # Should we use a smaller number
      dpa_uut.ComputeMoveLists()
      uut_move_list_runs.append(copy.copy(dpa_uut.move_lists))
      sys.stdout.write('+')

  print '\nMove list Computation time: %.1fs' % (end_time - start_time)

  # Analyse the move_list aggregate interference margin:
  #  - enable log level - usually 'info' allows concise report.
  logging.getLogger().setLevel(_LOGGER_MAP[options.log_level])
  #  - find a good channel to check: the one with maximum CBSDs.
  chan_idx = np.argmax([len(dpa.GetNeighborList(chan)) for chan in dpa._channels])
  channel = dpa._channels[chan_idx]
  # - find the move list sizes for that channel.
  ref_ml_size = [len(move_list[chan_idx]) for move_list in ref_move_list_runs]
  uut_ml_size = [len(move_list[chan_idx]) for move_list in uut_move_list_runs]

  # Plots the move lists size histogram.
  plt.figure()
  ml_size = ref_ml_size[:]
  if uut_has_diff_points:
    ml_size.extend(uut_ml_size)
  plt.hist(ml_size)
  plt.grid(True)
  plt.xlabel('Count')
  plt.ylabel('')
  plt.title('Histogram of move list size across %d runs' % options.num_ml)

  # Analyze aggregate interference. By default:
  #   + ref: taking biggest move list (ie smallest keep list)
  #      or  taking a median or intersection move list
  #   + uut: taking smallest move list (ie bigger keep list)
  # Hopefully (!) this is a good proxy for worst case scenarios.
  #
  # - The ref case first
  if options.ref_ml_method == -1:
    max_idx = np.argmax(ref_ml_size)
    ref_ml = ref_move_list_runs[max_idx]  # = smallest keep list
  elif options.ref_ml_method == -2:
    medan_idx = ref_ml_size.index(np.percentile(ref_ml_size, 50, interpolation='nearest'))
    ref_ml = ref_move_list_runs[median_idx]  # = median size keep list
  else:
    # Intersection method of NTIA (Michael Souryal)
    # To be done
    raise ValueError('Unsupported method for now')
  dpa.move_lists = ref_ml

  # - The ref case first
  uut_ml = uut_move_list_runs[np.argmin(uut_ml_size)]  # = largest keep list
  dpa_uut.move_lists = uut_ml
  uut_keep_list = dpa_uut.GetKeepList(channel)

  start_time = time.time()
  print '*****  CHECK INTERFERENCE size ref_ML=%d vs %d *****' % (
      len(dpa.move_lists[chan_idx]), len(dpa_uut.move_lists[chan_idx]))

  success = dpa.CheckInterference(uut_keep_list, dpa.margin_db, channel=channel)
  end_time = time.time()
  print 'Check Interf Computation time: %.1fs' % (end_time - start_time)

  # Finalization
  sim_utils.CheckTerrainTileCacheOk()


#--------------------------------------------------
# The simulation
if __name__ == '__main__':
  options = parser.parse_args()
  print 'Running DPA simulator'
  DpaSimulate(options.config_file, options)
  plt.show(block=True)
