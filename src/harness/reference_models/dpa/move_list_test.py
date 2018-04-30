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


import os
import unittest
from collections import namedtuple
import numpy as np

from reference_models.examples import testutils
from reference_models.examples import entities
from reference_models.common import data
from reference_models.propagation import wf_itm

from reference_models.dpa import move_list

# A Protection point namedtuple as required by input
ProtectionPoint = namedtuple('ProtectionPoint', ['latitude', 'longitude'])


class TestDpa(unittest.TestCase):

  def setUp(self):
    self.original_itm = wf_itm.CalcItmPropagationLoss

  def tearDown(self):
    wf_itm.CalcItmPropagationLoss = self.original_itm

  def test_movelist_single_grant(self):
    np.random.seed(1248)
    # Configuring for -144dBm circle at 20km
    wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(144+30-0.1) - 20.0)
    point = ProtectionPoint(latitude=36.815, longitude=-76.292)

    # Within the move list
    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_A_OUTDOOR,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=19.97, max_distance_km=19.98),
        min_freq_mhz=3600,
        max_freq_mhz=3610)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3600e6, 3610e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, grants)
    self.assertListEqual(move_grants, grants)

    # Outside the move list
    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_A_OUTDOOR,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=20.1, max_distance_km=20.2),
        min_freq_mhz=3600,
        max_freq_mhz=3610)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3600e6, 3610e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, grants)
    self.assertListEqual(move_grants, [])

  def test_movelist_oob_cata(self):
    np.random.seed(1248)
    # Configuring for -144dBm circle at 20km for OOB power -25dBm
    wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(144+(-25)-0.1) - 20.0)
    point = ProtectionPoint(latitude=36.815, longitude=-76.292)

    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_A_OUTDOOR,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=10, max_distance_km=11),
        min_freq_mhz=3600,
        max_freq_mhz=3610)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3540e6, 3550e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, [])
    self.assertListEqual(move_grants, [])

  def test_movelist_oob_catb(self):
    np.random.seed(1248)
    # Configuring for -144dBm circle at 20km for OOB power -15dBm/10MHz
    wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(144+(-15+8)-0.1) - 20.0)
    point = ProtectionPoint(latitude=36.815, longitude=-76.292)

    # Within move list for power
    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_B_OMNI,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=19.97, max_distance_km=19.98),
        min_freq_mhz=3600,
        max_freq_mhz=3610)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3540e6, 3550e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, grants)
    self.assertListEqual(move_grants, grants)

    # Outside the move list for power
    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_B_OMNI,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=20.1, max_distance_km=20.2),
        min_freq_mhz=3600,
        max_freq_mhz=3610)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3540e6, 3550e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, grants)
    self.assertListEqual(move_grants, [])

    # Outside the nbor list for distance. -144 at 30km
    wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(144+(-15+8)-0.1) - 20.0)

    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_B_OMNI,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=25.1, max_distance_km=25.2),
        min_freq_mhz=3600,
        max_freq_mhz=3610)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3540e6, 3550e6, grants,
        None, 50, 2000, -144, 3)
    self.assertListEqual(nbor_grants, [])
    self.assertListEqual(move_grants, [])

  def test_movelist_oob_purge_catb(self):
    np.random.seed(1248)
    # Configuring for -144dBm circle at 20km for OOB power -3dBm/10MHz
    wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(144+(-13+10+8)-0.1) - 20.0)
    point = ProtectionPoint(latitude=36.815, longitude=-76.292)

    # Within move list for power
    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_B_OMNI,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=19.97, max_distance_km=19.98),
        min_freq_mhz=3550,
        max_freq_mhz=3570,
        chunks_mhz=5)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3540e6, 3550e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, grants)
    self.assertListEqual(move_grants, grants)

    # However only using the last 2 would be out of move list
    grants = grants[2:]
    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3540e6, 3550e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, grants)
    self.assertListEqual(move_grants, [])

    # Slightly lower than the cutoff power -> none in move list
    grants = entities.ConvertToCbsdGrantInfo(
        entities.GenerateCbsdList(
            1, template_cbsd=entities.CBSD_TEMPLATE_CAT_B_OMNI,
            ref_latitude=36.815, ref_longitude=-76.292,
            min_distance_km=20.1, max_distance_km=20.2),
        min_freq_mhz=3550,
        max_freq_mhz=3570,
        chunks_mhz=5)

    move_grants, nbor_grants = move_list.moveListConstraint(
        point, 3540e6, 3550e6, grants,
        None, 50, 2000, -144, 3)

    self.assertListEqual(nbor_grants, grants)
    self.assertListEqual(move_grants, [])


if __name__ == '__main__':
  unittest.main()
