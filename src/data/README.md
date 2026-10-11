# Data retrieval and processing scripts

This folder holds some of the scripts that were used to retrieve and preprocess data
used in the SAS reference implementation.

NOTE: other scripts related to US border zone are kept in the Winnforum 
[Common-Data repository](https://github.com/Wireless-Innovation-Forum/Common-Data), 
under the `scripts/` folder.

These scripts are provided only for documenting the process in generating those data.
You DO NOT need to run the scripts unless you want to verify the process.

The scripts support Python 3.11–3.15. Install their optional spreadsheet dependencies
with `uv sync --locked --extra scripts`, then use `uv run --locked --extra scripts python`
to run a script under `src/data/`. The original historical data were generated
with Python 2. Legacy conversions live in `legacy/`; their FCC spreadsheet and
radar files are under `data/fcc/legacy/` in the repository root. Retrieval tools
still depend on the availability of their historical upstream services.
