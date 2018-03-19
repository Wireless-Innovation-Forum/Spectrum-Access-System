# Simple CRL Server
The simple CRL server implements a simple CRL server. The default URL for this CRL server
is http://localhost:9007/ca.crl. This a simple HTTP server that responds only to this URL and provides
the ca.crl file present in the harness/certs/crl/ directory. When the simple CRL server is started
it creates a CRL file for the intermediate CAs (CBSD CA, DP CA and SAS CA) and the root CA. All the
CRL files are concatenated to create CRL chain file named ca.crl. The first time the simple CRL server
started the ca.crl file may not have any certificates revoked.

The simple CRL server provides menu options to revoke any CBSD or DP or SAS certificate. It lists
all the certificate files and revokes the certificates using the appropriate intermediate CA based
on the certificate type. The ca.crl chain is then regenerated to include the revoked certificate's
sequence number. Another menu option is to update the CRL URL. If the URL mentioned in the CDP 
extension field of the certificates needs to be changed then this option can be used. It updates 
the [ crl_section ] in the openssl.cnf file and invokes the script 'generate_fake_certs.sh' to 
generate the certificates with the updated extension field.


### Starting CRL Server:
Go to harness directory and execute **python simple_crl_server.py**<br/>
The simple CRL server will start and generate a CRL file based on the contents from the **harness/certs**
directory.<br/> The crl file will not have any certificates revoked when started for the first time.<br/>
The ca.crl file at the location "certs/XXXX" will be served by this simple CRL server.<br/>
<pre>
<code>
$ python simple_crl_server.py 
\n\n Generate CRL for root_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for sas_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for proxy_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for cbsd_ca
Using configuration from ../../../cert/openssl.cnf
[INFO] 2018-03-19 16:40:27,542 crl/ca.crl CRL chain is created successfully
[INFO] 2018-03-19 16:40:27,065 CRL Server has been started 
   _____ _____  _         _____
  / ____|  __ \| |       / ____|
 | |    | |__) | |      | (___   ___ _ ____   _____ _ __
 | |    |  _  /| |       \___ \ / _ \ '__\ \ / / _ \ '__|
 | |____| | \ \| |____   ____) |  __/ |   \ V /  __/ |
  \_____|_|  \_\______| |_____/ \___|_|    \_/ \___|_|

Please select the options:
[1] Revoke Certificate
[2] Update CRL URL and Re-generate certificates
[0] Quit
CRL Server> [INFO] 2018-03-19 16:40:27,066 <b>Started CRL Server at localhost:9007</b>
</code>
</pre>
## Revoking a Certificate

### Revoke Certificate using CRLServer
- Step #1 Enter Option 1 to Revoke Certificate 
  - Lists out the all existing certificates present in harness/certs directory.
- Step #2 Select certificate to blacklist.
  - The selected certificate has been considered for revocation.
- Step #3 Specify the type of certificate whether it is a CBSD,DP or SAS certificate. 
  - The selected certificate type option has been considered for revocation.
- Step #4 Wait for few second(s) to receive confirmation message (highlighted below) about certificate revocation 
  and it's corresponding serial number addition to CRL Database.
<pre>
<code>
   _____ _____  _         _____
  / ____|  __ \| |       / ____|
 | |    | |__) | |      | (___   ___ _ ____   _____ _ __
 | |    |  _  /| |       \___ \ / _ \ '__\ \ / / _ \ '__|
 | |____| | \ \| |____   ____) |  __/ |   \ V /  __/ |
  \_____|_|  \_\______| |_____/ \___|_|    \_/ \___|_|

Please select the options:
<b>[1] Revoke Certificate</b>
[2] Update CRL URL and Re-generate certificates
[0] Quit
CRL Server> <b>1</b>
Certificates present in directory path: **/harness/certs**
Select the certificate to blacklist:
[0] admin_client.cert
[1] ca.cert
[2] cbsd-ecc_ca.cert
[3] cbsd_ca.cert
<b>[4] client.cert</b>
[5] client_expired.cert

