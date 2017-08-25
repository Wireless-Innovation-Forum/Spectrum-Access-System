#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

"""Hybrid WinnForum NTIA Propagation Model.

The Hybrid NTIA propagation model performs a blend of Extended-Hata,
Irregular Terrain Model (ITM) and Free Space Loss (FSL), as described
in WinnForum specification R2-SGN-04.

Typical usage:
  # Reconfigure the terrain driver
   #  - reset the terrain tile directory
  ConfigureTerrainDriver(terrain_dir=my_ned_path)
   #  - reset the cache size. Memory use is: cache_size * 50MB
  ConfigureTerrainDriver(cache_size=8)

  # Get the path loss and incidence angles
  db_loss, incidence_angles, internals = CalcHybridPropagationLoss(
              lat_cbsd, lon_cbsd, height_cbsd,
              lat_rx, lon_rx, height_rx,
              reliability=0.5,
              freq_mhz=3625.,
              region='URBAN')
"""

from collections import namedtuple
import logging
import math

from reference_models.geo import terrain
from reference_models.geo import vincenty

from reference_models.propagation import wf_itm
from reference_models.propagation.ehata import ehata


# Initialize terrain driver
terrainDriver = terrain.TerrainDriver()
def ConfigureTerrainDriver(terrain_dir=None, cache_size=None):
  """Configure the NED terrain driver.

  Note that memory usage is about cache_size * 50MB.

  Inputs:
    terrain_dir: if specified, modify the terrain directory.
    cache_size:  if specified, change the terrain tile cache size.
  """
  if terrain_dir is not None:
    terrainDriver.SetTerrainDirectory(terrain_dir)
    wf_itm.ConfigureTerrainDriver(terrain_dir=terrain_dir)
  if cache_size is not None:
    terrainDriver.SetCacheSize(cache_size)
    wf_itm.ConfigureTerrainDriver(cache_size=cache_size)


# eHata standard deviation calculation parameters
# according to WinnForum R2-SGN-22, and NTIA Technical Report
# TR-15-517, equation A18(a),(b),(c)
_ALPHA_U = 4.0976291
_BETA_U = -1.2255656
_GAMMA_U = 0.68350345


# Hybrid mode Application Information
class HybridMode:
  FSL = 0
  ITM_HIGH_HEIGHT = 1
  ITM_RURAL = 2
  ITM_DOMINANT = 3
  EHATA_DOMINANT = 4
  EHATA_FSL_INTERP = 5
  ITM_CORRECTED = 6

_HYBRID_MODES = {
    # Using FSL
    HybridMode.FSL: 'Using FSL: d <= 100 m and not rural.',
    # Using ITM
    HybridMode.ITM_HIGH_HEIGHT: 'Using ITM: Effective height > 200 m.',
    HybridMode.ITM_RURAL: 'Using ITM: Rural environment.',
    HybridMode.ITM_DOMINANT: 'Using ITM: ITM median >= eHata median.',
    # Using eHata
    HybridMode.EHATA_DOMINANT: 'Using eHata: eHata median > ITM median.',
    # Special mixed modes
    HybridMode.EHATA_FSL_INTERP: 'Using FSL-eHata interpolation: distance between 100 m - 1 km',
    HybridMode.ITM_CORRECTED: 'Using corrected ITM: distance > 80 km.'
}


def GetInfoOnHybridCode(code):
  """Get description of Hybrid calculation mode."""
  return _HYBRID_MODES[code]


def GetEHataStandardDeviation(freq_mhz, is_urban):
  """Gets the Log Normal standard deviation of E-Hata.

  Inputs:
    freq_mhz:  the frequency in MHz. Used to compute the eHata stdev.
    is_urban:  if False, an extra 2dB is added to the stdev

  Returns:
    the offset in dB to apply to the median
  """
  std = (_ALPHA_U + _BETA_U * math.log10(freq_mhz)
         + _GAMMA_U * math.log10(freq_mhz)**2)
  if not is_urban:
    std += 2
  return std


# Offset from median to mean dB
def _GetMedianToMeanOffsetDb(freq_mhz, is_urban):
  """Gets the Offset from median to mean for lognormal distribution.

  Inputs:
    freq_mhz:  the frequency in MHz. Used to compute the eHata stdev.
    is_urban:  if False, an extra 2dB is added to the stdev

  Returns:
    the offset in dB to apply to the median
  """
  std = GetEHataStandardDeviation(freq_mhz, is_urban)
  offset = std**2 / (20. * math.log(10.))
  return offset


