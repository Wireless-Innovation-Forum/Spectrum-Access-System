# Extended-HATA Python implementation

This directory holds a Python extension module of the Extended HATA model, in its
[ITS implementation](https://github.com/NTIA/ehata). 

The Extended HATA model is described in the [NTIA Technical Report 15-517](https://www.ntia.doc.gov/report/2015/35-ghz-exclusion-zone-analyses-and-methodology).

The its/ folder contains the original C++ implementation obtained from ITS GitHub, 
with minimal modifications for WinnForum requirements.

A simple python wrapper `ehata.py` is provided for defining the model interface.

## Interface

The entry points are the routines `ExtendedHata()` and `MedianBasicPropLoss()`,
which take as parameters the frequency, base station and mobile heights, and the
terrain profile in the same ITS format as used by the ITM (Irregular Terrain
Model) propagation model.

See the python wrapper `ehata.py` for a complete description of input/output parameters.


## Winnforum extensions

The ITS code has been slightly adapted to the WinnForum requirements, and all
modifications are flagged within the `_WinnForum_Extensions` flag and the
`// ******* WinnForum extension *******` comment lines.

The flag allows for running the original ITS code for full validation of this
implementation. To deactivate the winnforum extensions, you can use 
the `SetWinnForumExtensions(False)` call.
By default the WinnForum extensions are activated.

The modification relates mostly to:

  - the minimal value for the effective cbsd height being 20m instead of 30m
  - the mobile effective height not used (structural height used instead)
  - slight modification in formulas used to compute the internal effective height between 3km and 15km
  - a buffer overflow bug fix in the original ITS code for quantile calculation.
  (see `FindQuantile.cpp`), which makes the result vary depending on the run.
  Note: Fix is pending and not yet submitted at this time

In addition all the code has been ported to use double instead of float, using
a global #define in `ehata.h`. This allows much more consistent results across existing
or future implementations.


## Running the tests
To run the origina ITS test set, first compile le python extension module,
then run the `ehata_test.py` module:

    `python ehata_test.py`


## Building the python extension module

A Python wrapper is provided to generate a Python extension module.

To build this extension:

    `python setup.py build_ext -i`


