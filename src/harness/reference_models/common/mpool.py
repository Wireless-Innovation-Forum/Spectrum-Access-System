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

"""Multiprocessing pool manager.

Managing pool in one place avoids issue of either:
 - pool being issued locally in a function and loosing its context
   across repeated function calls.
 - centralize management of common shared memory

Usage:

import mpool
# Configure the pool
mpool.Configure(-1)


# Gets the number of worker processes
num_workers = mpool.GetNumWorkerProcesses()

# Apply a function on all workers
mpool.RunOnEachWorkerProcess(fn, 3, arg2=4)

# Use the multiprocessing worker pool
pool = mpool.Pool()
pool.map(...)
pool.apply_async(...)
"""
# NOTE: This has been tested in Linux only.
# Windows has some special way of launching processes, not using fork(),
# but rather by instantiating new processes and reimporting the
# modules. Make sure that the code creating the processes is not
# actually called during the imports, ie:
#  - within the if __name__ == 'main': block
#  - in a function that is not executed at time of import or within
#    the routines delegated to workers.

from functools import partial
import multiprocessing
import time

class _DummyPool(object):
  """A dummy pool for replacement of `multiprocessing.Pool`

  Using single process. Implements `map` and `apply_async`.
  """
  _max_workers = 1
  def map(self, fn, iterable, chunksize=None):
    return map(fn, iterable)

  def apply_async(self, fn, args=(), kwds={}, callback=None):
    class Result(object):
      def __init__(self, result):
        self._result = result
      def get(self, timeout):
        return self._result
      def wait(self, timeout):
        return
      def ready(self):
        return True
      def successful(self):
        return True
    result = Result(fn(*args, **kwargs))
    if callback is not None:
      callback(result.get())
    return result

  def close(self):
    return
  def join(self):
    return

# The global pool
_pool = _DummyPool()

# Number of workers in current pool
_num_workers = 0

# External interface
def Pool():
  """Returns the worker pool.

  It supports routines:
    map()
    apply_async()
  And other `multiprocessing.Pool` routines if not a dummy pool.
  """
  return _pool


def GetNumWorkerProcesses():
  """Returns the number of worker processes."""
  return _num_workers


def _partial_fn(fn):
  # sleep to avoid returning too fast so each worker
  # gets one job in the RunOnEachWorkerProcess.
  time.sleep(0.5)
  return fn()


def RunOnEachWorkerProcess(fn, * args, **kwargs):
  """Runs a function on each of the pool process."""
  if not _num_workers:
    return
  pfn = partial(fn, *args, **kwargs)
  return _pool.map(_partial_fn, [pfn] * _num_workers, chunksize=1)


def Configure(num_processes=-1, pool=None):
  """Configure multiprocessing pool.

  WARNING: do not call this function in the code executed by the workers.
  For example do it in a function only reachable by the parent process,
  or inside a block `if __name__ == '__main__':`.

  Args:
    num_processes: The number of worker processes to use for the calculation,
      limited to the maximum number of cpus available. Special values:
         0: use no multiprocessing (dummy pool).
        -1: use half of the cpus
        -2: use all the available cpus (minus one).
      Only used when `pool` not specified.
    pool: An optional multiprocessing |Pool|. If not specified, a pool will be
      automatically created with `num_processes`.
  """
  global _pool
  global _num_workers
  if pool is not None:
    _pool = pool
  else:
    # Dummy pool with no multiprocessing
    if num_processes == 0:
      _pool = _DummyPool()
      _num_workers = 0
      return
    # Actual multiprocessing pool of workers
    num_cpus = multiprocessing.cpu_count()
    if num_processes == -1:
      num_processes = num_cpus / 2
    elif num_processes < 0:
      # Always reserve 1 for other things (multiprocessing Manager for ex)
      num_processes = num_cpus - 1
    if num_processes > num_cpus:
      num_processes = num_cpus
    if num_processes <= 1:
      _pool = _DummyPool()
      _num_workers = 0
      return
    # Instantiate the pool if it has changed.
    if pool is None or num_processes != _num_workers:
      _pool = multiprocessing.Pool(processes=num_processes)
      _num_workers = num_processes
