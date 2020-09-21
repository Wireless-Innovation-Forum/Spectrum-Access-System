# USGS population driver

This driver allows to read the US population density based on USGS data.
Note that it requires enough RAM as the data is managed in memory as a single
raster of about 8G.


## Installation

1. Download the population data (preferable pden_2010.zip) from:
    https://www.sciencebase.gov/catalog/item/57753ebee4b07dd077c70868

2. Unzip the data and put the `pden2010_block/` folder into the `data/pop/` folder

3. If using another folder, change the `DEFAULT_POP_DIR` global variable
   to point to that other folder.
   
## Usage

### Lazy Loading (Recommended)

The data is loaded as needed.

```python
  # Initialize raster.
  driver = UsgsPopDriver(usgs_pop_directory, lazy_load=True)

  # Now read population density for one point, or a sequence of points.
  density = driver.GetPopulationDensity(latitudes, longitudes)
```

### Full data loading in memory

This method has initial overhead to read the full US population (even though
only part of it might be used).

```python
  # Initialize raster.
  driver = UsgsPopDriver(usgs_pop_directory)

  # Load data in memory.
  driver.LoadRaster()

  # Now read population density for one point, or a sequence of points.
  density = driver.GetPopulationDensity(latitudes, longitudes)
```

### Partial data loading in memory

Only to be used to control precisely the memory loading process. 
No sanity check performed to verify that retrieval of population data is done
on tiles previously loaded.


```python
  # Initialize raster.
  driver = UsgsPopDriver(usgs_pop_directory)

  # Load data in memory from a box.
  driver.LoadRaster((lat_min, lon_min, lat_max, lon_max))

  # Now read population density for one point, or a sequence of points.
  # Needs to be done within the box.
  density = driver.GetPopulationDensity(latitudes, longitudes)
```

