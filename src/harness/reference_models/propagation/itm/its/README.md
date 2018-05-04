# The C version of the Irregular Terrain Model (ITM) from ITS

(See https://www.its.bldrdoc.gov/resources/radio-propagation-software/itm/itm.aspx)

## Description

This source repository contains a slightly modified version of the ITS ITM model,
written originally in Fortran and ported in C++.

See the `original/` subfolder for the original C++ source code.


## Winnforum Modification

The modification are related to the `point_to_point()` main routine:

 - a new function `point_to_point_rels()` replicates the `point_to_point()` routine,
 but takes takes an array of reliabilities and return an array of path losses values.

 - returning ver0, and ver1, the vertical incidence angles (in degrees) for both end points.
 
 - passing mdvar value - default value = 12 (original)

 - passing a boolean variable 'eno_is_final' (default=false), which intent is
 to specify if the refractivity shall be compensated with average profile
 altitude. Required to run original ITM test set as originally intended (with
 value True) in Fortran code.

 - using default value 310 for the base refractivity if not specified (as found
 in Fortran code).

These last two code changes are to replicate the original Fortran code, and
mostly in use in passing original test set provided with the Fortran code.

## Running the tests
To run the origina NTIA test set, build the test script

    `g++ -Wall itm.cpp itm_test.cpp -o itm_test`

Then the test can be run with './itm_test'