CRL Server> <b>4</b>
[INFO] 2018-03-19 16:48:01,372 Certificate selected to blacklist is:client.cert
Select the certificate type:
<b>[1] CBSD</b>
[2] DP
[3] SAS
CRL Server> <b>1</b>
Using configuration from ../../../cert/openssl.cnf
Adding Entry with serial number 9946F8E1AEFBD7C0 to DB for /C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS CBSD Example
<b>Revoking Certificate 9946F8E1AEFBD7C0.</b>
Data Base Updated
\n\n Generate CRL for root_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for sas_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for proxy_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for cbsd_ca
Using configuration from ../../../cert/openssl.cnf
<b>[INFO] 2018-03-19 16:48:48,923 client.cert is blacklisted successfully</b>
</code>
</pre> 

### Update CDP CRL Distribution Point in certificate and Regenerate CRLs


Select this option to update the CDP URL extension field in the certificates with the URL of the simple CRL server.<br/> 
The <b>[ crl_section ]</b> field in the <b>'openssl.cnf'</b> will be updated with the URL of this simple CRL server and 
all the certificates will be regenerated.<br/>
<pre>
<code>
   _____ _____  _         _____
  / ____|  __ \| |       / ____|
 | |    | |__) | |      | (___   ___ _ ____   _____ _ __
 | |    |  _  /| |       \___ \ / _ \ '__\ \ / / _ \ '__|
 | |____| | \ \| |____   ____) |  __/ |   \ V /  __/ |
  \_____|_|  \_\______| |_____/ \___|_|    \_/ \___|_|

Please select the options:
[1] Revoke Certificate
<b>[2] Update CRL URL and Re-generate certificates</b>
[0] Quit
CRL Server><b>2</b> 
[INFO] 2018-03-18 21:29:01,192 CRL URL has been updated correctly in openssl.cnf
\n\nGenerate 'root_ca' and 'root-ecc_ca' certificate/key
Generating a 4096 bit RSA private key
.++
..................................................................++
writing new private key to 'private/root_ca.key'
-----
\n\nGenerate 'sas_ca' and 'sas-ecc_ca' certificate/key
Generating a 4096 bit RSA private key
...............................................................................................++
.........................................++
writing new private key to 'private/sas_ca.key'
-----
Using configuration from ../../../cert/openssl.cnf
Check that the request matches the signature
Signature ok
Certificate Details:
        Serial Number:
            f4:b9:9d:d7:27:21:14:3d
        Validity
            Not Before: Mar 18 15:59:05 2018 GMT
            Not After : Mar 14 15:59:05 2033 GMT
        Subject:
            countryName               = US
            stateOrProvinceName       = District of Columbia
            localityName              = Washington
            organizationName          = Wireless Innovation Forum
            organizationalUnitName    = www.wirelessinnovation.org
            commonName                = WInnForum RSA SAS CA-1
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                CF:45:8F:3A:CB:A5:9A:F3:95:8E:2D:0D:51:FF:61:63:75:73:B8:57
            X509v3 Authority Key Identifier:
                keyid:50:69:EB:DA:C3:98:14:4A:63:8F:57:09:B5:D2:EB:15:36:E3:F6:4B

            X509v3 Basic Constraints: critical
                CA:TRUE, pathlen:0
            X509v3 Key Usage: critical
                Digital Signature, Certificate Sign, CRL Sign
            X509v3 Certificate Policies:
                Policy: 2.16.840.1.114412.2.1
                  CPS: https://www.digicert.com/CPS
                Policy: ROLE_CA
                Policy: ROLE_SAS

Certificate is to be certified until Mar 14 15:59:05 2033 GMT (5475 days)

