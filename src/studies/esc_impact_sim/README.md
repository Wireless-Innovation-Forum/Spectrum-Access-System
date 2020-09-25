# ESC impact simulator

Provides the `run_esc_impact_sim.py` simulator that evaluates the power
reduction on a network of CBSD caused by the ESC sensor protection.

The script simply runs the IAP algorithm. 


Note that the IAP code is slighly patched to save and return the final 
EIRP computed **after** the IAP loop is done. This is done by providing
an `iap_patch.py` that implements the required changes. 

## Installation

No special installation to be done, beyond the basic described in ../README.md.

## Running

See the `run_esc_impact_sim.py` module docstring for running instructions.

You can find CBSD deployment models in the Spectrum-Access-System/data/research/
directory, that were provided by NTIA for all DPA-related studies. Since they are 
based on DPA, the deployment model is only provided around a given DPA neighborhood
(typically 200+km from the DPA). 

A global deployment model valid for all the US might be provided in the future by NTIA.

For the purpose of testing your environment, a fake ESC FAD file is provided (single sensor
near East1). You can run:

```
    python run_esc_impact_sim.py --esc_fads=testdata/esc_test.json \
        --sensors=E01  \
        ../../../data/research/deployment_models/East1_reg_grant.json.zip
```
