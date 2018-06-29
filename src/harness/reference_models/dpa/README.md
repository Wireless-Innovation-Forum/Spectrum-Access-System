# The WinnForum R2-SGN-24 DPA Protection Procedure Reference Implementation

This folder contains Python code and test data for calculation of the DPA move-list 
according to the R2-SGN-24 requirement in the WINNF-TS-0112 document, Version V1.4.1-r2.0 
(January 16, 2018) [1].

## Main Interface 

The code is organized in 2 main files:
 
  - `dpa_mgr.py`: the DPA manager code wrapping the move list code.
  - `move_list.py`: the move list and interference check calculation code.

A third file `dpa_builder.py` is provided for managing the protected points distribution within
the DPA and eventually plugging a custom builder.

### DPA Manager

The DPA manager provides a `Dpa` class for managing fully a DPA, along with a `BuildDpa()`
factory routine for building a DPA from basic information.

The typical process for using the DPA is the following:

```python
  import dpa_mgr
  # Create a DPA with the builder, from a JSON file defining all the DPA protected points:
  dpa = BuildDpa('East1', 
                 protection_points_method = 'filename.json', 
                 portal_dpa_filename='My_P-DPA.kml')
  #   or create it with a default builder - See BuildDpa() docs.
  dpa = BuildDpa('East1', 
                 protection_points_method = 'default (250,100,100,50,40,0.2,2,0.2,2)',
                 portal_dpa_filename='My_P-DPA.kml')
  #   or create it with your own custom builder - See section below. `dpa_builder.py`
  dpa = BuildDpa('East1', 
                 protection_points_method = 'my_builder (2500, "method1")'
                 portal_dpa_filename='My_P-DPA.kml')

  # Set the grants from the FAD objects.
  dpa.SetGrantsFromFad(sas_uut_fad, sas_th_fads)
  #   or set them from a list of `CbsdGrantInfo` objects
  dpa.SetGrandsFromList(grants)
  
  # Eventually restrict artificially the protected band.
  # (optional - just for speed up in simulations)
  dpa.ResetFreqRange([(3550, 3570), (3600, 3650)])

  # Now compute the DPA move list.
  dpa.ComputeMoveLists()
  
  # Get The move list, neighbor list or keep list for a given channel.
  ml_grants = dpa.GetMoveList((3550, 3560))
  kl_grants = dpa.GetKeepList((3550, 3560))
  nl_grants = dpa.GetNeighborList((3550, 3560))
  
  # Computes the maximum aggregated interference from the keep list on the DPA.
  interf = dpa.CalcKeepListInterference((3550, 3560))
  
  # Performs the test harness interference check of SAS UUT versus reference model.
  dpa.CheckInterference(sas_uut_active_grants, margin_db=10)
```

Notes:
 - the `protection_points_method` argument is what needs to be specified on the
 configuration file of the testcases related to DPA (IPR, MCP, ...).
 - the `dpa_mgr` module uses multiprocessing to speed up calculation, using the common 
 mpool facility.

### Move List

The main routines are:
 
  - `moveListConstraint()` : compute the move list for a single protection point and a set
  of grants.
  - `calcAggregateInterference()` : calculates the 95% aggregated interference quantile on
  a protected point from a set of active grants (typically the grants in the Keep list).

Notes: These routines are used by the DPA manager, and do not need to be called directly, 
except in possible simulation environment unrelated to SAS certification where more control
is required. Note that a legacy `findMoveList()` is provided as well as it was used in 
early NIST simulation, as examplified in the `move_list_example.py` file.


### DPA Builder

The DPA builder is automatically used by the `BuildDpa()` routine. It provides ability
to load the protected points from a specified json file (use an absolute path or a 
relative path to your script). 

It also provides a simple `default` builder that performs a distribution of points 
within the DPA with a simple strategy:

  - divide the DPA in 4 entities: front border, front zone, back border, back zone
  - distribute points along the 2 borders in a linear fashion, and within the 2 zones
  in a grid fashion. The number of points can be specified for each.
  - the division of front to back is done by cutting the DPA with an expanded US border. 
  Obviously inland DPA only contains a front border and front zone. The expansion parameter
  is configurable (by default 40km).
  - a minimum distance can be specified between protected points of each of these 4 entities
  separately. By default 0.2km for front border, 0.5km for front zone, 1km for front zone
  and 3km  for back zone. Note that the distance are approximative.

The total number of points distributed is variable depending on these condition. A common 
strategy would be:

  - define a large maximum number of points for each of the entities.
  - define a sensible distance between points.

Finally this module allows for plugging in new types of builders.
  
```python
  import dpa_builder
  # Create your own custom builder.
  def builder_fn(dpa_name, dpa_geometry, arg1, arg2, arg3):
     ... do something here to build the points...

  # Register the builder to the framework.
  dpa_builder.RegisterMethod('my_builder', builder_fn)

  # Now you can use it when building your DPA
  dpa = BuildDpa('East1', 
                 protection_points_method = 'my_builder (2500, "method1", 300)'
                 portal_dpa_filename='My_P-DPA.kml')
```


## Code Prerequisites

Reference models:

   - WinnForum ITM propagation reference model (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/propagation)   
   - WinnForum geo modules and geo data (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/geo)
   - WinnForum antenna gain models (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/antenna)
   - WinnForum common modules (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/common)

Python software and packages:

   - python 2.7 (https://www.python.org/download/releases/2.7/)
   - shapely (https://pypi.python.org/pypi/Shapely)
   - numpy (http://www.scipy.org/scipylib/download.html)
   - pykml (https://pythonhosted.org/pykml/installation.html)

## Test Data

The files described earlier are provided with unit tests `dpa_mgr_test.py` and
`move_list_test.py` which validates the code against non regression and proper behavior.

A set of example code are also provided that can be used to test the full code. See the
`dpa_mgr_example.py` and `move_list_example.py` files.

Finally a full small simulation (for time profiling purpose mainly) is also provided in
the [`tools/benchmark/time_dpa.py`](https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/tools/benchmark/time_dpa.py). 
This script use some of the `tools` facilities to automatically generate CBSDs in urban 
aread and is a good example on how to develop more fancy DPA related simulations.


## Copyrights and Disclaimers

This software was developed by employees of the National Institute of Standards and 
Technology (NIST), an agency of the Federal Government. Pursuant to title 17 United 
States Code Section 105, works of NIST employees are not subject to copyright 
protection in the United States and are considered to be in the public domain. 
Permission to freely use, copy, modify, and distribute this software and its 
documentation without fee is hereby granted, provided that this notice and 
disclaimer of warranty appears in all copies.

THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER EXPRESSED, 
IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT THE SOFTWARE 
WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS 
FOR A PARTICULAR PURPOSE, AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE 
DOCUMENTATION WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL 
BE ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT 
LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, 
RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED 
UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY 
PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR 
AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.

Distributions of NIST software should also include copyright and licensing 
statements of any third-party software that are legally bundled with the 
code in compliance with the conditions of those licenses. 

## References

[1] WInnForum Standards, Requirements for Commercial Operation in the 
U.S. 3550-3700 MHz Citizens Broadband Radio Service Band,  Working Document 
WINNF-TS-0112, Version V1.4.1-r2.0 (January 16, 2018).
