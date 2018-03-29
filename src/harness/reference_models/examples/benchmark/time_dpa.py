"""Benchmark the DPA model timing.

This is a simple simulation of the DPA for purpose of estimating time to run
"""
from collections import namedtuple
import time
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from reference_models.move_list_calc import move_list
from reference_models.geo import zones
from reference_models.geo import drive
from reference_models.examples import entities

#------------------------------
# Define simulation parameters
# - DPA to simulate
dpa_name = 'east_dpa_1'  # Norfolk

# - Number of sites to distribute within a given range of the DPA
num_sites = 100
max_dist_cat_a = 160
max_dist_cat_b = 320

# - Number of protection points in DPA per category.
#   Keep a ratio as expected in final to get accurate timing estimate
npts_front_dpa_contour = 20    # The mainland facing contour
npts_back_dpa_contour = 10     # The back contour
npts_within_dpa = 10

# - Do we restrict the sites to be within the census-defined urban areas
do_inside_urban_area = False

# - Ratio of cat B and different catA
ratio_cat_b = 0.2
ratio_cat_a_indoor = 0.4

# - Simulation setup
#   + Number of parallel processes
num_processes = 1
#   + Number of cached tiles (per process)
num_cached_tiles = 32

# - Internal parameters
num_montecarlo_iter = 2000
fmin, fmax = 3560, 3570
ratio_cat_a_outdoor = 1.0 - ratio_cat_b - ratio_cat_a_indoor


#----------------------------------
# Define the Protection points and specification
ProtectionPoint = namedtuple('ProtectionPoint',
                             ['latitude', 'longitude'])
ProtectionSpecs = namedtuple('ProtectionSpecs',
                             ['lowFreq', 'highFreq',
                              'antHeight', 'beamwidth', 'threshold'])

# Configure the geo drivers to avoid swap
drive.ConfigureTerrainDriver(cache_size=num_cached_tiles)
drive.ConfigureNlcdDriver(cache_size=num_cached_tiles)

# Read the DPA zone
print 'Preparing Zones'
dpa_zone = zones.GetDpaZones()[dpa_name]
usborder = zones.GetUsBorder()
urban_areas = zones.GetUrbanAreas() if do_inside_urban_area else None
protection_zone = zones.GetCoastalProtectionZone()


# Distribute random CBSD of various types around the FSS.
print 'Distributing random CBSDs in DPA neighborhood'
# - Find the zone where to distribute the CBSDs
typical_lat = dpa_zone.centroid.y
km_per_lon_deg = 111. * np.cos(typical_lat * np.pi / 180)
extend_cata_deg = max_dist_cat_a / km_per_lon_deg
extend_catb_deg = max_dist_cat_b / km_per_lon_deg

zone_cata = dpa_zone.buffer(extend_cata_deg).intersection(usborder)
zone_catb = dpa_zone.buffer(extend_catb_deg).intersection(usborder)

# - Distribute the CBSDs
cbsds_cat_a_indoor = entities.GenerateCbsdsInPolygon(
    num_sites * ratio_cat_a_indoor,
    entities.CBSD_TEMPLATE_CAT_A_INDOOR,
    zone_cata,
    drive.nlcd_driver,
    urban_areas)

cbsds_cat_a_outdoor = entities.GenerateCbsdsInPolygon(
    num_sites * ratio_cat_a_outdoor,
    entities.CBSD_TEMPLATE_CAT_A_OUTDOOR,
    zone_cata,
    drive.nlcd_driver,
    urban_areas)

cbsds_cat_b = entities.GenerateCbsdsInPolygon(
    num_sites * ratio_cat_b,
    entities.CBSD_TEMPLATE_CAT_B,
    zone_catb,
    drive.nlcd_driver,
    urban_areas)

all_cbsds = cbsds_cat_a_indoor + cbsds_cat_a_outdoor + cbsds_cat_b

# Useful plotting routine
ax = plt.axes(projection=ccrs.PlateCarree())
margin = 0.1
box = zone_catb.union(dpa_zone)
ax.axis([box.bounds[0]-margin, box.bounds[2]+margin,
         box.bounds[1]-margin, box.bounds[3]+margin])
ax.coastlines()
ax.stock_img()
ax.plot(*dpa_zone.exterior.xy, color='r')
ax.plot(*zone_cata.exterior.xy, color='b', linestyle='--')
ax.plot(*zone_catb.exterior.xy, color='g', linestyle='--')
ax.scatter([cbsd.longitude for cbsd in all_cbsds],
           [cbsd.latitude for cbsd in all_cbsds],
           color='g', marker='.')
ax.set_title('DPA: %s' % dpa_name)
plt.show(block=False)


# - Convert them into proper registration and grant requests
reg_requests = [entities.GetCbsdRegistrationRequest(cbsd)
                for cbsd in all_cbsds]
grant_requests = [entities.GetCbsdGrantRequest(cbsd, fmin, fmax)
                  for cbsd in all_cbsds]

# Manual for now: define a set of typical point with respecting a distribution
# of points which will be typical of ratio of what we have in the boundaries and
# inside distribution
protection_points = [ProtectionPoint(longitude=-75.686, latitude=37.234),
                     ProtectionPoint(longitude=-75.417, latitude=37.757),
                     ProtectionPoint(longitude=-75.635, latitude=36.188),
                     ProtectionPoint(longitude=-74.808, latitude=37.897),
                     ProtectionPoint(longitude=-75.058, latitude=35.762),
                     ProtectionPoint(longitude=-74.610, latitude=36.812),
                     ProtectionPoint(longitude=-75.869, latitude=36.859),
                     ProtectionPoint(longitude=-75.116, latitude=38.014),
                     ProtectionPoint(longitude=-75.386, latitude=35.713),
                     ProtectionPoint(longitude=-75.251, latitude=36.890)]

protection_spec = ProtectionSpecs(lowFreq=fmin*1e6, highFreq=fmax*1e6,
                                  antHeight=50, beamwidth=3, threshold=-144)


# Run the move list algorithm a first time to fill up geo cache
print 'Running Move List algorithm once'
result = move_list.findMoveList(protection_spec, protection_points[:1],
                                reg_requests[0:100], grant_requests[0:100],
                                num_montecarlo_iter, num_processes,
                                protection_zone)

# Run it for real and measure time
start_time = time.time()
result = move_list.findMoveList(protection_spec, protection_points,
                                reg_requests, grant_requests,
                                num_montecarlo_iter, num_processes,
                                protection_zone)
end_time = time.time()

print 'Num CBSD: %d' % len(reg_requests)
print 'Move list size: %d' % np.sum(result)
print 'Computation time: %.1fs' % (end_time - start_time)

# Check statistic on tile loading
print '-- Cache tile statistics'
cnt_per_tile = drive.terrain_driver.stats.DetailedCountPerTile()
if max(cnt_per_tile) > 1:
  print 'WARNING: cache tile too small - tiles are evicted from cache'
  drive.terrain_driver.stats.Report()

# Plot the move list
ax.scatter([cbsd.longitude for k, cbsd in enumerate(all_cbsds) if result[k]],
           [cbsd.latitude for k, cbsd in enumerate(all_cbsds) if result[k]],
           color='r', marker='.')
plt.show()