Write out database with 1 new entries
Data Base Updated
Using configuration from ../../../cert/openssl.cnf
Check that the request matches the signature
Signature ok
Certificate Details:
        Serial Number:
            f4:b9:9d:d7:27:21:14:3e
        Validity
            Not Before: Mar 18 15:59:05 2018 GMT
            Not After : Mar 14 15:59:05 2033 GMT
        Subject:
            countryName               = US
            stateOrProvinceName       = District of Columbia
            localityName              = Washington
            organizationName          = Wireless Innovation Forum
            organizationalUnitName    = www.wirelessinnovation.org
            commonName                = WInnForum ECC SAS CA-1
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                30:09:FF:DC:84:99:40:EC:D8:1B:2D:54:4B:A0:55:36:98:5A:09:C4
            X509v3 Authority Key Identifier:
                keyid:E0:5E:23:72:C1:35:5B:DC:05:32:19:D3:02:49:8D:C2:BD:B7:AA:69

            X509v3 Basic Constraints: critical
                CA:TRUE, pathlen:0
            X509v3 Key Usage: critical
                Digital Signature, Certificate Sign, CRL Sign
            X509v3 Certificate Policies:
                Policy: 2.16.840.1.114412.2.1
                  CPS: https://www.digicert.com/CPS
                Policy: ROLE_CA
                Policy: ROLE_SAS

Certificate is to be certified until Mar 14 15:59:05 2033 GMT (5475 days)

Write out database with 1 new entries
Data Base Updated
\n\nGenerate 'cbsd_ca' certificate/key
Generating a 4096 bit RSA private key
..........++
...................................................................................................................................++
writing new private key to 'private/cbsd_ca.key'
-----
Using configuration from ../../../cert/openssl.cnf
Check that the request matches the signature
Signature ok
Certificate Details:
        Serial Number:
            f4:b9:9d:d7:27:21:14:3f
        Validity
            Not Before: Mar 18 15:59:08 2018 GMT
            Not After : Mar 14 15:59:08 2033 GMT
        Subject:
            countryName               = US
            stateOrProvinceName       = District of Columbia
            localityName              = Washington
            organizationName          = Wireless Innovation Forum
            organizationalUnitName    = www.wirelessinnovation.org
            commonName                = WInnForum RSA CBSD CA-1
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                EB:86:4E:70:E5:3E:AF:D0:89:95:29:BF:F8:4C:AE:CA:A0:80:01:32
            X509v3 Authority Key Identifier:
                keyid:50:69:EB:DA:C3:98:14:4A:63:8F:57:09:B5:D2:EB:15:36:E3:F6:4B

            X509v3 Basic Constraints: critical
                CA:TRUE, pathlen:1
            X509v3 Key Usage: critical
                Digital Signature, Certificate Sign, CRL Sign
            X509v3 Certificate Policies:
                Policy: 2.16.840.1.114412.2.1
                  CPS: https://www.digicert.com/CPS
                Policy: ROLE_CA
                Policy: ROLE_CBSD

Certificate is to be certified until Mar 14 15:59:08 2033 GMT (5475 days)

Write out database with 1 new entries
Data Base Updated
Using configuration from ../../../cert/openssl.cnf
Check that the request matches the signature
Signature ok
Certificate Details:
        Serial Number:
            f4:b9:9d:d7:27:21:14:40
        Validity
            Not Before: Mar 18 15:59:09 2018 GMT
            Not After : Mar 14 15:59:09 2033 GMT
        Subject:
            countryName               = US
            stateOrProvinceName       = District of Columbia
            localityName              = Washington
            organizationName          = Wireless Innovation Forum
            organizationalUnitName    = www.wirelessinnovation.org
            commonName                = WInnForum ECC CBSD CA-1
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                D4:44:F2:CD:99:D4:24:0D:47:B5:EB:3A:BE:91:3B:8D:A8:0E:5E:4E
            X509v3 Authority Key Identifier:
                keyid:E0:5E:23:72:C1:35:5B:DC:05:32:19:D3:02:49:8D:C2:BD:B7:AA:69

            X509v3 Basic Constraints: critical
                CA:TRUE, pathlen:1
            X509v3 Key Usage: critical
                Digital Signature, Certificate Sign, CRL Sign
            X509v3 Certificate Policies:
                Policy: 2.16.840.1.114412.2.1
                  CPS: https://www.digicert.com/CPS
                Policy: ROLE_CA
                Policy: ROLE_CBSD

