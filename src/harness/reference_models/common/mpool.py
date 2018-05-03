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
  """A dummy pool for replacement of concurrent.futures.ProcessPoolExecutor."""
  _max_workers = 1
  def map(self, fn, iterable, chunksize=None):
    return map(fn, iterable)

  def submit(self, fn, *args, **kwargs):
    class Result(object):
      def __init__(self, result):
        self._result = result
      def result(self):
        return self._result
      def done(self):
        return True
      def running(self):
        return False
      def cancel(self):
        return False
      def cancelled(self):
        return False

    future = Result(fn(*args, **kwargs))
    return future


# The global pool
_pool = _DummyPool()

# Number of processes in current pool
_num_processes = 0

# External interface
def Pool():
  return _pool

def Configure(num_processes=-1, pool=None):
  """Configure multiprocessing pool.

  WARNING: do not call this function in the code executed by the child
  processes. For example do it in a function only reachable by the parent process,
  or inside a block `if __name__ == '__main__':`.

  Args:
    num_processes: The number of processes to use for the calculation, limited to the
      maximum number of cpus available.
      If -1, use half of the cpus. If -2, use all the cpus.
      Only used when `pool` not specified.
    pool: An optional multiprocessing |Pool|. If not specified, a pool will be
      automatically created with `num_processes`.
  """
  global _pool
  global _num_processes
  if pool is not None:
    _pool = pool
  else:
    num_cpus = multiprocessing.cpu_count()
    if num_processes == -1:
      num_processes = num_cpus / 2
    elif num_processes < 0:
      num_processes = num_cpus
    if num_processes > num_cpus:
      num_processes = num_cpus
    if pool is None or num_processes != _num_processes:
      _pool = multiprocessing.Pool(processes=num_processes)
      _num_processes = num_processes
