## Extended-HATA Python implementation

This module contains a Python implementation of the Extended HATA model
described in the [NTIA Technical Report 15-517](https://www.ntia.doc.gov/report/2015/35-ghz-exclusion-zone-analyses-and-methodology).

The code here is based upon the [NIST implementation](https://github.com/usnistgov/eHATA).

The entry points are the functions `ExtendedHata_PropagationLoss` and `ExtendedHata_MedianBasicPropLoss`.
These functions take as parameters the frequency, base station and mobile station heights. The terrain
profile to be used is in the same format as the ITM terrain profile information.

There are also variability functions `EHataStdDevUrban` and `EHataStdDevSuburban` which return the
variability in the model estimate for these propagation environments.

The implementation relies on the numpy module.

