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
                  -------------root_ca --------------------------------------                
                 /                   \         				     \                 
                /                     \         			      \            
          sas_ca--------              cbsd_ca   			   proxy_ca
          /    \        \                \              	  		\
         /      \        \                \              	  		 \
   admin_client  server  sas     client|device_[a|c]|corrupted_client        domain_proxy|
		          |       wrong_type_client|client_expired           corrupted_domain_proxy|
                   corrupted_sas|  client_inapplicable|                    wrong_type_domain_proxy|
                   sas_expired|    blacklisted_client                      domain_proxy_expired|
                   blacklisted_client                                   domain_proxy_inapplicable|
                                                                        blacklisted_client

 
unrecognized_ca             non_cbrs_root_ca----------------------------------------------
         |                     |                                 \	                  \
unrecognized_device|        non_cbrs_root_signed_cbsd_ca   non_cbrs_root_signed_sas_ca  non_cbrs_root_signed_oper_ca
unrecognized_sas               |                                  |                        |
unrecognized_domain_proxy   non_cbrs_signed_device         non_cbrs_root_signed_sas     non_cbrs_signed_domain_proxy
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

* `proxy_ca.cert`: intermediate Domain Proxy certificate authority for
  all Domain Proxy Operator, signed by `root_ca`.

* `domain_proxy.[cert|key]`: leaf Domain Proxy Operator certificate signed by
  `proxy_ca`.
  Used to authenticate a Domain proxy Operator connecting to a SAS server.

* `ca.cert`: trusted certificates chain bundle. Contains all certificate CA
  used to verify the server chain and the client chain. Basically the
  concatenation of all intermediate certificate CA and root CA.

* `unrecognized_root_ca.cert`: root certificate authority to generate unrecognized device
  Self signed.
  
* `unrecognized_device.[cert|key]`: leaf CBSD device certificate signed by
  `unrecognized_root_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SCS_6.

* `unrecognized_domain_proxy.[cert|key]`: leaf Domain Proxy certificate signed by
  `unrecognized_root_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SDS_6.

* `corrupted_client.cert`: corrupted 'client.cert' certificate where the 20th character have been changed.
  Used on security test test_WINNF_FT_S_SCS_7.
  
* `self_signed_client.cert`: self signed certificate of client (CBSD) signed by client.key
  Used on security test test_WINNF_FT_S_SCS_8.
  
* `non_cbrs_root_ca.cert`: a root certificate authority that is not approved as a CBRS root CA
  Self signed.
  Used on security test test_WINNF_FT_S_SCS_9.
  
* `non_cbrs_root_signed_cbsd_ca.cert`: an intermediate CBSD certificate authority for CBSD devices,
  signed by `non_cbrs_root_ca`.
  Used on security test test_WINNF_FT_S_SCS_9.
  
* `non_cbrs_signed_device.[cert|key]`: leaf CBSD certificate signed by
  `non_cbrs_root_signed_cbsd_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SCS_9.
  
* `wrong_type_client.cert`: leaf CBSD certificate signed using server.csr 
  Used on security test test_WINNF_FT_S_SCS_10.
  
* `blacklisted_client.[cert|key]`: leaf CBSD device certificate is blacklisted 
  Used on security test test_WINNF_FT_S_SCS_11, test_WINNF_FT_S_SDS_11 and test_WINNF_FT_S_SSS_11..
  
* `client_expired.[cert|key]`: leaf CBSD device expired certificate
  Used on security test test_WINNF_FT_S_SCS_12.

* `client_inapplicable.[cert|key]`: leaf CBSD device inapplicable fields certificate
  Used on security test test_WINNF_FT_S_SCS_15.

* `corrupted_domain_proxy.cert`: corrupted 'domain_proxy.cert' certificate where the 20th character have been changed.
  Used on security test test_WINNF_FT_S_SDS_7.

* `wrong_type_domain_proxy.cert`: domain_proxy certificate signed using server.csr 
  Used on security test test_WINNF_FT_S_SDS_10.
  
* `domain_proxy_expired.[cert|key]`: domain_proxy device expired certificate
  Used on security test test_WINNF_FT_S_SDS_12.

* `domain_proxy_inapplicable.[cert|key]`: domain_proxy device inapplicable fields certificate
  Used on security test test_WINNF_FT_S_SDS_15.

* `unrecognized_sas.[cert|key]`: leaf SAS certificate signed by
  `unrecognized_root_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SSS_6.
  
* `corrupted_sas.cert`: corrupted 'sas.cert' certificate where the 20th character have been changed.
  Used on security test test_WINNF_FT_S_SSS_7.
  
* `self_signed_sas.cert`: self signed certificate of SAS signed by sas.key
  Used on security test test_WINNF_FT_S_SSS_8.
  
* `non_cbrs_root_signed_sas_ca.cert`: an intermediate SAS certificate authority for SAS,
  signed by `non_cbrs_root_ca`.
  Used on security test test_WINNF_FT_S_SSS_9.
  
* `non_cbrs_signed_sas.[cert|key]`: leaf SAS certificate signed by
  `non_cbrs_root_signed_sas_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SSS_9.

* `sas_expired.[cert|key]`: leaf SAS expired certificate
  Used on security test test_WINNF_FT_S_SSS_12.

