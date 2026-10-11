## The SAS Testing and Interoperability Repository

This repository contains code and data for testing the compliance
of Spectrum Access System (SAS) software. The SAS is defined by
the FCC in proceeding 12-354 as the system authorizing priority
access and general access to the 3550-3700MHz Citizens Broadband
Radio Service.

This repository contains procedures, documentation, and tests
for such software, and for the devices authorized by it.

To contribute, please first read the CONTRIBUTING file in the
repository for instructions.

### Data

Some of the required data is provided in folder `data/`. Scripts used to
retrieve or generate these data are in src/data/.

USGS NED Terrain and NLCD Land cover data are not provided as part of the
data/ folder, but kept instead in a separate Git repository found at:
 https://github.com/Wireless-Innovation-Forum/Common-Data

The process relies in cloning that repository, unzipping the geo data and
pointing the SAS reference models to point to those data.

See the corresponding [README.md](https://github.com/Wireless-Innovation-Forum/Common-Data/README.md)
for more details on the integration of those geo data for use with SAS.


### Python and dependency support

The code targets Python 3.11–3.15, with Python 3.15.0 as the current stable
runtime. Python 2 and Python 3.10 or earlier are no longer supported. Dependency
ranges and uv.lock select maintained releases compatible with each interpreter;
there is no fallback to PyCrypto or obsolete OpenSSL bindings. The SAS security
conformance cases still use current pyOpenSSL and PycURL to exercise the TLS 1.2
cipher suites required by their specifications. Protocol SHA-1 fingerprints and
FAD checksums remain unchanged.

Use a C++ compiler to build the ITM and eHata propagation extensions. These use
setuptools, including on Python versions where distutils has been removed.
Build again whenever changing Python versions. Binary wheels of NumPy, Shapely,
lxml, cryptography, and PycURL normally avoid separate native development
packages. Source installations may require their upstream build prerequisites;
PycURL must use an OpenSSL backend for the security cases.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from this repository root:

```sh
uv python install 3.15.0
uv sync --locked
uv run --locked python --version
uv run --locked make -C src/harness/reference_models/propagation PYTHON=python
uv run --locked python run_unit_tests.py
uv run --locked python schema/verify_schema.py
```

The exact `.python-version` pin requests final Python 3.15.0. Upgrade uv if its
Python download catalog does not yet contain that release, or use
`uv sync --locked --python /path/to/python3.15`. Confirm the version is final
before testing. Python 3.11–3.14 use the same lockfile with an explicit
`--python 3.11` (or other supported version) on each uv command.

`pyproject.toml` and `uv.lock` are authoritative. The default development group
includes build/test tools; use `uv sync --locked --no-dev` for runtime only.
`uv sync --locked --extra scripts` installs the historical spreadsheet tools.
Compatibility `requirements*.txt` exports remain available for pip consumers;
regenerate them with `uv export` after dependency changes. Use `uv lock --upgrade`
and rerun tests to refresh dependency versions deliberately.

The local runner includes transport tests, reference models, geometry libraries,
and harness helper tests. Six tests using production NED/NLCD tiles are explicitly
skipped by default; use `uv run --locked python run_unit_tests.py --with-production-data` after configuring/extracting those tiles to include them.
`--with-gdal` additionally enables the optional population raster driver tests.
The spreadsheet conversion test also requires `--extra scripts`; CI installs
that extra so it exercises the historical spreadsheet tools.

The data retrieval scripts still depend on upstream services and files; syntax
compatibility does not establish that those historical services remain available.

### The four repositories together

Keep these checkouts as siblings:

```text
GitRepos/
  Citizens-Broadband-Radio-Service-Device/
  Spectrum-Access-System/
  Spectrum-Access_System-Release-2/
  Common-Data/
```

Common-Data supplies terrain/land-cover datasets and an optional independently
installable `winnf` library. This repository retains its own reference models;
installing Common-Data alone does not build these local propagation extensions.
`CBRS_COMMON_DATA_DIR` can point to the Common-Data checkout in another location.
When local SAS NED/NLCD folders are absent, the sibling checkout is used.
Unpack the required geographical tiles using the Common-Data README before
running tests requiring production terrain or land cover. SAS ITU, county,
FCC, and zone data continue to come from this repository's `data/` directory.

```sh
uv --directory ../Common-Data sync --locked
export CBRS_COMMON_DATA_DIR="$(cd ../Common-Data && pwd)"
```

The device simulator has its own requirements and configuration; follow its
README. Release 2 currently contains only a placeholder test file and does not
supply an executable Release 2 compliance suite.

Configure `src/harness/sas.cfg` and `test.cfg` with your SAS endpoints and lab
settings, and generate/provide current certificates as described in
[src/harness/certs/README.md](src/harness/certs/README.md). Then start the actual
compliance suite:

```sh
cd src/harness
uv run --locked python test_main.py
```

Unit transport tests generate temporary fresh certificates and contact only
local servers. They do not require or overwrite lab credentials. Compliance
cases need a configured SAS under test and its administrative interface.

### Optional GDAL population drivers

`src/lib/usgs_pop` and some data tooling require GDAL. Install a current native
GDAL library and the Python bindings matching **that library's version**.
`requirements-gdal.txt` is the optional dependency export; do not blindly install
bindings newer than your native library. For example, after installing the GDAL
headers and command-line tools:

```sh
uv pip install --python .venv/bin/python "GDAL==$(gdal-config --version)"
# Keep manually installed, version-matched GDAL while running:
uv run --no-sync python run_unit_tests.py --with-gdal
```

Alternatively, `conda env create -f conda-environment.yml` uses conda-forge's
matching GDAL library/bindings. Follow that file's uv instructions to synchronize
the Python dependencies without removing the conda GDAL bindings. You may
change its Python constraint to an older supported version. Conda availability
of the newest Python is platform-dependent; use the uv-managed setup if needed.
