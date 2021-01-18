# Population-based ESC impact.

The `esc_pop_impact` module allows for evaluating the impact of ESC sensors, by counting
the population that falls within a "whisper zone".

The whisper zone is defined as the area such as if a single CBSD was deployed
then its power would be reduced. 

## Methodology

The sensor neighborhood area is gridded at a given resolution (`grid_arcsec`), 
where the neighborhood is defined as all areas within 80km for CatB and 40km for CatA.
Note: The neighborhood distance can be forced to other value for simulation speedup.

Path loss and interference reception level is then computed on each cell of this grid. 
All cell for which the ESC sensor protection level (-109dBm/MHz) is exceeded is then 
added to derive the so called population impact.

Note that to have uniquely defined whisper zone, some assumptions are done:
 + CatB: 25m high, 80km radius
 + CatA outdoor: 6m high, 40km radius
 + CatA indoor: 5m high, 40km radius

The CBSD antenna is taken as omnidirectional which is a good modeling for both CatA, and multi-sector CatBs.

An optional `budget_link_offset` can be used to scale the whisper zone
definition to include those area for which a deployed CBSD power reduction
would be above that offset.  This offset can also be used to simulate a 
noise rise, i.e. counting the impact of many CBSD deployed. 


## Installation

Install the population data by following the instructions on src/lib/usgs_pop/README.md

For running instruction, see header of  src/studies/esc_impact_pop/esc_pop_impact.py 

You will need one of several "ESC Sensor definition" files in the form of FAD file.
Currently only the ESC and SAS operators have access to the real files.


## Test

For the purpose of testing your environment, a fake FAD with a single fake sensor is
provided in front of East1 DPA in:
    Spectrum-Access-System/src/studies/esc_impact_pop/testdata/esc_fake.json 

You can run:

```bash
  python esc_pop_impact.py --esc_fads=testdata/esc_test.json --fast_mode --force_radius_km=50
```

This shall output:

```
## Measuring impact of ESC networks
Loading ESC networks
** Init population raster: Lazy loading **
.. done in 0s
** Evaluating population impact **
ESC Network processing: #0
... processing: E01_left
      27251 pops
*** Network Total: 27251 pops
.. done in 82s
** Final results **
Total Population: 27.252 kpops (1000s)
Network:
    0 : 27.252 kpops (1000s)
Sensors:
    E01_left : 27.252 kpops (1000s)
```


## Special mode to compute the population neighborhood

This mode allows to compute the population in each sensor neighborhood
independently of the actual propagation. In other words it computes the full
population that is present in the 80km (catB) or 40km neighborhoods.

Example

```bash
python esc_pop_impact.py --esc_fads=testdata/esc_test.json --nbor_pop_only
```

This shall output:

```
## Measuring impact of ESC networks
Loading ESC networks
** Init population raster: Lazy loading **
.. done in 0s
** Evaluating population impact **
**  SPECIAL MODE: population within neighborhood. **
ESC Network processing: #0
... processing: E01_left
      86428 pops
*** Network Total: 86428 pops
.. done in 12s
** Final results **
Total Population: 86.428 kpops (1000s)
Network:
    0 : 86.428 kpops (1000s)
Sensors:
    E01_left : 86.428 kpops (1000s)
```

