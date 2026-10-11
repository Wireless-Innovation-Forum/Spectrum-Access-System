#    Copyright 2026 SAS Project Authors. All Rights Reserved.
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

"""Regression tests for driver setup in spawn and forkserver workers."""

import multiprocessing
import os
import time
import unittest

from reference_models.common import mpool


def _delayed_worker_start():
  # Force an uneven startup so the first worker could consume both tasks if
  # RunOnEachWorkerProcess relied on a fixed sleep for task distribution.
  if multiprocessing.current_process()._identity[-1] % 2 == 0:
    time.sleep(2)


def _configure_drivers(terrain_dir, landcover_dir):
  from reference_models.geo import drive
  drive.ConfigureTerrainDriver(terrain_dir=terrain_dir, cache_size=3)
  drive.ConfigureNlcdDriver(nlcd_dir=landcover_dir, cache_size=2)
  return os.getpid()


def _read_driver_configuration():
  from reference_models.geo import drive
  return (os.getpid(), drive.terrain_driver._terrain_dir,
          drive.nlcd_driver._nlcd_dir, drive.terrain_driver.cache_size,
          drive.nlcd_driver.cache_size)


def _add(first, second=0):
  return first + second


class TestMpool(unittest.TestCase):

  def tearDown(self):
    pool = mpool.Pool()
    if not isinstance(pool, mpool._DummyPool):
      pool.terminate()
      pool.join()
    mpool.Configure(num_processes=0)

  def test_dummy_async_arguments_and_callback(self):
    mpool.Configure(num_processes=0)
    callbacks = []
    result = mpool.Pool().apply_async(
        _add, args=(3,), kwds={'second': 4}, callback=callbacks.append)
    self.assertEqual(result.get(), 7)
    self.assertEqual(callbacks, [7])
    self.assertIsNone(result.wait())
    self.assertTrue(result.ready())
    self.assertTrue(result.successful())

  def _assert_workers_configured(self, context):
    mpool.Configure(pool=context.Pool(processes=2,
                                     initializer=_delayed_worker_start))
    self.assertEqual(mpool.GetNumWorkerProcesses(), 2)
    configured_pids = mpool.RunOnEachWorkerProcess(
        _configure_drivers, '/test/terrain', '/test/landcover')
    self.assertEqual(len(set(configured_pids)), 2)
    results = mpool.RunOnEachWorkerProcess(_read_driver_configuration)
    self.assertEqual(set(row[0] for row in results), set(configured_pids))
    for _, terrain_dir, landcover_dir, terrain_cache, landcover_cache in results:
      self.assertEqual((terrain_dir, landcover_dir, terrain_cache, landcover_cache),
                       ('/test/terrain', '/test/landcover', 3, 2))

  def test_spawn_worker_driver_configuration(self):
    self._assert_workers_configured(multiprocessing.get_context('spawn'))

  @unittest.skipUnless('forkserver' in multiprocessing.get_all_start_methods(),
                       'forkserver is unavailable on this platform')
  def test_forkserver_worker_driver_configuration(self):
    self._assert_workers_configured(multiprocessing.get_context('forkserver'))


if __name__ == '__main__':
  unittest.main()
