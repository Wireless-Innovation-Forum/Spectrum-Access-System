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
""" CBSD Registration User Part """

import json
import os
import unittest
import cbsd_sas as sas


class TestRegistration(unittest.TestCase):
    """ CBSD - SAS Registration Test Suite """

    # Set-up and Tear-down

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        # self._sas_admin.Reset()

    def tearDown(self):
        pass

    # Test Cases

    def test_10_3_4_1_1_1(self):
        self._sas.logger.info(
            '10.3.4.1.1.1 New Multi-Step registration for CBSD Cat A '
            '(No existing CBSD ID)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'device1_a.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])


if __name__ == '__main__':
    unittest.main()
