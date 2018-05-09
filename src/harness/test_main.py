#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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
"""Top main script of the test harness.

If writing your own top level script to run the test harness,
look here how the setup is performed.
It is particularly important to correctly set the geo drivers
and multiprocessing pool for best performance
"""
import logging
import os
import sys
import unittest


from reference_models.common import mpool
from reference_models.geo import drive

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        '[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Multi-processing
# Number of worker processes allocated for heavy duty calculation,
# typically DPA, PPA creation and IAP for PPA/GWPZ.
# Values:
#  -1: Use half of the cpu available
#  -2: Use all available cpu minus one (one process should be reserved for
#      the IAP shared objects manager process).
#  Other: the number of process to allocate
NUM_PROCESSES = -2

# Memory allocation management
# A simple strategy is proposed by default, knowing the test harness usage:
#   - NLCD only used for PPA and GWPZ for deriving the Land Cover. Area size
#     is limited in general. LandCover extraction is done in main thread only
#     (except for PPA tests where worker processes check the CBSD landcover)
#     ==> Allocate most of the cache to main processes
#   - NED used by all others, with heavy terrain profile reading by the main
#     and worker threads.
#     ==> Allocate equal memory to worker processes, and twice to main process
# This strategy could be tuned for best performance.
#
# A 2 level cache could also be used (with memmap or otherwise) in order to share
# most of the in-memory tiles across processes. Not implemented.
#

# The memory allocated for geo cache across all sub-processes (in MB).
#  -1: automatic allocation
#  otherwise this number (in MB) is used for setting up the cache size
MEM_ALLOCATION_GEO_CACHE_MB = -1
# When 'automatic allocation', the ratio of total physical memory
# dedicated to the geo cache
RATIO_MEM_FOR_GEO_CACHE = 0.7
# The factor of the main process vs worker processes. Use > 0.
RATIO_MASTER_WORKER = 2


def GetAvailableMemoryMb():
  """Returns the available physical memory."""
  import psutil
  return int(psutil.virtual_memory().total / 1e6)

def GetGeoAllocatedMemory():
  """Returns the memory available for Geo cache."""
  if MEM_ALLOCATION_GEO_CACHE_MB > 0:
    return MEM_ALLOCATION_GEO_CACHE_MB
  else:
    return GetAvailableMemoryMb() * RATIO_MEM_FOR_GEO_CACHE


if __name__ == '__main__':
  # Configure the multiprocessing worker pool.
  # Your options are:
  #   0: single process (default if not called)
  #  -1: use half of the cpus
  #  -2: use all cpus (minus one)
  #  a specific number of cpus
  # Or your own `pool`.
  mpool.Configure(num_processes=NUM_PROCESSES)
  num_workers = mpool.GetNumWorkerProcesses()

  # Configure geo drivers
  geo_mem = GetGeoAllocatedMemory()
  num_ned_work = num_workers + RATIO_MASTER_WORKER
  num_nlcd_work = RATIO_MASTER_WORKER
  ned_tile_mem = 52
  nlcd_tile_mem = 13
  num_tiles = float(geo_mem) / (
      num_ned_work * ned_tile_mem + num_nlcd_work * nlcd_tile_mem)

  # For main process
  drive.ConfigureTerrainDriver(cache_size=RATIO_MASTER_WORKER*num_tiles)
  drive.ConfigureNlcdDriver(cache_size=RATIO_MASTER_WORKER*num_tiles)

  # For worker processes
  # TODO

  # Run the tests
  tests = unittest.TestLoader().discover('testcases', '*_testcase.py')
  unittest.TextTestRunner(verbosity=2).run(tests)
