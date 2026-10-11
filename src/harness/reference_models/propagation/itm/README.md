# ITM (Irregular Terrain Model) propagation model

This directory holds a Python extension module of the ITS Irregular Terrain Model.

The ITM model is described in details in the documentation found in subfolder `its/original/docs`.

The `its/` folder contains the C++ implementation (itself derived from the reference
Fortran implementation), with only minimal modifications.

A simple python wrapper `itm.py` is provided for defining the model interface.

## Interface

The entry point is the routine `point_to_point()`. 
See the python wrapper `itm.py` for a complete description of input/output parameters.


## Winnforum extensions

There are only a few changes compared to the original ITM code:

  - the core implementation has been extended with a new `point_to_point_rels()`
  routine, which takes an array of reliabilities and returns an array of path losses.
  This is useful for efficient computation of the mean and inverse CDF.
  
  - `point_to_point()` routine takes the extra `mdvar` parameter as to allow
  for specializing this parameter in WinnForum. This parameter is by default
  set to 12 which is the default value in the original ITM code. Value 13
  shall be used for the WinnForum implementation.

  - `point_to_point()` routine also takes the extra `eno_is_final` boolean parameter, 
  which is by default set to False. When set to True, the code dealing with
  refractivity calculation replicates the logic found in the original Fortran code, which
  has been lost during the Fortran->C++ port (namely to allow specifying a
  final refractivity 'eno' with no compensation by altitude).
  In particular this allows to run the original ITS test set as originally
  intended.


## Building the Python extension module

Python 3.11 through 3.15 is supported. From the Spectrum-Access-System repository
root, install the locked dependencies and build ITM with the selected interpreter:

```sh
uv sync --locked
uv run --locked make -C src/harness/reference_models/propagation/itm PYTHON=python
```

The Makefile invokes setuptools in the root uv environment. A C++ compiler and
make are required; rebuild the extension whenever you change Python versions.
For Windows build commands, see the [propagation README](../README.md).

## Running the tests

After building the extension, run the original ITS test set and wrapper tests
from the repository root:

```sh
uv run --locked python -m pytest src/harness/reference_models/propagation/itm/itm_test.py
```

## Thread safety

Warning: The ITS ITM implementation is not thread-safe as it extensively uses
global variables. Do not try to run several calculation in parallel.
