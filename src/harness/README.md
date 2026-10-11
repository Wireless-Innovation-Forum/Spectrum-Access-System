# The SAS Test Harness

This folder contains code and testcases for SAS certification test as defined in
"CBRS Architecture Test and Certification Specification" (WINNF-15-S-0061).

## Code prerequisites

Python 3.11–3.15 and the root `pyproject.toml` dependencies are required.
Use `uv sync --locked` to install the default development group, build the
propagation models with `uv run make`, and run tests with `uv run python`.
See [the repository setup instructions](../../README.md) for installation,
Common-Data configuration, and optional GDAL drivers. Run commands here with
`uv run --locked python` from the project environment.

Security tests use maintained cryptography, pyOpenSSL, and OpenSSL-enabled
PycURL. The configured SAS must provide its administrative interface and current
lab certificates. Python 2 and obsolete cryptography backports are unsupported.

## Code location

*   **.**: Test framework.
    *   **./test_main.py**: Main entrypoint to run all test cases.
    *   **./sas_interface.py**: All needed interfaces.
    *   **./sas_testcase.py**: Implementation of helper functions needed for test cases.
    *   **./sas.py**: Implementation of all needed interfaces.
    *   **./fake_sas.py**: A fake SAS implementation, and a HTTP server which
        runs with the fake implementation.
*   **./testcases**: Test cases, grouped by section in the test specification.
*   **./testcases/testdata**: Data used in test cases.

## Certificate

A self-signed CA is used to generate all certs/keys in this folder, using RSA.
To support ECDSA ciphers in the fake SAS server (fake_sas.py) or PycURL client
(sas.py), generate a new certificate using EC cryptography.
