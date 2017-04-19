# The SAS Test Harness

This folder contains code and testcases for SAS certification test as defined in
"CBRS Architecture Test and Certification Specification" (WINNF-15-P-0061).

## Code prerequisites

*   Python 2.7.12 (https://www.python.org/downloads/release/python-2712/)
*   PycURL 7.43.0 (http://pycurl.io)

## Code location

*   **.**: Test framework.
    *   **./test_main.py**: Main entrypoint to run all test cases.
    *   **./sas_interface.py**: All needed interfaces.
    *   **./sas.py**: Implementation of all needed interfaces.
    *   **./fake_sas.py**: A fake SAS implementation, and a HTTP server which
        runs with the fake implementation.
*   **./testcases**: Test cases, grouped by section in the test specification.
*   **./testcases/testdata**: Data used in test cases.

## Certificate

A self-signed CA is used to generate all certs/keys in this folder, using RSA.
To support ECDSA ciphers in the fake SAS server (fake_sas.py) or PycURL client
(sas.py), generate a new certificate using EC cryptography.


## Known Issues

The test harness is using pycurl packages and assumes they are compiled with openssl support.  If the packages were compiled with nss support insteadt this esults in “Uknown cipher” error when the harness is started.  To avoid this use the pycurl package with openssl support.  If not possible the following changes can be made to sas.py

HTTP_TIMEOUT_SECS = 30

CA_CERT = 'ca.cert'

#ssl_cert = 'client.cert'

#ssl_key = 'client.key'

#CIPHERS = [

#   'AES128-GCM-SHA256', 'AES256-GCM-SHA384', 'ECDHE-RSA-AES128-GCM-SHA256'
#]

CIPHERS = [
     'ecdhe_rsa_aes_128_gcm_sha_256'
     ]

