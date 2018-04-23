## Reference models

### Content
This folder provides the reference models to be used for SAS testing.

This includes:

  - `geo/`: the geo data drivers and distance calculation routines.
  - `propagation_models/`: the Winnforum ITM and Hybrid propagation models.
  - `antenna/`: the antenna gain calculation.
  - `ppa/`: the PPA zones creation.
  - `interference/`: interference calculation on protected entities (except dpa).
  - `move_list_calc/`: the DPA move list calculation.
  - `iap/`: The IAP (Iterative Allocation Process) algorithm.
  - `pre_iap_filtering/`: Pre IAP filtering, including purge algorithms.
  
The `examples/` folder provides an example of using the models for FSS protection,
which exercise the ITM model, antenna gain calculation and geo routines.

### Setup
In order to use the reference models, you should:
 - have your PYTHONPATH pointing to the top level harness/ directory
 - configure the geo/CONFIG.py paths towards the geo databases.
 - compile the propagation model extension modules
 
See the specific README.md for more details. 

### Setup Validation
You can validate your setup by using the script:

```
    python test_config.py
```

If everything properly installed, the script will end with a SUCCESS message,
otherwise follow the provided instruction to complete your setup.

You can also validate that the scripts are performing as expected by launching
the unit tests:

In Linux:
```
    ./run_all_tests.sh
```

In Windows:

```
    python -m unittest discover -p '*_test.py'
```

