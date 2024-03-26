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


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import namedtuple
import json
import os
import shutil
import tempfile
import unittest

import numpy as np
import shapely.geometry as sgeo

from reference_models.common import data
from reference_models.dpa import dpa_mgr
from reference_models.geo import zones
from reference_models.propagation import wf_itm
from reference_models.tools import entities
from reference_models.tools import testutils

TEST_DIR = os.path.join(os.path.dirname(__file__),'test_data')


ProtectionPoint = namedtuple('ProtectionPoint', ['latitude', 'longitude'])

def json_load(fname):
  with open(fname, 'r') as fd:
    return json.load(fd)

class TestDpa(unittest.TestCase):

  def setUp(self):
    self.temp_dir = tempfile.mkdtemp()
    self.orig_dpa_log_dir = dpa_mgr.GetDpaLogDir
    dpa_mgr.GetDpaLogDir = lambda: self.temp_dir

  def tearDown(self):
    dpa_mgr.GetDpaLogDir = self.orig_dpa_log_dir
    shutil.rmtree(self.temp_dir, ignore_errors=True)

  def test_channelization(self):
    channels = dpa_mgr.GetDpaProtectedChannels([(3550, 3650)], is_portal_dpa=False)
    self.assertListEqual(channels, [(f, f+10) for f in range(3550, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3650)], is_portal_dpa=False)
    self.assertListEqual(channels, [(f, f+10) for f in range(3540, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3650)], is_portal_dpa=True)
    self.assertListEqual(channels, [(f, f+10) for f in range(3500, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3550), (3550, 3650)],
                                               is_portal_dpa=True)
    self.assertListEqual(channels, [(f, f+10) for f in range(3500, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3600), (3550, 3650)],
                                               is_portal_dpa=True)
    self.assertListEqual(channels, [(f, f+10) for f in range(3500, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3572, 3585)], is_portal_dpa=False)
    self.assertListEqual(channels, [(3570, 3580), (3580, 3590)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3572, 3575)], is_portal_dpa=False)
    self.assertListEqual(channels, [(3570, 3580)])

  def test_cbsdInsideDpaInMoveList(self):
    dpa = dpa_mgr.BuildDpa('Alameda',
                           protection_points_method='default(10,2,0,0)')
    dpa.ResetFreqRange([(3540, 3650)])
    alameda_geom = zones.GetCoastalDpaZones()['Alameda'].geometry
    # Assign grants inside the DPA and inband + OOB in mix of CatA and CatB
    np.random.seed(1234)
    cbsds_a = entities.GenerateCbsdsInPolygon(
        3, entities.CBSD_TEMPLATE_CAT_A_OUTDOOR, alameda_geom)
    cbsds_b = entities.GenerateCbsdsInPolygon(
        2, entities.CBSD_TEMPLATE_CAT_B, alameda_geom)
    cbsds_a[1] = cbsds_a[1]._replace(eirp_dbm_mhz=-100)
    cbsds_b[1] = cbsds_b[1]._replace(eirp_dbm_mhz=-100)
    grants = []
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_a[0:2], 3550, 3560))
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_a[2:3], 3660, 3670))
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_b[0:1], 3550, 3570))
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_b[1:2], 3630, 3670))
    dpa.SetGrantsFromList(grants)

    dpa.ComputeMoveLists()

    self.assertSetEqual(dpa.GetMoveList((3550, 3560)),
                        set([grants[0], grants[1], grants[3]]))
    self.assertSetEqual(dpa.GetMoveList((3640, 3650)),
                        set([grants[4]]))
    self.assertSetEqual(dpa.GetMoveList((3540, 3550)),
                        set(grants))

  def test_computeMoveListAndCheckInterf(self):
    protection_points = [ProtectionPoint(latitude=36.9400, longitude=-75.9989),
                         ProtectionPoint(latitude=37.7579, longitude=-75.4105),
                         ProtectionPoint(latitude=36.1044, longitude=-73.3147),
                         ProtectionPoint(latitude=36.1211, longitude=-75.5939)]
    regs = [json_load(os.path.join(TEST_DIR, 'RegistrationRequest_%d.json' % k))
            for k in range(1, 7)]
    grants = [json_load(os.path.join(TEST_DIR, 'GrantRequest_%d.json' % k))
              for k in range(1, 7)]
    grants_uut = data.getGrantsFromRequests(regs[:4], grants[:4])
    grants_th = data.getGrantsFromRequests(regs[4:], grants[4:])
    channel = (3600, 3610)
    dpa = dpa_mgr.Dpa(protection_points,
                      geometry=sgeo.Polygon([(pt.longitude, pt.latitude)
                                             for pt in protection_points]),
                      name='test(East1)',
                      threshold=-144,
                      beamwidth=3,
                      radar_height=50,
                      neighbor_distances=(150, 190, 0, 25),
                      freq_ranges_mhz=[channel])
    dpa.SetGrantsFromList(grants_uut + grants_th)
    expected_grants = set(grants_uut[0:3] + grants_th[0:1])
    # Testing move list
    dpa.ComputeMoveLists()
    self.assertSetEqual(dpa.GetMoveList(channel),
                        expected_grants)
    # Testing interference calculation
    interf = dpa.CalcKeepListInterference(channel)
    self.assertLess(max(interf), -144)
    # Testing check
    result = dpa.CheckInterference([grants_uut[3], grants_th[1]],
                                    margin_db=0.01,
                                    do_abs_check_single_uut=True,
                                    extensive_print=False)
    self.assertEqual(result, True)
    result = dpa.CheckInterference([grants_uut[2], grants_th[1]],
                                    margin_db=0.01,
                                    do_abs_check_single_uut=True,
                                    extensive_print=True)
    self.assertEqual(result, False)

  def test_cbsdInsideDpaInMoveList_Rel1Ext(self):
    dpa = dpa_mgr.BuildDpa('Alameda',
                           protection_points_method='default(10,2,0,0)',
                           use_updated_neighborhoods=True,
                           apply_clutter_network_loss_and_50_percent=True)
    dpa.ResetFreqRange([(3540, 3650)])
    alameda_geom = zones.GetCoastalDpaZones()['Alameda'].geometry
    # Assign grants inside the DPA and inband + OOB in mix of CatA and CatB
    dpa.ResetFreqRange([(3550, 3650)])
    np.random.seed(1234)
    cbsds_a = entities.GenerateCbsdsInPolygon(
        3, entities.CBSD_TEMPLATE_CAT_A_OUTDOOR, alameda_geom)
    cbsds_b = entities.GenerateCbsdsInPolygon(
        2, entities.CBSD_TEMPLATE_CAT_B, alameda_geom)
    cbsds_a[1] = cbsds_a[1]._replace(eirp_dbm_mhz=-100)
    cbsds_b[1] = cbsds_b[1]._replace(eirp_dbm_mhz=-100)
    grants = []
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_a[0:2], 3550, 3560))
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_a[2:3], 3660, 3670))
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_b[0:1], 3550, 3570))
    grants.extend(entities.ConvertToCbsdGrantInfo(cbsds_b[1:2], 3630, 3670))
    dpa.SetGrantsFromList(grants)

    dpa.ComputeMoveLists()

    self.assertSetEqual(dpa.GetMoveList((3550, 3560)),
                        {grants[0], grants[1], grants[3]})
    self.assertSetEqual(dpa.GetMoveList((3640, 3650)),
                        {grants[4]})

  def test_computeMoveListAndCheckInterf_Rel1Ext(self):
    protection_points = [ProtectionPoint(latitude=36.9400, longitude=-75.9989),
                         ProtectionPoint(latitude=37.7579, longitude=-75.4105),
                         ProtectionPoint(latitude=36.1044, longitude=-73.3147),
                         ProtectionPoint(latitude=36.1211, longitude=-75.5939)]
    regs = [json_load(os.path.join(TEST_DIR, 'RegistrationRequest_%d.json' % k))
            for k in range(1, 7)]
    grants = [json_load(os.path.join(TEST_DIR, 'GrantRequest_%d.json' % k))
              for k in range(1, 7)]
    grants_uut = data.getGrantsFromRequests(regs[:4], grants[:4])
    grants_th = data.getGrantsFromRequests(regs[4:], grants[4:])
    channel = (3600, 3610)
    dpa = dpa_mgr.Dpa(protection_points,
                      geometry=sgeo.Polygon([(pt.longitude, pt.latitude)
                                             for pt in protection_points]),
                      name='test(East1)',
                      threshold=-144,
                      beamwidth=3,
                      radar_height=50,
                      neighbor_distances=(150, 190, 0, 25),
                      freq_ranges_mhz=[channel],
                      apply_clutter_network_loss_and_50_percent=True)
    dpa.SetGrantsFromList(grants_uut + grants_th)
    expected_grants = set(grants_uut[0:3])
    # Testing move list
    dpa.ComputeMoveLists()
    self.assertSetEqual(dpa.GetMoveList(channel),
                        expected_grants)
    # Testing interference calculation
    interf = dpa.CalcKeepListInterference(channel)
    self.assertLess(max(interf), -144)
    # Testing check
    result = dpa.CheckInterference([grants_uut[3], grants_th[1]],
                                   margin_db=0.01,
                                   do_abs_check_single_uut=True,
                                   extensive_print=False,
                                   apply_clutter_network_loss_and_50_percent=True)
    self.assertEqual(result, True)
    result = dpa.CheckInterference([grants_uut[2], grants_th[1]],
                                   margin_db=0.01,
                                   do_abs_check_single_uut=True,
                                   extensive_print=True,
                                   apply_clutter_network_loss_and_50_percent=True)
    self.assertEqual(result, False)


if __name__ == '__main__':
  unittest.main()
