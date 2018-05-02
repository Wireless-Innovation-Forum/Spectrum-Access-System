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
             ------------------root_ca ------------------
            /                     |                      \
           /                      |                       \
       sas_ca--------          cbsd_ca                  proxy_ca
       /    \        \            |                         \
      /      \        \           |                          \
   admin     sas    server     device_a                 domain_proxy
              |                device_c                 domain_proxy_1
          sas_corrupted        device_corrupted         domain_proxy_corrupted
          sas_wrong_type       device_wrong_type        domain_proxy_wrong_type
          sas_expired          device_expired           domain_proxy_expired
          sas_inapplicable     device_inapplicable      domain_proxy_inapplicable
          sas_blacklisted      device_blacklisted       domain_proxy_blacklisted
          sas_self_signed      device_self_signed       domain_proxy_self_signed

           --------root_ca (same as above, continued)---------
          /                       |                           \
         /                        |                            \
  revoked_sas_ca           revoked_cbsd_ca                revoked_proxy_ca
        |                         |                              \
        |                         |                               \
sas_cert_from_revoked_ca  device_cert_from_revoked_ca  domain_proxy_cert_from_revoked_ca
 
            ------------------non_cbrs_root_ca----------------------
           /                          |                             \
non_cbrs_root_signed_cbsd_ca   non_cbrs_root_signed_sas_ca  non_cbrs_root_signed_oper_ca
          |                           |                              |
non_cbrs_signed_device         non_cbrs_root_signed_sas     non_cbrs_signed_domain_proxy


                             unrecognized_ca
                                   |
                          unrecognized_device
                          unrecognized_sas
                          unrecognized_domain_proxy
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

* `device_a.[cert|key]`: leaf CBSD device certificate signed by `cbsd_ca`.
  Used to authenticate the device_a when connecting to a SAS server.

* `device_c.[cert|key]`: leaf CBSD device certificate signed by `cbsd_ca`.
  Used to authenticate the device_c when connecting to a SAS server.

* `admin.[cert|key]`: leaf certificate signed by `sas_ca`.
  Used to authenticate the test harness when connecting to the SAS testing API.

* `proxy_ca.cert`: intermediate Domain Proxy certificate authority for
  all Domain Proxy Operator, signed by `root_ca`.

* `domain_proxy.[cert|key]`: leaf Domain Proxy Operator certificate signed by
  `proxy_ca`.
  Used to authenticate a Domain proxy Operator connecting to a SAS server.

* `ca.cert`: trusted certificates chain bundle. Contains all certificate CA
  used to verify the server chain and the client chain. Basically the
  concatenation of all intermediate certificate CA and root CA.

* `revoked_sas_ca.cert`: intermediate SAS certificate authority signed by the same `root_ca` and status is
revoked. Used on security test test_WINNF_FT_S_SSS_16.

* `revoked_cbsd_ca.cert`: intermediate CBSD certificate authority signed by the same `root_ca` and status is
revoked. Used on security test test_WINNF_FT_S_SCS_16.

* `revoked_proxy_ca.cert`: intermediate Domain Proxy certificate authority signed by the same `root_ca` and status is
revoked. Used on security test test_WINNF_FT_S_SDS_16.

* `unrecognized_root_ca.cert`: root certificate authority to generate unrecognized device
  Self signed.
  
* `unrecognized_device.[cert|key]`: leaf CBSD device certificate signed by
  `unrecognized_root_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SCS_6.

* `unrecognized_domain_proxy.[cert|key]`: leaf Domain Proxy certificate signed by
  `unrecognized_root_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SDS_6.

* `device_corrupted.cert`: corrupted 'device_a.cert' certificate where the 20th character have been changed.
  Used on security test test_WINNF_FT_S_SCS_7.
  
* `device_self_signed.cert`: self signed certificate of client (CBSD) signed by device_a.key
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
  
* `device_wrong_type.cert`: leaf CBSD certificate signed using server.csr 
  Used on security test test_WINNF_FT_S_SCS_10.
  
* `device_blacklisted.[cert|key]`: A leaf CBSD device certificate that is blacklisted using CRL. 
  Used on security test test_WINNF_FT_S_SCS_11.
  
* `device_expired.[cert|key]`: leaf CBSD device expired certificate
  Used on security test test_WINNF_FT_S_SCS_12.

* `device_inapplicable.[cert|key]`: leaf CBSD device inapplicable fields certificate
  Used on security test test_WINNF_FT_S_SCS_15.

* `device_cert_from_revoked_ca.[cert|key]`: leaf CBSD device certificate signed by revoked intermediate CA 
  `revoked_cbsd_ca` and corresponding trusted client certificate bundle.
   Used on security test test_WINNF_FT_S_SCS_16.

* `domain_proxy_corrupted.cert`: corrupted 'domain_proxy.cert' certificate where the 20th character have been changed.
  Used on security test test_WINNF_FT_S_SDS_7.

* `domain_proxy_wrong_type.cert`: domain_proxy certificate signed using server.csr 
  Used on security test test_WINNF_FT_S_SDS_10.
  
* `domain_proxy_blacklisted.[cert|key]`: A leaf domain proxy certificate that is blacklisted using CRL. 
  Used on security test test_WINNF_FT_S_SDS_11.
  
* `domain_proxy_expired.[cert|key]`: domain_proxy device expired certificate
  Used on security test test_WINNF_FT_S_SDS_12.

* `domain_proxy_inapplicable.[cert|key]`: domain_proxy device inapplicable fields certificate
  Used on security test test_WINNF_FT_S_SDS_15.
  
* `domain_proxy_cert_from_revoked_ca.[cert|key]`: domain proxy certificate signed by revoked intermediate CA 
  `revoked_proxy_ca` and corresponding trusted client certificate bundle.
   Used on security test test_WINNF_FT_S_SDS_16.

* `unrecognized_sas.[cert|key]`: leaf SAS certificate signed by
  `unrecognized_root_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SSS_6.
  
* `sas_corrupted.cert`: corrupted 'sas.cert' certificate where the 20th character have been changed.
  Used on security test test_WINNF_FT_S_SSS_7.
  
* `sas_self_signed.cert`: self signed certificate of SAS signed by sas.key
  Used on security test test_WINNF_FT_S_SSS_8.
  
* `non_cbrs_root_signed_sas_ca.cert`: an intermediate SAS certificate authority for SAS,
  signed by `non_cbrs_root_ca`.
  Used on security test test_WINNF_FT_S_SSS_9.
  
* `non_cbrs_signed_sas.[cert|key]`: leaf SAS certificate signed by
  `non_cbrs_root_signed_sas_ca`, and corresponding trusted client certificates bundle.
  Used on security test test_WINNF_FT_S_SSS_9.
  
* `sas_blacklisted.[cert|key]`: A leaf SAS certificate that is blacklisted using CRL.
  Used on security test test_WINNF_FT_S_SSS_11.

* `sas_expired.[cert|key]`: leaf SAS expired certificate
  Used on security test test_WINNF_FT_S_SSS_12.

* `sas_cert_from_revoked_ca.[cert|key]`: leaf SAS certificate signed by revoked intermediate CA 
  `revoked_sas_ca` and corresponding trusted client certificate bundle.
   Used on security test test_WINNF_FT_S_SSS_16.
