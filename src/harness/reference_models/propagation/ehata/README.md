# Extended-HATA Python implementation

This directory holds a Python extension module of the Extended HATA model, in its
[ITS implementation](https://github.com/NTIA/ehata). 

The Extended HATA model is described in the [NTIA Technical Report 15-517](https://www.ntia.doc.gov/report/2015/35-ghz-exclusion-zone-analyses-and-methodology).

The its/ folder contains the original C++ implementation obtained from ITS GitHub, 
with minimal modifications for WinnForum requirements.

A simple python wrapper `ehata.py` is provided for defining the model interface.

## Interface

The entry points are the routines `ExtendedHata()` and `MedianBasicPropLoss()`
in ehata.py, which take as parameters the frequency, base station and mobile heights,
and the terrain profile in the same ITS format as used by the ITM (Irregular Terrain
Model) propagation model.

Note that the original ITS C++ code uses a reversed profile compared to the ITM:
the profile shall be given from the mobile station to the transmitter station.
The python extension module `ehata_its_py.cpp` module takes care of this adaptation
so that the outer interface is consistent with the ITM interface (ie the profile from
transmitter to receiver).

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
  - modification of formulas used to compute the terrain effective height
  between 3km and 15km (due to an issue in original formulas), and to use
  terrain strictly included within the 3km and 15km range.

In addition all the code has been ported to use double instead of float, using
a global #define in `ehata.h`. This allows much more consistent results across existing
or future implementations.


## Running the tests
To run the origina ITS test set, first compile le python extension module,
then run the `ehata_test.py` module:

    `python ehata_test.py`


## Building the python extension module

A Python wrapper is provided to generate a Python extension module.
To build this extension, use the make command:

    `make`
    
which basically runs:

    `python setup.py build_ext --inplace`
    `python3 setup.py build_ext --inplace`    

For Windows specific compilation, see upper level [README.md](../README.md).

