## Reference models

### Content
This folder provides the reference models to be used for SAS testing.

This includes:

  - `geo/`: the geo data drivers and distance calculation routines.
  - `propagation/`: the Winnforum ITM and Hybrid propagation models.
  - `antenna/`: the antenna gain calculation.
  - `ppa/`: the PPA zones creation.
  - `interference/`: interference calculation on protected entities (except dpa).
  - `dpa/`: the DPA move list calculation.
  - `iap/`: The IAP (Iterative Allocation Process) algorithm.
  - `pre_iap_filtering/`: Pre IAP filtering, including purge algorithms.
  
The `tools/examples/` folder provides an example of using the models for FSS protection,
which exercise the ITM model, antenna gain calculation and geo routines.

### Setup

The reference models support Python 3.11 through 3.15. Python 3.15 is the default
selected by the repository's `.python-version`; Python 2 is no longer supported.
Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and a C++
compiler, then run these commands from the `Spectrum-Access-System` repository
root:

```sh
uv sync --locked
uv run --locked make -C src/harness/reference_models/propagation PYTHON=python
```

Rebuild the native propagation extensions whenever you change Python versions.
See the [propagation README](propagation/README.md) for Windows build commands and
geographic data setup. NED and NLCD data default to the sibling `Common-Data`
repository when local SAS data directories are absent; set `CBRS_COMMON_DATA_DIR`
to use another Common-Data checkout. Extract the required tiles before using the
models with production data.

Applications importing these models must include `src/harness` in `PYTHONPATH`.
The unit test runner below configures its import paths and working directory.

### Setup validation

From the repository root, run:

```sh
uv run --locked python run_unit_tests.py
```

This runs all local SAS unit tests, including the reference models and their
bundled geographic fixtures. Six tests requiring production NED/NLCD tiles are
explicitly skipped by default. After extracting the required Common-Data tiles,
include those tests with:

```sh
uv run --locked python run_unit_tests.py --with-production-data
```

On Unix systems, `src/harness/reference_models/run_all_tests_py3.sh` delegates to
the same repository runner from any working directory and accepts the same
arguments. For example, append `--with-production-data` or `-k TestItm`.
These local tests are separate from the SAS compliance suite, which requires a
configured SAS endpoint and is launched through `src/harness/test_main.py`.
