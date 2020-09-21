"""Tests for the module 'esc_pop_impact.py'."""

import json
import os
import unittest

import mock
import numpy as np
import shapely.geometry as sgeo

from reference_models.tools import testutils
from reference_models.geo import zones
from reference_models.propagation import wf_itm

from usgs_pop import usgs_pop_driver

import esc_pop_impact

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'testdata')
TEST_JSON = 'esc_test.json'

def ReplaceItmModelByFakeVersion(offset_db=100, factor=1.0):
  """Replaces Itm model by fake version.

  The predicted path loss will be for a given distance:
    factor * distance_km + offset_db

  Args:
    offset_db: The fixed offset (dB).
    factor: A factor on the distance.
  """
  wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
      factor=factor, offset=offset_db, dist_type='REAL')


class EscImpact(unittest.TestCase):

  @mock.patch.object(
      zones, 'GetUsBorder', return_value=sgeo.box(-179, -89, 179, 89))
  @mock.patch.object(usgs_pop_driver, 'UsgsPopDriver', autospec=True)
  def testPopulationImpact(self, mock_pop_driver, _):
    # Mock and Fakes.
    mock_pop_driver.return_value.GetPopulationDensity.side_effect = (
        lambda lat, lon: np.ones(len(lat)))
    ReplaceItmModelByFakeVersion(
        offset_db=126)  # loss < 146dB for first 20km, ie 37-(-109)
    # Read network Json data: omni antenna except 20 degrees wide null.
    with open(os.path.join(TESTDATA_DIR, TEST_JSON), 'r') as fd:
      sensors = json.load(fd)['recordData']
    # Processing - should be a pop of 1pop/km2 in a circle of 20km,
    # except for a 20degrees-wide area, ie about:
    #  340/360. * pi*20**2  = 1186
    popper = usgs_pop_driver.UsgsPopDriver()
    total_pop, pop_per_network, pop_per_sensor = esc_pop_impact.PopulationImpact(
        [sensors, sensors],
        'B',
        res_arcsec=10,
        offset_db=0,
        popper=popper,
        filter_box=None,
        forced_radius_km=30)
    self.assertAlmostEqual(total_pop, 1182, 0)  # almost 1186
    self.assertEqual(total_pop, pop_per_network[0])
    self.assertEqual(total_pop, pop_per_network[1])
    self.assertEqual(total_pop, pop_per_sensor['E01_left'])


if __name__ == '__main__':
  unittest.main()
