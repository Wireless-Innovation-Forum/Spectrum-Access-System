# Repository for research/studies related data

Currently are provided the following data

## Deployment Models

The per-DPA deployment model used by numerous studies  done by NTIA and NIST. 
Useful for any study requiring a more realistic set of CBSD deployment models
taking into account population, etc..

The data is provided in the `reg_grant` Zipped JSON format holding registration 
and grant requests.
To read the data, one can simply use the function:

  `reference_models.tools.sim_utils.ReadTestHarnessConfigFile(<file_name>)`

