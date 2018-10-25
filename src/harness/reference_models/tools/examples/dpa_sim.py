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

import argparse
import copy
import logging
import time

import matplotlib.pyplot as plt
import numpy as np

from reference_models.tools import sim_utils

#----------------------------------------
# Setup the command line arguments
parser = argparse.ArgumentParser(description='DPA Simulator')
parser.add_argument('--seed', type=int, help='Random seed.')
parser.add_argument('--num_process', type=int, default=-1,
                    help='Number of parallel process. -2=all-1, -1=50%.')
parser.add_argument('--size_tile_cache', type=int, default=32,
                    help='Number of parallel process. -2=all-1, -1=50%.')
parser.add_argument('--num_ml', type=int, default=2,
                    help='Number of move list to compute.')
parser.add_argument('--dpa_builder', type=str, default='',
                    help='Optional DPA builder to override the configuration'
                    'DPA protected points. See BuildDpa().')
parser.add_argument('--log_level', type=str, default='warning',
                    help='Logging level: debug, info, warning, error.')
#parser.add_argument('--option', action='store_true', help='An option.')
parser.add_argument('config_file', type=str,
                    help='The configuration file (IPR only)')

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
  if options.dpa_builder:
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
  print '\nMove list Computation time: %.1fs' % (end_time - start_time)

  # Plot the last move list
  for channel in dpa._channels:
    move_list = dpa.GetMoveList(channel)
    sim_utils.PlotGrants(ax, move_list, color='r')

  # Analyse the move_list aggregate interference margin
  logging.getLogger().setLevel(_LOGGER_MAP[options.log_level])
  #  - find a good channel to check: the one with maximum CBSDs
  chan_idx = np.argmax([len(dpa.GetNeighborList(chan)) for chan in dpa._channels])
  channel = dpa._channels[chan_idx]

  #  - gets and plots the move lists size.
  ml_size = [len(move_list[chan_idx]) for move_list in move_list_runs]
  plt.figure()
  plt.hist(ml_size)
  plt.grid('on')
  plt.xlabel('Count')
  plt.ylabel('')
  plt.title('Histogram of move list size across %d runs' % options.num_ml)

  # - analyze aggregate interference for worst case (hopefully):
  #   + taking the biggest move list (ie smallest keep list) as the reference
  #   + spanning in turn the other move lists as UUT move list
  ref_ml = move_list_runs[np.argmax(ml_size)]
  dpa.move_list = ref_ml
  start_time = time.time()
  for ml in move_list_runs:
    uut_keep_list = dpa.GetNeighborList(channel).difference(ml[chan_idx])
    success = dpa.CheckInterference(uut_keep_list, dpa.margin_db, channel=channel)
  end_time = time.time()
  print 'Check Interf Computation time: %.1fs' % (end_time - start_time)

  # Finalization
  sim_utils.CheckTerrainTileCacheOk()

#--------------------------------------------------
# The simulation
if __name__ == '__main__':
  options = parser.parse_args()
  import sys # test
  print sys.argv
  print 'Running DPA simulator'
  DpaSimulate(options.config_file, options)
  plt.show()
