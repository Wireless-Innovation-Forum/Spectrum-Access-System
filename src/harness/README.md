# The SAS Test Harness

This folder contains code and testcases for SAS certification test as defined in
"CBRS Architecture Test and Certification Specification" (WINNF-15-P-0061).

## Code prerequisites

*   Python 2.7.12 (https://www.python.org/downloads/release/python-2712/)
*   PycURL 7.43.0 (http://pycurl.io) compiled with OpenSSL
*   PyOpenSSL 16.2.0 (https://www.openssl.org/)

## Code location

*   **.**: Test framework.
    *   **./test_main.py**: Main entrypoint to run all test cases.
    *   **./cbsd_sas_interface.py**: All needed interfaces.
    *   **./cbsd_sas.py**: Implementation of all needed interfaces.
    *   **./fake_sas.py**: A fake SAS implementation, and a HTTP server which
        runs with the fake implementation.
*   **./tests**: Test cases, grouped by section in the test specification.
*   **./tests/testdata**: Data used in test cases.

## Certificate

A self-signed CA is used to generate all certs/keys in this folder, using RSA.
To support ECDSA ciphers in the fake SAS server (fake_sas.py) or PycURL client
(cbsd_sas.py), generate a new certificate using EC cryptography.