# Defined namedtuple for nice output packing
_PropagResult = namedtuple('_PropagResult',
                           ['db_loss', 'incidence_angles', 'internals'])
_IncidenceAngles = namedtuple('_IncidenceAngles',
                              ['hor_cbsd', 'ver_cbsd', 'hor_rx', 'ver_rx'])


# Main entry point of the Hybrid model
def CalcHybridPropagationLoss(lat_cbsd, lon_cbsd, height_cbsd,
                              lat_rx, lon_rx, height_rx,
                              reliability=-1,
                              freq_mhz=3625.,
                              region='RURAL',
                              refractivity=-1, climate=-1):
  """Implements the Hybrid ITM/eHata NTIA propagation model.

  As specified by Winforum, see:
    R2-SGN-03, R2-SGN-04 through R2-SGN-10 and NTIA TR 15-517 Appendix A.

  Note that contrary to the ITM model, this function does not provide the
  possibility to retrieve a CDF of path losses, as it is not required in the
  intended use of that model (it shall be used currently only for protecting
  zones using average aggregated interference).

  Warning: Only 'reliability' values 0.5 (median) and -1 (average) are currently
  fully supported, as other values will not return the quantile when using
  internally the eHata model. Workaround is to apply it afterwards when the
  returned opcode=4, and using the standard deviation obtained with the
  'GetEHataStdev()' routine.

  Inputs:
    lat_cbsd, lon_cbsd, height_cbsd: Lat/lon (deg) and height AGL (m) of CBSD
    lat_rx, lon_rx, height_rx:       Lat/lon (deg) and height AGL (m) of Rx point
    freq_mhz:           Frequency (MHz). Default is mid-point of band.
    reliability:        Reliability. Default is -1 (average value).
                        Options:
                          Value in [0,1]: returns the CDF quantile
                          -1: returns the mean path loss
    region:             Region type among 'URBAN', 'SUBURBAN, 'RURAL'
    refractivity        Refractivity [0-1]. Default -1
                        If < 0 (default), use lookup for midpoint in database.
    climate             Climate value [0-1]. Default -1
                        If < 0 (default), use lookup for midpoint in database.

  Returns:
    A namedtuple of:
      db_loss:          Path Loss in dB.

      incidence_angles: A namedtuple of angles (degrees)
          hor_cbsd:       Horizontal departure angle (bearing) from CBSD to Rx
          ver_cbsd:       Vertical departure angle at CBSD
          hor_rx:         Horizontal incidence angle (bearing) from Rx to CBSD
          ver_rx:         Vertical incidence angle at Rx

      internals:        A dictionary of internal data for advanced analysis:
          hybrid_opcode:  Opcode from HybridCode - See GetInfoOnHybridCodes()
          effective_height_cbsd: Effective CBSD antenna height
          itm_db_loss:    Loss in dB for the ITM model.
          itm_err_num:    ITM error code (see wf_itm module).
          itm_str_mode:   Description (string) of dominant prop mode in ITM.
          dist_km:        Distance between end points (km)
          prof_d_km       ndarray of distances (km) - x values to plot terrain.
          prof_elev       ndarray of terrain heightsheights (m) - y values to plot terrain,

  Raises:
    Exception if input parameters invalid or out of range.
  """
  # TODO: Apply quantile in eHata prediction for values not equal to 0.5.
  #       Not critical since the expected use is only for mean value (ie reliability=-1)
  #       which is properly managed. For now raise an exception if reliability value
  #       different of -1 or 0.5

  # Sanity checks on input parameters
  if height_cbsd < 1 or height_rx < 1:
    raise Exception('End-point height less than 1m.')
  if height_cbsd > 1000 or height_rx > 1000:
    raise Exception('End-point height greater than 1000m.')
  if freq_mhz < 40 or freq_mhz > 10000:
    raise Exception('Frequency outside range [40MHz - 10GHz].')
  if region not in ['RURAL', 'URBAN', 'SUBURBAN']:
    raise Exception('Region %s not allowed' % region)
  if refractivity >= 0 and (refractivity < 250.0 or refractivity > 400.0):
    raise Exception('Refractivity outside range [250 - 400].')
  if climate >= 0 and (climate < 1 or climate > 7):
    raise Exception('Bad radio climate value (not within [1..7]).')

  if reliability != -1 and reliability != 0.5:
    logging.warning('E-Hata submodel only computes the median.'
                    'Use GetEhataStdDev() to obtain quantile in case opcode is 4 or 5.')

  # Get the terrain profile, using Vincenty great circle route, and WF
  # standard (bilinear interp; 1501 pts for all distances over 45 km)
  its_elev = terrainDriver.TerrainProfile(lat1=lat_cbsd, lon1=lon_cbsd,
                                          lat2=lat_rx, lon2=lon_rx,
                                          target_res_meter=30.,
                                          do_interp=True, max_points=1501)


  # Structural CBSD and mobile height corrections
  height_cbsd = max(height_cbsd, 20.)
  height_rx = 1.5

  # Calculate the predicted ITM loss
  # and get the distance and profile for use in further logic
  db_loss_itm, incidence_angles, internals = wf_itm.CalcItmPropagationLoss(
      lat_cbsd, lon_cbsd, height_cbsd,
      lat_rx, lon_rx, height_rx,
      reliability, freq_mhz, refractivity, climate, its_elev)
  internals['itm_db_loss'] = db_loss_itm

  # Calculate the effective heights of the tx
  height_cbsd_eff = CbsdEffectiveHeights(height_cbsd, its_elev)
  internals['effective_height_cbsd'] = height_cbsd_eff

  # Use ITM if CBSD effective height greater than 200 m
  if height_cbsd_eff >= 200:
    internals['hybrid_opcode'] = HybridMode.ITM_HIGH_HEIGHT
    return _PropagResult(
        db_loss = db_loss_itm,
        incidence_angles = incidence_angles,
        internals = internals)

  # Set the environment code number.
  if region == 'URBAN':
    region_code = 23
  elif region == 'SUBURBAN':
    region_code = 22
  else:  # 'RURAL': use ITM
    internals['hybrid_opcode'] = HybridMode.ITM_RURAL
    return _PropagResult(
        db_loss = db_loss_itm,
        incidence_angles = incidence_angles,
        internals = internals)

  # The eHata offset to apply (in case the mean is requested)
  offset_median_to_mean = 0.
  if reliability == -1:
    offset_median_to_mean = _GetMedianToMeanOffsetDb(freq_mhz, region == 'URBAN')

  # Now process the different cases
  dist_km = internals['dist_km']

  if dist_km <= 0.1:  # Use Free Space Loss
    db_loss = CalcFreeSpaceLoss(dist_km, freq_mhz, height_cbsd, height_rx)
    internals['hybrid_opcode'] = HybridMode.FSL
    return _PropagResult(
        db_loss = db_loss,
        incidence_angles = incidence_angles,
        internals = internals)

  elif dist_km > 0.1 and dist_km < 1:  # Use E-Hata Median Basic Prop Loss
    fsl_100m = CalcFreeSpaceLoss(0.1, freq_mhz, height_cbsd, height_rx)
    median_basic_loss = ehata.MedianBasicPropLoss(
        freq_mhz, height_cbsd, height_rx,
        dist_km, region_code)
    alpha = 1. + math.log10(dist_km)
    db_loss = fsl_100m + alpha * (median_basic_loss - fsl_100m)

    # TODO: validate the following approach with WinnForum participants:
    # Weight the offset as well from 0 (100m) to 1.0 (1km).
    db_loss += alpha * offset_median_to_mean
    internals['hybrid_opcode'] = HybridMode.EHATA_FSL_INTERP
    return _PropagResult(
        db_loss = db_loss,
        incidence_angles = incidence_angles,
        internals = internals)

  elif dist_km >= 1 and dist_km <= 80:  # Use best of E-Hata / ITM
    ehata_loss_med = ehata.ExtendedHata(its_elev, freq_mhz, height_cbsd, height_rx,
                                        region_code)
    if reliability == 0.5:
      itm_loss_med = db_loss_itm
    else:
      itm_loss_med = wf_itm.CalcItmPropagationLoss(
          lat_cbsd, lon_cbsd, height_cbsd, lat_rx, lon_rx, height_rx,
          0.5, freq_mhz, refractivity, climate, its_elev).db_loss

    if itm_loss_med >= ehata_loss_med:
      internals['hybrid_opcode'] = HybridMode.ITM_DOMINANT
      return _PropagResult(
          db_loss = db_loss_itm,
          incidence_angles = incidence_angles,
          internals = internals)
    else:
      ehata_loss = ehata_loss_med + offset_median_to_mean
      internals['hybrid_opcode'] = HybridMode.EHATA_DOMINANT
      return _PropagResult(
          db_loss = ehata_loss,
          incidence_angles = incidence_angles,
          internals = internals)

  elif dist_km > 80:  # Use the ITM with correction from E-Hata @ 80km
    # Calculate the ITM median and eHata median losses at a
    # distance of 80 km.
    bearing = incidence_angles.hor_cbsd

    # TODO: validate the following approach with WinnForum participants:
    # Note: For best performance, and avoiding another profile extraction,
    #       we get the 80km from the original profile instead of extraction
    #       from scratch which would require the following slow operations:
    #
    # lat_80km, lon_80km, _ = vincenty.GeodesicPoint(lat_cbsd, lon_cbsd,
    #                                                80., bearing)
    # its_elev_80km = terrainDriver.TerrainProfile(lat_cbsd, lon_cbsd, lat_80km, lon_80km,
    #                                              30, 1501)
    num_points = int(80000. / its_elev[1]) + 1
    its_elev_80km = its_elev[0:num_points+2]
    its_elev_80km[0] = num_points - 1
    dist_80km = (num_points - 1) * its_elev_80km[1]

    # Calculate eHata loss and the ITM median loss at 80 km
    ehata_loss_80km = ehata.ExtendedHata(its_elev_80km, freq_mhz,
                                         height_cbsd, height_rx,
                                         region_code)
    lat_80km, lon_80km, _ = vincenty.GeodesicPoint(lat_cbsd, lon_cbsd,
                                                   dist_80km, bearing)

    itm_loss_80km = wf_itm.CalcItmPropagationLoss(
        lat_cbsd, lon_cbsd, height_cbsd, lat_80km, lon_80km, height_rx,
        0.5, freq_mhz, refractivity, climate, its_elev_80km).db_loss

    J = max(ehata_loss_80km - itm_loss_80km, 0)
    db_loss = db_loss_itm + J

    internals['hybrid_opcode'] = HybridMode.ITM_CORRECTED
    return _PropagResult(
        db_loss = db_loss,
        incidence_angles = incidence_angles,
        internals = internals)


