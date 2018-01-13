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
                 |---------------root_ca                                                             
                 |               /      \                               
                 |              /        \                              
               dp_ca       sas_ca        cbsd_ca                          
              /            /  |            \                             
            /             /   |             \                            
          /              /    |              \                            
     dp_client   admin_client server        client|device_[a|c]
   corrupted_dp                


      unknown_ca     
           |         
     unknown_device  
                      

  unrecognized_ca              non_cbrs_root_ca
        |                           |
 unrecognized_dp           non_cbrs_root_signed_dp_ca
                                    |
                              non_cbrs_signed_dp
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

* `dp_ca.cert`: intermediate Domain Proxy certificate authority signed by `root_ca`.

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

* `dp_client.[cert|key]`: Domain Proxy certificate signed by DP CA.
  Used in all tests not concerned with security-related features.

* `unrecognized_dp.[cert|key]`: Domain Proxy certificate signed by
  `unrecognized_root_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SDS_6.
 
* `corrupted_dp.cert`: corrupted 'dp_client.cert' certificate. This is generated
  during the execution of test_WINNF_FT_S_SDS_7
  Used on security test test_WINNF_FT_S_SDS_7.

* `self_signed_dp_client.cert`: self signed certificate of domain proxy client signed by dp_client.key
  Used on security test test_WINNF_FT_S_SDS_8.

* `non_cbrs_root_ca.cert`: a root certificate authority that is not approved as a CBRS root CA
  Self signed.
  Used on security test test_WINNF_FT_S_SDS_9.

* `non_cbrs_root_signed_dp_ca.cert`: an intermediate DP certificate authority for domain proxy client,
  signed by `non_cbrs_root_ca`.
  Used on security test test_WINNF_FT_S_SDS_9.

* `non_cbrs_signed_dp.[cert|key]`: leaf DP certificate signed by
  `non_cbrs_root_signed_dp_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SDS_9.

* `sas_ca_signed_dp_client.cert`: leaf DP certificate signed by SAS CA ('sas_ca') 
  instead of DP CA ('dp_ca').
  Used on security test test_WINNF_FT_S_SDS_10.

* `dp_expired.[cert|key]`: Domain Proxy expired certificate
  Used on security test test_WINNF_FT_S_SDS_12.

* `dp_client_inapplicable.[cert|key]`: leaf DP device inapplicable fields certificate
  Used on security test test_WINNF_FT_S_SDS_15.

* `[root_ca|dp_ca].crl`: CRL is generated for root_ca and dp_ca after revoke intermediate CA dp_ca
  `WINNF_FT_S_SDS_16_ca.cert`: CA trusted chain appended with CRL of root and intermediate CA
  Used on security test test_WINNF_FT_S_SDS_16
 
* `short_lived_dp_client.[cert|key]`: leaf DP device will expire in short duration mentioned in generate_fake_certs.sh 
  Used on security test test_WINNF_FT_S_SDS_17,test_WINNF_FT_S_SDS_18 and test_WINNF_FT_S_SDS_19 
 
