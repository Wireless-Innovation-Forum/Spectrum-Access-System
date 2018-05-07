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
# Configure the pool
pool.Configure(-1)

# Use the multiprocessing pool
pool = mpool.Pool()
pool.map(...)

"""
# TODO(sbdt): review behavior in multiple platforms.

import multiprocessing


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

# Number of processes in current pool
_num_processes = 0

# External interface
def Pool():
  """Returns the worker pool.

  It supports routines:
    map()
    apply_async()
  And other `multiprocessing.Pool` routines if not a dummy pool.
  """
  return _pool

def Configure(num_processes=-1, pool=None):
  """Configure multiprocessing pool.

  WARNING: do not call this function in the code executed by the child
  processes. For example do it in a function only reachable by the parent process,
  or inside a block `if __name__ == '__main__':`.

  Args:
    num_processes: The number of processes to use for the calculation,
      limited to the maximum number of cpus available. Special values:
         0: use no multiprocessing (dummy pool).
        -1: use half of the cpus
        -2: use all the available cpus (minus one).
      Only used when `pool` not specified.
    pool: An optional multiprocessing |Pool|. If not specified, a pool will be
      automatically created with `num_processes`.
  """
  global _pool
  global _num_processes
  if pool is not None:
    _pool = pool
  else:
    # Dummy pool with no multiprocessing
    if num_processes == 0:
      _pool = _DummyPool()
      _num_processes = 0
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
    if pool is None or num_processes != _num_processes:
      _pool = multiprocessing.Pool(processes=num_processes)
      _num_processes = num_processes
