This directory contains the certificates used by the test harness to connect
with the SAS under test.

NOTE: Before running the tests you must provide the certificates described in
this file:
- The shell script `generate_fake_certs.sh` can be used to generate fake version
  to be used with the `fake_sas.py` implementation.
- To run against a real SAS, please generate your own certificates.

The various certificates follow the PKI structure defined on the "CBRS COMSEC TS
WINNF-15-S-0065" document. Naming and base configuration are issued from
https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/cert

```
                    root_ca                                     unknown_ca
                    /      \                                         |
                   /        \                                  unknown_device
              sas_ca        cbsd_ca                          
              /  |            \                             
             /   |             \                            
            /    |              \                            
  admin_client  server         client|device_[a|c]                
                           
```

Refer to the `generate_fake_certs.py` script and `../../cert/openssl.cnf` file
to get command line example on how to generate required certificates and keys.

Required certificates are:

* `root_ca.cert`: root certificate authority for all certificates used by SAS
  related components (SAS instance, CBSD, domain proxy, PAL ...). Self signed.

* `sas_ca.cert`: intermediate SAS certificate authority for all certificates
  related to a SAS server implementation. Signed by `root_ca`.

* `server.[cert|key]`: leaf SAS fake server certificate signed by `sas_ca`.

* `cbsd_ca.cert`: intermediate CBSD certificate authority for all CBSD device,
  signed by `root_ca`.

* `client.[cert|key]`: leaf CBSD device certificate signed by `cbsd_ca`.
  Used in all tests not concerned with security-related features.

* `device_a.[cert|key]`: leaf CBSD device certificate signed by `cbsd_ca`.
  Used to authenticate the device_a when connecting to a SAS server.

* `device_c.[cert|key]`: leaf CBSD device certificate signed by `cbsd_ca`.
  Used to authenticate the device_c when connecting to a SAS server.

* `admin_client.[cert|key]`: leaf certificate signed by `sas_ca`.
  Used to authenticate the test harness when connecting to the SAS testing API.

* `ca.cert`: trusted certificates chain bundle. Contains all certificate CA
  used to verify the server chain and the client chain. Basically the
  concatenation of all intermediate certificate CA and root CA.

* `unknown_ca.cert`: root certificate authority to generate unknown device
  (valid device not managed by the SAS instance under test). Self signed.

* `unknown_device.[cert|key]`: leaf CBSD device certificate signed by
  `unknown_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SCS_2.

* `unrecognized_root_ca.cert`: root certificate authority to generate unrecognized device
  Self signed.

* `client_expired.[cert|key]`: leaf CBSD device expired certificate
  Used on security test test_WINNF_FT_S_SCS_12.

* `client_inapplicable.[cert|key]`: leaf CBSD device inapplicable fields certificate
  Used on security test test_WINNF_FT_S_SCS_15.
 
* `[root_ca|cbsd_ca].crl`: CRL is generated for root_ca and cbsd_ca after revoke intermediate CA cbsd_ca
  `WINNF_FT_S_SCS_16_ca.cert`: CA trusted chain appended with CRL of root and intermediate CA
  Used on security test test_WINNF_FT_S_SCS_16
 
* `short_lived_client.[cert|key]`: leaf CBSD device will expire in short duration mentioned in generate_fake_certs.sh 
  Used on security test test_WINNF_FT_S_SCS_17,test_WINNF_FT_S_SCS_18 and test_WINNF_FT_S_SCS_19 
  
