# Population-based ESC impact.

This module allows for evaluating the impact of ESC, by counting
the population that falls within a "whisper zone".

The whisper zone is defined as the area for which: if a CBSD was deployed
then its power would be reduced. An optional `budget_link_offset` can be
used to scale the whisper zone definition to include those area for which
a deployed CBSD power reduction would be above that offset. Or it can be
used to simulate a noise rise, i.e. counting the impact if there was a certain
number of CBSD deployed.

This is done by gridding the sensor neighborhood area at a given resolution (`grid_arcsec`), 
where the neighborhood is defined as all areas within 80km for CatB and 40km for CatA.
The neighborhood distance can be forced to other value for simulation speedup.


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


