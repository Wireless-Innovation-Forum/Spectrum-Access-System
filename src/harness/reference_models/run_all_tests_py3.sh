#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/../../.." && pwd)

exec uv run --project "$repo_root" --locked python "$repo_root/run_unit_tests.py" "$@"
