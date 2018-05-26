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

"""Multiprocessing pool with profiling abilities.

Standard program profiling can usually be done with:
  python -m cProfile -s cumulative <your_script.py>
However this profiles only the main process. To profile
each worker thread this module provides a drop-in replacement
of a multiprocessibf pool with profiling enabled.

This is to be used only during code analys and dev as it
introduces running overhead.

Usage:
  # Create a special pool with profiler enabled
  pool = profpool.PoolWithProfiler(processes=4)

  # Configure the test harness mpool manager
  mpool.Configure(pool=pool)

  ... run the test cases to profile ...

  # Dump the profile output
  pool.dump_stats()

  # To print the profiling data
  import pstats
  p = pstats.Stats('profile-<pid>.stats')
  p.sort_stats('cumulative')
  p.print_stats(20) # 20 most significant lines
"""

import cProfile
import os
import multiprocessing

# The profiler object
_prof = None

def _process_profile_init():
  """Initialize the process profiler."""
  global _prof
  _prof = cProfile.Profile()


class _FnRunnerWithProfiler(object):
  """A functor to run a function within profiler."""
  def __init__(self, fn):
    self.fn = fn
  def __call__(self, arg):
    _prof.enable()
    res = self.fn(arg)
    _prof.disable()
    return res


def _dump_stats(idx):
  """Dumps the stats."""
  _prof.dump_stats('profile-%s.out' % idx)


class PoolWithProfiler(object):
  """A multiprocessing pool with profiling on each worker."""
  def __init__(self, processes):
    self.pool = multiprocessing.Pool(processes=processes,
                                     initializer=_process_profile_init)
    self.num_processes = processes

  def map(self, fn, iterable, chunksize=None):
    return self.pool.map(_FnRunnerWithProfiler(fn), iterable, chunksize=chunksize)

  def apply_async(self, fn, args=(), kwds={}, callback=None):
    return self.pool.apply_async(_FnRunnerWithProfiler(fn), args, kwds)

  def dump_stats(self):
    self.pool.map(_dump_stats, range(1, self.num_processes+1), chunksize=1)
