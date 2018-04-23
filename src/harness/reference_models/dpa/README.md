# The WinnForum R2-SGN-24 DPA Protection Procedure Reference Implementation

This folder contains Python code and test data for calculation of the DPA move-list 
according to the R2-SGN-24 requirement in the WINNF-TS-0112 document, Version V1.4.1-r2.0 
(January 16, 2018) [1].

## Main Interface 

The main routine to find which CBSD grants are on the move-list is:

    `Dpa.CalcMoveList()`

## Code Prerequisites

Reference models:

   - WinnForum ITM propagation reference model (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/propagation)   
   - WinnForum geo modules and geo data (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/geo)
   - WinnForum antenna gain models (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/antenna)

Python software and packages:

   - python 2.7 (https://www.python.org/download/releases/2.7/)
   - shapely (https://pypi.python.org/pypi/Shapely)
   - numpy (http://www.scipy.org/scipylib/download.html)
   
## Test Data

To test the Move List for a co-channel offshore DPA protection, one can use
the example given in the `move_list_example.py` file along with the test data 
stored in the `\test_data` sub-folder. To run the example, use the command:

    `python move_list_example.py`.

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
