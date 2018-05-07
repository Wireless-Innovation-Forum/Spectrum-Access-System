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
import logging
import sys
import unittest

from reference_models.common import mpool


logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        '[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


if __name__ == '__main__':
  # Configure the multiprocessing worker pool.
  # Your options are:
  #   0: single process (default if not called)
  #  -1: use half of the cpus
  #  -2: use all cpus (minus one)
  #  a specific number of cpus
  # Or your own `pool`.
  mpool.Configure(num_processes=-2)

  # Run the tests
  tests = unittest.TestLoader().discover('testcases', '*_testcase.py')
  unittest.TextTestRunner(verbosity=2).run(tests)