Certificate is to be certified until Mar 14 15:59:09 2033 GMT (5475 days)
\n\nGenerate 'certs for devices' certificate/key
Generating a 2048 bit RSA private key
..........+++
..................................+++
writing new private key to 'device_a.key'
-----
Using configuration from ../../../cert/openssl.cnf
Check that the request matches the signature
Signature ok
Certificate Details:
        Serial Number:
            f4:b9:9d:d7:27:21:14:45
        Validity
            Not Before: Mar 18 15:59:10 2018 GMT
            Not After : Jun 15 15:59:10 2021 GMT
        Subject:
            countryName               = US
            stateOrProvinceName       = District of Columbia
            localityName              = Washington
            organizationName          = Wireless Innovation Forum
            organizationalUnitName    = www.wirelessinnovation.org
            commonName                = device_a
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                2E:AA:66:B6:21:D6:CD:40:40:32:88:BD:B4:1A:32:94:58:10:EA:CF
            X509v3 Authority Key Identifier:
                keyid:EB:86:4E:70:E5:3E:AF:D0:89:95:29:BF:F8:4C:AE:CA:A0:80:01:32

            X509v3 Basic Constraints:
                CA:FALSE
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment, CRL Sign
            X509v3 Extended Key Usage:
                TLS Web Client Authentication
            X509v3 Certificate Policies:
                Policy: 2.16.840.1.114412.2.1
                  CPS: https://www.digicert.com/CPS
                Policy: ROLE_CBSD

            X509v3 CRL Distribution Points:

                Full Name:
                   <b>URI:http://localhost:9007/ca.crl</b>

Certificate is to be certified until Jun 15 15:59:10 2021 GMT (1185 days)

Write out database with 1 new entries
Data Base Updated
Generating a 2048 bit RSA private key
.......................................+++
..........................................+++
writing new private key to 'device_c.key'
-----
Using configuration from ../../../cert/openssl.cnf
Check that the request matches the signature
Signature ok
Certificate Details:
        Serial Number:
            f4:b9:9d:d7:27:21:14:46
        Validity
            Not Before: Mar 18 15:59:10 2018 GMT
            Not After : Jun 15 15:59:10 2021 GMT
        Subject:
            countryName               = US
            stateOrProvinceName       = District of Columbia
            localityName              = Washington
            organizationName          = Wireless Innovation Forum
            organizationalUnitName    = www.wirelessinnovation.org
            commonName                = device_c
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                BC:A3:10:06:92:43:1A:84:4E:EA:85:E2:E4:5B:8F:4C:7D:7E:F2:EB
            X509v3 Authority Key Identifier:
                keyid:EB:86:4E:70:E5:3E:AF:D0:89:95:29:BF:F8:4C:AE:CA:A0:80:01:32

            X509v3 Basic Constraints:
                CA:FALSE
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment, CRL Sign
            X509v3 Extended Key Usage:
                TLS Web Client Authentication
            X509v3 Certificate Policies:
                Policy: 2.16.840.1.114412.2.1
                  CPS: https://www.digicert.com/CPS
                Policy: ROLE_CBSD

            X509v3 CRL Distribution Points:

                Full Name:
                  <b>URI:http://localhost:9007/ca.crl</b>

Certificate is to be certified until Jun 15 15:59:10 2021 GMT (1185 days)

Write out database with 1 new entries
Data Base Updated
\n\nGenerate 'ca' bundle
<b>[INFO] 2018-03-18 21:29:55,879 The certs are regenerated successfully</b> 
\n\n Generate CRL for root_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for sas_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for proxy_ca
Using configuration from ../../../cert/openssl.cnf
\n\n Generate CRL for cbsd_ca
Using configuration from ../../../cert/openssl.cnf
<b>[INFO] 2018-03-18 21:29:56,020 crl/ca.crl CRL chain is created successfully</b>

</code>
</pre>


The various certificates follow the PKI structure defined on the "CBRS COMSEC TS
WINNF-15-S-0065" document. Naming and base configuration are issued from
https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/cert
