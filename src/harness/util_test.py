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
"""Tests for the util.py."""

import unittest
import mock

import util


class UtilTest(unittest.TestCase):

  def test_getFqdnLocalhost(self):
    # Initialize the testConfig with our test data.
    util._initTestConfig()
    util._test_config.hostname = 'foo.bar.com'

    self.assertEqual(util.getFqdnLocalhost(), 'foo.bar.com')

  def test_getUnusedPort_pickAny(self):
    # Initialize the testConfig with our test data.
    util._initTestConfig()
    util._test_config.min_port = -1
    util._test_config.min_port = -1

    self.assertGreater(util.getUnusedPort(), 0)

  def test_getUnusedPort_pickRange(self):
    # Initialize the testConfig with our test data.
    util._initTestConfig()
    # Note that the could failed if these port are already in use...
    START_PORT = 12345
    util._test_config.min_port = START_PORT
    util._test_config.max_port = START_PORT + 5

    self.assertEqual(util.getUnusedPort(), START_PORT)
    self.assertEqual(util.getUnusedPort(), START_PORT + 1)
    self.assertEqual(util.getUnusedPort(), START_PORT + 2)
    self.assertEqual(util.getUnusedPort(), START_PORT + 3)
    self.assertEqual(util.getUnusedPort(), START_PORT + 4)
    with self.assertRaises(AssertionError):
      util.getUnusedPort()

    util.releasePort(START_PORT + 2)
    self.assertEqual(util.getUnusedPort(), START_PORT + 2)
    with self.assertRaises(AssertionError):
      util.getUnusedPort()