def CalcFreeSpaceLoss(dist_km, freq_mhz, height_cbsd, height_rx):
  """Computes the free space loss.

  Inputs:
    dist_km:  the distance (km)
    freq_mhz: the frequency (MHz)
    height_cbsd: the height of the CBSD
    height_rx: the height of the receive point

  Returns:
    the free space path loss in dB
  """
  r = math.sqrt((1000. * dist_km)**2 + (height_cbsd - height_rx)**2)
  db_loss = 20. * math.log10(r) + 20. * math.log10(freq_mhz) - 27.56
  return db_loss


def CbsdEffectiveHeights(height_cbsd, its_elev):
  """Get the CBSD effective height 'h_b'.

  According to Winnforum spec R2-SGN-04.

  Inputs:
    height_cbsd: height of the CBSD above terrain (meters).
    its_elev:  terrain profile in ITS format.

  Returns:
    the CBSD effective height.
  """

  np = int(its_elev[0])
  xi = its_elev[1] * 0.001   # step size of the profile points, in km
  dist_km = np * xi          # path distance, in km
  elev_cbsd = its_elev[2]

  if height_cbsd < 20:
    height_cbsd = 20.

  if dist_km < 3.0:
    eff_height = height_cbsd

  else: # dist_km >= 3
    i_start = 2 + int(math.ceil(3.0 / xi))
    i_end = np + 2
    if dist_km > 15:
      i_end = 2 + int(math.floor(15.0 / xi))
      dist_km = 15.0

    avg_height = sum(its_elev[i_start:i_end+1]) / float(i_end - i_start + 1)
    eff_height = height_cbsd + (dist_km - 3.0) / 12.0 * (elev_cbsd - avg_height)

  if eff_height < 20:
    eff_height = 20

  return eff_height
