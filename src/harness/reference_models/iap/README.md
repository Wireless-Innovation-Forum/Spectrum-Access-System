# The WinnForum R2-SGN-16 Iterative Allocation Process(IAP) Reference Implementation

This folder contains Python code and test data for calculation of the IAP 
according to the R2-SGN-16 requirement in the WINNF-TS-0061 document, Version V1.0.0-r5.1 
(January 17, 2018) [1].

## Main Interface 

The main routine to perform IAP on different incumbent types is  
`iap.performIAP()`. 

## Code Prerequisites

Reference models:

   - WInnForum ITM propagation reference model (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/propagation)   
   - WInnForum geo modules and geo data (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/geo)
   - WInnForum antenna gain models (https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/antenna)

Python software and packages:
   - python 2.7 (https://www.python.org/download/releases/2.7/)
   - shapely (https://pypi.python.org/pypi/Shapely)
   - numpy (http://www.scipy.org/scipylib/download.html)
   
## Test Data

To test the 
    `iap.performIapForGwpz(), 
     iap.performIapForPpa(), 
     iap.performIapForFssCochannel, 
     iap.performIapForFssBlocking,
     iap.performIapForEsc` 
routine for a GWPZ, PPA, FSS and ESC incumbent types respectively,
one can use the example given in the `iap_example.py` file along with the test 
data stored in the `\test_data` sub-folder. To run the example, use the command 
`python iap_example.py`.

## Copyrights and Disclaimers
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

## References

[1] WInnForum Standards, Requirements for Commercial Operation in the 
U.S. 3550-3700 MHz Citizens Broadband Radio Service Band,  Working Document 
WINNF-TS-0061, Version V1.0.0-r5.1 (January 17, 2018).
