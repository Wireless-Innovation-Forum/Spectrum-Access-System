## Benchmarks

This directory holds a bunch of benchmark code for various typical test case.
Currently:

  - `time_prop.py`: benchmark the propagation timing calculation for one link.
  - `time_dpa.py`: realistic benchmark of the DPA move list calculation for
    a full DPA.

It also provide some profiling script to better understand the reference models
code bottleneck:
  
    - `prof_agg_interf.py`: profiling of aggregate interference calculation.
    - `prof_prop.py`: profiling of propagation models.

