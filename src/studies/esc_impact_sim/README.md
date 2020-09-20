# ESC impact simulator

Provides the `run_esc_impact_sim.py` simulator that evaluates the power
reduction on a network of CBSD caused by the ESC sensor protection.

The script simply runs the IAP algorithm. 

See that module docstring for running instructions.

Note that the IAP code is slighly patched to save and return the final 
EIRP computed **after** the IAP loop is done. This is done by providing
an `iap_patch.py` that implements the required changes. 
