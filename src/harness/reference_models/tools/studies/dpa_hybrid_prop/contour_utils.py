# This software was developed by employees of the National Institute
# of Standards and Technology (NIST), an agency of the Federal
# Government. Pursuant to title 17 United States Code Section 105, works
# of NIST employees are not subject to copyright protection in the United
# States and are considered to be in the public domain. Permission to freely
# use, copy, modify, and distribute this software and its documentation
# without fee is hereby granted, provided that this notice and disclaimer
# of warranty appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
# WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
# ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
# BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
# ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS
# SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR
# OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY
# OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT
# OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#
# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with
# the code in compliance with the conditions of those licenses.

#==================================================================
# Utilities for analysis of non-overlapping PPA contour deployments
#==================================================================

import numpy as np
import matplotlib.pyplot as plt
from shapely.ops import unary_union
from shapely.geometry import MultiPolygon

from reference_models.geo import utils as geo_utils


def calcOverlapRatio(contours):
  """Calculate the total area of the contours, the area of their
     union, and their ratio.

  Args:
    contours: list of contours as shapely polygons
  """
  # Calculate area of each contour in square km
  area = [geo_utils.GeometryArea(c) for c in contours]

  # Calculate area of the union of the contours in sq km
  area_union = geo_utils.GeometryArea(unary_union(contours))

  # Print results
  print 'Total area:', np.sum(area), 'sq km'
  print 'Union area:', area_union, 'sq km'
  print 'Ratio:', np.sum(area)/area_union


def writeGeoJson(contours, fname):
  """Create a GeoJson file of the contours.

  Args:
    contours: list of contours as shapely polygons
    fname: path and name of GeoJson file
  """
  multiPolygon = MultiPolygon(list(contours))

  with open(fname, 'w') as f:
    f.write(geo_utils.ToGeoJson(multiPolygon))


def plotContourAreaHist(contours, bins, title):
  """Plot the histogram of contour areas.

  Args:
    contours: list of contours as shapely polygons
    bins: bins parameter of pyplot hist function
    title: title of histogram plot
  """
  # Calculate area of each contour in square km
  area = [geo_utils.GeometryArea(c) for c in contours]

  # Plot the histogram
  plt.hist(area, bins=bins)
  plt.xlabel('-96 dBm/10 MHz contour area (sq km)')
  plt.ylabel('Count')
  plt.title(title)
  plt.show(block=False)



