# DPA Calculator

## Docker
### Build
From the root directory, run
```shell
docker build . -f src/harness/cu_pass/dpa_calculator/Dockerfile -t dpa
```

### Run
Mount data directory volumes and use environment variables matching the container volume paths.

```shell
docker run \
  -v "<PATH_TO_LOCAL_NED_DATA>:/cu_pass/dpa/data/ned" \
  -v "<PATH_TO_LOCAL_NLCD_DATA>:/cu_pass/dpa/data/nlcd" \
  -v "<PATH_TO_LOCAL_POPULATION_DATA>:/cu_pass/dpa/data/pop/pden2010_block" \
  --env TERRAIN_DIR=/cu_pass/dpa/data/ned \
  --env LANDCOVER_DIR=/cu_pass/dpa/data/nlcd \
  --env POPULATION_DIRECTORY_CENSUS=/cu_pass/dpa/data/pop/pden2010_block \
  dpa
```
