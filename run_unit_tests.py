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

"""Run local SAS tests from their expected working directory.

Use --with-production-data to include the NED/NLCD integration tests. All other
arguments are forwarded to pytest. The actual SAS compliance suite is launched
separately through src/harness/test_main.py.
"""

import os
from pathlib import Path
import subprocess
import sys


def main():
  root = Path(__file__).resolve().parent
  harness = root / 'src' / 'harness'
  paths = [harness, root / 'src' / 'lib', root / 'src' / 'lib' / 'geo',
           root / 'src' / 'lib' / 'usgs_pop']
  env = os.environ.copy()
  env['PYTHONPATH'] = os.pathsep.join(str(path) for path in paths)
  if os.environ.get('PYTHONPATH'):
    env['PYTHONPATH'] += os.pathsep + os.environ['PYTHONPATH']
  tests = [harness, root / 'src' / 'lib' / 'geo',
           harness / 'testcases' / 'helper_unit_testcase.py']
  if '--with-gdal' in sys.argv:
    tests.append(root / 'src' / 'lib' / 'usgs_pop')
  args = [arg for arg in sys.argv[1:] if arg != '--with-gdal']
  return subprocess.call([sys.executable, '-m', 'pytest', '-q',
                          *(str(path) for path in tests), *args],
                         cwd=harness, env=env)


if __name__ == '__main__':
  sys.exit(main())
