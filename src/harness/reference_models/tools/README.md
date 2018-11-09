# Tools library

Code here is **NOT** supposed to be run directly in combination of SAS test 
harness. Instead it provides a set of useful tools for illustrative purpose 
or testing & simulation :
 
  - `docs/`: miscellaneous functional docs.
  
  - `examples/`: some example usage of the reference model: 
    * `example_fss_interference.py`: example of RSSI calculation for a FSS, 
    showing in particular how to call the propagation and antenna modules.
    
  - `benchmark/`: some benchmark and profiling scripts. 
  Good starting point if trying to speed up the reference models.
  
  - `studies/`: miscellaneous studies on key test harness issues. 
  Good starting point if trying to simulate some of SAS behavior.
  
  - various modules for helping on simulation or test setup:
    * cata_max_height: derive maximum allowed antenna height for CatA outdoor CBSDs.
    * sim_utils, testutils, entities: collection of useful routines and abstractions for testing and simulation.


### Code prerequisites

In addition of generic Winnforum prerequesite, some of the code requires:

* matplotlib (https://matplotlib.org/)

* cartopy (http://scitools.org.uk/cartopy/)

* scipy (https://www.scipy.org/)

These Python library can be installed with <code>pip</code>.

If issues in installing some of these libraries (for example in Windows), it 
is recommended to use the Miniconda (or full Anaconda) python distribution. 
Installation of individual packages can be done wth `conda install cartopy`, etc.
