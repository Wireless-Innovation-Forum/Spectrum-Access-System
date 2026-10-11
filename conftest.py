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

"""Keep local unit tests distinct from tests requiring production geo tiles."""

import pytest


PRODUCTION_DATA_TESTS = {
    ('dpa_mgr_test.py', 'test_cbsdInsideDpaInMoveList'),
    ('dpa_mgr_test.py', 'test_cbsdInsideDpaInMoveList_Rel1Ext'),
    ('dpa_mgr_test.py', 'test_computeMoveListAndCheckInterf'),
    ('dpa_mgr_test.py', 'test_computeMoveListAndCheckInterf_Rel1Ext'),
    ('ppa_test.py', 'test_ClippedPpaByCountyWithSmallHoles'),
    ('fss_purge_test.py', 'test_fss_purge_default'),
}


def pytest_addoption(parser):
  parser.addoption('--with-production-data', action='store_true',
                   help='Run tests using configured production NED/NLCD tiles')


def pytest_collection_modifyitems(config, items):
  if config.getoption('--with-production-data'):
    return
  skip = pytest.mark.skip(reason='requires production NED/NLCD tiles; '
                                 'use --with-production-data after configuration')
  for item in items:
    if (item.path.name, item.name) in PRODUCTION_DATA_TESTS:
      item.add_marker(skip)
