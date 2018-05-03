#!/bin/bash
set -e

# Setup: build intermediate directories.
rm -rf crl/
mkdir -p private
mkdir -p root
mkdir -p crl

# Empty the index.txt to avoid to old certificates index
rm -f index.txt
touch index.txt
echo -n 'unique_subject = no' > index.txt.attr

function gen_corrupt_cert()
{
  cp $1 $3
  cp $2 $4
  # cert file have first header line with 28 char: we want to change the 20th cert character
     pos=48
  hex_byte=$(xxd -seek $((10#$pos)) -l 1 -ps $4 -)
  #Modifying the byte value. If the byte character is 'z' or 'Z' or '9', then it is decremented by 1 to 'y' or 'Y' or '8' respectively.
  #If the value is '+' or '/' then we set it to 'A', else the current character value is incremented by 1.
  #This takes care of all the 64 characters of Base64 encoding.
  if [[ $hex_byte == "7a"  ||  $hex_byte == "5a" || $hex_byte == "39" ]]; then
    corrupted_dec_byte=$(($((16#$hex_byte)) -1))
  elif [[ $hex_byte == "2f"  ||  $hex_byte == "2b" ]]; then
    corrupted_dec_byte=65
  else
    corrupted_dec_byte=$(($((16#$hex_byte)) +1))
  fi
  # write it back
  printf "%x: %02x" $pos $corrupted_dec_byte | xxd -r - $4
}

# Generate root and intermediate CA certificate/key.
echo -e "\n\nGenerate 'root_ca' and 'root-ecc_ca' certificate/key"
openssl req -new -x509 -newkey rsa:4096 -sha384 -nodes -days 7300 \
    -extensions root_ca -config ../../../cert/openssl.cnf \
    -out root_ca.cert -keyout private/root_ca.key \
    -subj "/C=US/O=WInnForum/OU=RSA Root CA0001/CN=WInnForum RSA Root CA"

openssl ecparam -genkey -out  private/root-ecc_ca.key -name secp521r1
openssl req -new -x509 -key private/root-ecc_ca.key -out root-ecc_ca.cert \
    -sha384 -nodes -days 7300 -extensions root_ca -config ../../../cert/openssl.cnf \
    -subj "/C=US/O=WInnForum/OU=ECC Root CA0001/CN=WInnForum ECC Root CA"

echo -e "\n\nGenerate 'sas_ca' and 'sas-ecc_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts sas_ca  -config ../../../cert/openssl.cnf \
    -out sas_ca.csr -keyout private/sas_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=RSA SAS Provider CA0001/CN=WInnForum RSA SAS Provider CA"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in sas_ca.csr \
    -policy policy_anything -extensions sas_ca_sign -config ../../../cert/openssl.cnf \
    -out sas_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

openssl ecparam -genkey -out  private/sas-ecc_ca.key -name secp521r1
openssl req -new -nodes \
    -reqexts sas_ca  -config ../../../cert/openssl.cnf \
    -out sas-ecc_ca.csr -key private/sas-ecc_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=ECC SAS Provider CA0001/CN=WInnForum ECC SAS Provider CA"
openssl ca -cert root-ecc_ca.cert -keyfile private/root-ecc_ca.key -in sas-ecc_ca.csr \
    -policy policy_anything -extensions sas_ca_sign -config ../../../cert/openssl.cnf \
    -out sas-ecc_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

echo -e "\n\nGenerate 'cbsd_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts cbsd_ca  -config ../../../cert/openssl.cnf \
    -out cbsd_ca.csr -keyout private/cbsd_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=RSA CBSD OEM CA0001/CN=WInnForum RSA CBSD OEM CA"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in cbsd_ca.csr \
    -policy policy_anything -extensions cbsd_ca_sign -config ../../../cert/openssl.cnf \
    -out cbsd_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

openssl ecparam -genkey -out  private/cbsd-ecc_ca.key -name secp521r1
openssl req -new -nodes \
    -reqexts cbsd_ca  -config ../../../cert/openssl.cnf \
    -out cbsd-ecc_ca.csr -key private/cbsd-ecc_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=ECC CBSD OEM CA0001/CN=WInnForum ECC CBSD OEM CA"
openssl ca -cert root-ecc_ca.cert -keyfile private/root-ecc_ca.key -in cbsd-ecc_ca.csr \
    -policy policy_anything -extensions cbsd_ca_sign -config ../../../cert/openssl.cnf \
    -out cbsd-ecc_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

echo -e "\n\nGenerate 'proxy_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts oper_ca  -config ../../../cert/openssl.cnf \
    -out proxy_ca.csr -keyout private/proxy_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=RSA Domain Proxy CA0001/CN=WInnForum RSA Domain Proxy CA"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in proxy_ca.csr \
    -policy policy_anything -extensions oper_ca_sign -config ../../../cert/openssl.cnf \
    -out proxy_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

# Generate fake server certificate/key.
echo -e "\n\nGenerate 'server' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server.csr -keyout server.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server.csr \
    -out server.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

openssl ecparam -genkey -out  server-ecc.key -name secp521r1
openssl req -new -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server-ecc.csr -key server-ecc.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=localhost"
openssl ca -cert sas-ecc_ca.cert -keyfile private/sas-ecc_ca.key -in server-ecc.csr \
    -out server-ecc.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate sas server certificate/key.
echo -e "\n\nGenerate 'sas server' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out sas.csr -keyout sas.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas.csr \
    -out sas.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out sas_1.csr -keyout sas_1.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate 001/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas_1.csr \
    -out sas_1.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate normal operation device certificate/key.
echo -e "\n\nGenerate 'certs for devices' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out device_a.csr -keyout device_a.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum CBSD Certificate/CN=test_fcc_id_a:test_serial_number_a"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_a.csr \
    -out device_a.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_device_a_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out device_c.csr -keyout device_c.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum CBSD Certificate/CN=test_fcc_id_c:test_serial_number_c"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_c.csr \
    -out device_c.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_device_c_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

echo -e "\n\nGenerate 'admin' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out admin.csr -keyout admin.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum Admin Certificate/CN=SAS admin Example"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in admin.csr \
    -out admin.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate Domain Proxy certificate/key.
echo -e "\n\nGenerate 'domain_proxy' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out domain_proxy.csr -keyout domain_proxy.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum Domain Proxy Certificate/CN=0123456789:0002"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy.csr \
    -out domain_proxy.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out domain_proxy_1.csr -keyout domain_proxy_1.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum Domain Proxy Certificate/CN=0123456789:0003"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy_1.csr \
    -out domain_proxy_1.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate certificates for test case WINNF.FT.S.SCS.6 - Unrecognized root of trust certificate presented during registration
echo -e "\n\nGenerate 'unrecognized_device' certificate/key"
openssl req -new -x509 -newkey rsa:4096 -sha384 -nodes -days 7300 \
    -extensions root_ca -config ../../../cert/openssl.cnf \
    -out unrecognized_root_ca.cert -keyout private/unrecognized_root_ca.key \
    -subj "/C=US/O=Generic Certification Organization/OU=www.example.org/CN=Generic RSA Root CA"

openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out unrecognized_device.csr -keyout unrecognized_device.key \
    -subj "/C=US/O=Generic Certification Organization/OU=www.example.org/CN=Unrecognized CBSD"
openssl ca -cert unrecognized_root_ca.cert -keyfile private/unrecognized_root_ca.key -in unrecognized_device.csr \
    -out unrecognized_device.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificates for test case WINNF.FT.S.SCS.7 - corrupted certificate, based on device_a.cert
echo -e "\n\nGenerate 'device_corrupted' certificate/key"
gen_corrupt_cert device_a.key device_a.cert device_corrupted.key device_corrupted.cert

# Certificate for test case WINNF.FT.S.SCS.8 - Self-signed certificate presented during registration
# Using the same CSR that was created for normal operation
echo -e "\n\nGenerate 'device_self_signed' certificate/key"
openssl x509 -signkey device_a.key -in device_a.csr \
    -out device_self_signed.cert \
    -req -days 1185

# Certificate for test case WINNF.FT.S.SCS.9 - Non-CBRS trust root signed certificate presented during registration
echo -e "\n\nGenerate 'non_cbrs_signed_cbsd_ca' certificate/key"
openssl req -new -x509 -newkey rsa:4096 -sha384 -nodes -days 7300 \
    -extensions root_ca -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_ca.cert -keyout private/non_cbrs_root_ca.key \
    -subj "/C=US/O=Non CBRS company/OU=www.example.org/CN=Non CBRS Root CA"

echo -e "\n\nGenerate 'non_cbrs_signed_cbsd_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts cbsd_ca  -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_cbsd_ca.csr -keyout private/non_cbrs_root_signed_cbsd_ca.key \
    -subj "/C=US/O=Non CBRS company/OU=www.example.org/CN=Non CBRS CBSD CA"
openssl ca -cert non_cbrs_root_ca.cert -keyfile private/non_cbrs_root_ca.key -in non_cbrs_root_signed_cbsd_ca.csr \
    -policy policy_anything -extensions cbsd_ca_sign -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_cbsd_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

# Generate CBSD certificate signed by a intermediate CBSD CA which is signed by a non-CBRS root CA
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out non_cbrs_signed_device.csr -keyout non_cbrs_signed_device.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum CBSD Certificate/CN=test_fcc_id:0001"
openssl ca -cert non_cbrs_root_signed_cbsd_ca.cert -keyfile private/non_cbrs_root_signed_cbsd_ca.key -in non_cbrs_signed_device.csr \
    -out non_cbrs_signed_device.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SCS.10 - Certificate of wrong type presented during registration
# Creating a wrong type certificate by reusing the server.csr and creating a server certificate.
echo -e "\n\nGenerate wrong type certificate/key"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server.csr \
    -out device_wrong_type.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign   -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SCS.11
echo -e "\n\nGenerate blacklisted client certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out device_blacklisted.csr -keyout device_blacklisted.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum CBSD Certificate/CN=test_fcc_id:sn_0001"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_blacklisted.csr \
    -out device_blacklisted.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Revoke the device_blacklisted.cert for WINNF.FT.S.SCS.11
openssl ca -revoke device_blacklisted.cert -keyfile private/cbsd_ca.key -cert cbsd_ca.cert \
     -config ../../../cert/openssl.cnf

# Certificate for test case WINNF.FT.S.SDS.11
echo -e "\n\nGenerate blacklisted domain proxy certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out domain_proxy_blacklisted.csr -keyout domain_proxy_blacklisted.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum Domain Proxy Certificate/CN=0123456789:0004"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy_blacklisted.csr \
    -out domain_proxy_blacklisted.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Revoke the domain_proxy_blacklisted.cert for WINNF.FT.S.SDS.11
openssl ca -revoke domain_proxy_blacklisted.cert -keyfile private/proxy_ca.key -cert proxy_ca.cert \
     -config ../../../cert/openssl.cnf

# Certificate for test case WINNF.FT.S.SSS.11
echo -e "\n\nGenerate blacklisted sas certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out sas_blacklisted.csr -keyout sas_blacklisted.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas_blacklisted.csr \
    -out sas_blacklisted.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Revoke the sas_blacklisted.cert for WINNF.FT.S.SSS.11
openssl ca -revoke sas_blacklisted.cert -keyfile private/sas_ca.key -cert sas_ca.cert \
    -config ../../../cert/openssl.cnf

# Create a CRL for root CA containing the revoked CBSD CA certificate
echo -e "\n\nGenerate CRL for root_ca"
openssl ca -gencrl -keyfile private/root_ca.key -cert root_ca.cert \
    -config ../../../cert/openssl.cnf -crldays 365 \
    -out crl/root_ca.crl

# Creating CRL for blacklisted certificates xxS.11 test cases
echo -e "\n\nGenerate CRL for sas_ca"
openssl ca -gencrl -keyfile private/sas_ca.key -cert sas_ca.cert \
    -config ../../../cert/openssl.cnf -crldays 365 \
    -out crl/sas_ca.crl

echo -e "\n\nGenerate CRL for proxy_ca"
openssl ca -gencrl -keyfile private/proxy_ca.key -cert proxy_ca.cert \
    -config ../../../cert/openssl.cnf -crldays 365 \
    -out crl/proxy_ca.crl

echo -e "\n\nGenerate CRL for cbsd_ca"
openssl ca -gencrl -keyfile private/cbsd_ca.key -cert cbsd_ca.cert \
    -config ../../../cert/openssl.cnf -crldays 365 \
    -out crl/cbsd_ca.crl

# Certificate for test case WINNF.FT.S.SCS.12 - Expired certificate presented during registration
echo -e "\n\nGenerate 'device_expired' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out device_expired.csr -keyout device_expired.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum CBSD Certificate/CN=test_fcc_id:0002"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_expired.csr \
    -out device_expired.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -startdate 20150214120000Z -enddate 20160214120000Z -md sha384

# Certificate for test case WINNF.FT.S.SCS.15 - Certificate with inapplicable fields presented during registration
echo -e "\n\nGenerate 'inapplicable certificate for WINNF.FT.S.SCS.15' certificate/key"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_a.csr \
    -out device_inapplicable.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_inapplicable_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate certificates for test case WINNF.FT.S.SDS.6 - Unrecognized root of trust certificate presented during registration
echo -e "\n\nGenerate 'unrecognized_domain_proxy' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out unrecognized_domain_proxy.csr -keyout unrecognized_domain_proxy.key \
    -subj "/C=US/O=Generic Certification Organization/OU=www.example.org/CN=Unrecognized Domain Proxy"
openssl ca -cert unrecognized_root_ca.cert -keyfile private/unrecognized_root_ca.key -in unrecognized_domain_proxy.csr \
    -out unrecognized_domain_proxy.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificates for test case WINN.FT.S.SDS.7 - corrupted certificate, based on domain_proxy.cert
echo -e "\n\nGenerate 'domain_proxy_corrupted' certificate/key"
gen_corrupt_cert domain_proxy.key domain_proxy.cert domain_proxy_corrupted.key domain_proxy_corrupted.cert

# Certificate for test case WINNF.FT.S.SDS.8 - Self-signed certificate presented during registration
# Using the same CSR that was created for normal operation
echo -e "\n\nGenerate 'domain_proxy_self_signed' certificate/key"
openssl x509 -signkey domain_proxy.key -in domain_proxy.csr \
    -out domain_proxy_self_signed.cert \
    -req -days 1185

# Certificate for test case WINNF.FT.S.SDS.9 - Non-CBRS trust root signed certificate presented during registration
echo -e "\n\nGenerate non_cbrs_root_signed_oper_ca.csr certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts oper_ca -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_oper_ca.csr -keyout private/non_cbrs_root_signed_oper_ca.key \
    -subj "/C=US/O=Non CBRS company/OU=www.example.org/CN=Non CBRS Domain Proxy CA"

openssl ca -cert non_cbrs_root_ca.cert -keyfile private/non_cbrs_root_ca.key -in non_cbrs_root_signed_oper_ca.csr \
    -policy policy_anything -extensions oper_ca_sign -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_oper_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

# Generate a Domain Proxy certifcate signed by an intermediate Domain Proxy CA which is signed by a non-CBRS root CA
echo -e "\n\nGenerate domain_proxy certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out non_cbrs_signed_domain_proxy.csr -keyout non_cbrs_signed_domain_proxy.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum Domain Proxy Certificate/CN=0123456789:0005"
openssl ca -cert non_cbrs_root_signed_oper_ca.cert -keyfile private/non_cbrs_root_signed_oper_ca.key -in non_cbrs_signed_domain_proxy.csr \
    -out non_cbrs_signed_domain_proxy.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SDS.10 - Certificate of wrong type presented during registration
# Creating a wrong type certificate by reusing the server.csr and creating a server certificate.
echo -e "\n\nGenerate wrong type certificate/key"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server.csr \
    -out domain_proxy_wrong_type.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign   -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SDS.12 - Expired certificate presented during registration
echo -e "\n\nGenerate 'domain_proxy_expired' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out domain_proxy_expired.csr -keyout domain_proxy_expired.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum Domain Proxy Certificate/CN=0123456789:0006"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy_expired.csr \
    -out domain_proxy_expired.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -startdate 20150214120000Z -enddate 20160214120000Z -md sha384

# Certificate for test case WINNF.FT.S.SDS.15 -Certificate with inapplicable fields presented during registration
echo -e "\n\nGenerate 'inapplicable certificate for WINNF.FT.S.SDS.15' certificate"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy.csr \
    -out domain_proxy_inapplicable.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_inapplicable_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate certificates for test case WINNF.FT.S.SSS.6 - Unrecognized root of trust certificate presented during registration
echo -e "\n\nGenerate 'unrecognized_sas' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out unrecognized_sas.csr -keyout unrecognized_sas.key \
    -subj "/C=US/O=Generic Certification Organization/OU=www.example.org/CN=Unrecognized SAS Provider"
openssl ca -cert unrecognized_root_ca.cert -keyfile private/unrecognized_root_ca.key -in unrecognized_sas.csr \
    -out unrecognized_sas.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificates for test case WINN.FT.S.SSS.7 - corrupted certificate, based on sas.cert
echo -e "\n\nGenerate 'sas_corrupted' certificate/key"
gen_corrupt_cert sas.key sas.cert sas_corrupted.key sas_corrupted.cert

# Certificate for test case WINNF.FT.S.SSS.8 - Self-signed certificate presented during registration
# Using the same CSR that was created for normal operation
echo -e "\n\nGenerate 'sas_self_signed' certificate/key"
openssl x509 -signkey sas.key -in sas.csr \
    -out sas_self_signed.cert \
    -req -days 1185

# Certificate for test case WINNF.FT.S.SSS.9 - Non-CBRS trust root signed certificate presented during registration
echo -e "\n\nGenerate non_cbrs_root_signed_sas_ca.csr certificate/key"

openssl req -new -newkey rsa:4096 -nodes \
    -reqexts sas_ca -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_sas_ca.csr -keyout private/non_cbrs_root_signed_sas_ca.key \
    -subj "/C=US/O=Non CBRS company/OU=www.example.org/CN=Non CBRS SAS Provider CA"

openssl ca -cert non_cbrs_root_ca.cert -keyfile private/non_cbrs_root_ca.key -in non_cbrs_root_signed_sas_ca.csr \
    -policy policy_anything -extensions sas_ca_sign -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_sas_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

# Generate a SAS certificate signed by an intermediate SAS CA which is signed by a non-CBRS root CA
echo -e "\n\nGenerate sas certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out non_cbrs_signed_sas.csr -keyout non_cbrs_signed_sas.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=non-cbrs.example.org"
openssl ca -cert non_cbrs_root_signed_sas_ca.cert -keyfile private/non_cbrs_root_signed_sas_ca.key -in non_cbrs_signed_sas.csr \
    -out non_cbrs_signed_sas.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SSS.10 - Certificate of wrong type presented by SAS Test Harness 
# Creating a wrong type certificate by reusing the device_a.csr and creating a client certificate.
echo -e "\n\nGenerate wrong type certificate/key"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_a.csr \
    -out sas_wrong_type.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SSS.12 - Expired certificate presented by SAS Test Harness
echo -e "\n\nGenerate 'sas_expired' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out sas_expired.csr -keyout sas_expired.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=expired.example.org"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas_expired.csr \
    -out sas_expired.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -startdate 20150214120000Z -enddate 20160214120000Z -md sha384

# Certificate for test case WINNF.FT.S.SSS.15 -Certificate with inapplicable fields presented by SAS Test Harness
echo -e "\n\nGenerate 'inapplicable certificate for WINNF.FT.S.SSS.15' certificate"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas.csr \
    -out sas_inapplicable.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_inapplicable_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SCS.16 - Certificate signed by a revoked CA presented during registration
echo -e "\n\nGenerate 'revoked_cbsd_ca' certificate/key to revoke intermediate CA"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts cbsd_ca  -config ../../../cert/openssl.cnf \
    -out revoked_cbsd_ca.csr -keyout private/revoked_cbsd_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=RSA CBSD OEM CA0002/CN=WInnForum RSA CBSD OEM CA - Revoked"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in revoked_cbsd_ca.csr \
    -policy policy_anything -extensions cbsd_ca_sign -config ../../../cert/openssl.cnf \
    -out revoked_cbsd_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

# Generate client certificate/key signed by valid CA.
echo -e "\n\nGenerate 'client' certificate/key signed by revoked_cbsd_ca"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out device_cert_from_revoked_ca.csr -keyout device_cert_from_revoked_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum CBSD Certificate/CN=test_fcc_id:revoked"
openssl ca -cert revoked_cbsd_ca.cert -keyfile private/revoked_cbsd_ca.key -in device_cert_from_revoked_ca.csr \
    -out device_cert_from_revoked_ca.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Revoke the CBSD CA Certificate.
echo -e "\n\nRevoke intermediate CA (revoked_cbsd_ca) who already signed client certificate."
openssl ca -revoke revoked_cbsd_ca.cert -keyfile private/root_ca.key -cert root_ca.cert \
     -config ../../../cert/openssl.cnf

# Certificate for test case WINNF.FT.S.SDS.16 - Certificate signed by a revoked CA presented during registration.
echo -e "\n\nGenerate 'revoked_proxy_ca' certificate/key to revoke intermediate CA."
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts oper_ca  -config ../../../cert/openssl.cnf \
    -out revoked_proxy_ca.csr -keyout private/revoked_proxy_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=RSA Domain Proxy CA0002/CN=WInnForum RSA Domain Proxy CA - Revoked"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in revoked_proxy_ca.csr \
    -policy policy_anything -extensions oper_ca_sign -config ../../../cert/openssl.cnf \
    -out revoked_proxy_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

echo -e "\n\nGenerate 'domain_proxy' certificate/key signed by revoked_proxy_ca"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out domain_proxy_cert_from_revoked_ca.csr -keyout domain_proxy_cert_from_revoked_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum Domain Proxy Certificate/CN=0123456789:0010 - Revoked"
openssl ca -cert revoked_proxy_ca.cert -keyfile private/revoked_proxy_ca.key -in domain_proxy_cert_from_revoked_ca.csr \
    -out domain_proxy_cert_from_revoked_ca.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Revoke the Domain Proxy CA Certificate.
echo -e "\n\nRevoke intermediate CA (revoked_proxy_ca) who already signed domain proxy certificate."
openssl ca -revoke revoked_proxy_ca.cert -keyfile private/root_ca.key -cert root_ca.cert \
    -config ../../../cert/openssl.cnf

# Certificate for test case WINNF.FT.S.SSS.16 - Certificate signed by a revoked CA presented during registration
echo -e "\n\nGenerate 'sas_ca' certificate/key to revoke intermediate CA."
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts sas_ca  -config ../../../cert/openssl.cnf \
    -out revoked_sas_ca.csr -keyout private/revoked_sas_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=RSA SAS Provider CA0002/CN=WInnForum RSA SAS Provider CA - Revoked"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in revoked_sas_ca.csr \
    -policy policy_anything -extensions sas_ca_sign -config ../../../cert/openssl.cnf \
    -out revoked_sas_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

# Generate sas server certificate/key.
echo -e "\n\nGenerate 'sas server' certificate/key signed by revoked_sas_ca"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out sas_cert_from_revoked_ca.csr -keyout sas_cert_from_revoked_ca.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=localhost - Revoked"
openssl ca -cert revoked_sas_ca.cert -keyfile private/revoked_sas_ca.key -in sas_cert_from_revoked_ca.csr \
    -out sas_cert_from_revoked_ca.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Revoke the SAS CA Certificate.
openssl ca -revoke revoked_sas_ca.cert -keyfile private/root_ca.key -cert root_ca.cert \
    -config ../../../cert/openssl.cnf

# Creating CRL for revoked CA xxS.16 test cases
echo -e "\n\n Generate CRL for root_ca"
openssl ca -gencrl -keyfile private/root_ca.key -cert root_ca.cert \
     -config ../../../cert/openssl.cnf  -crldays 365 \
     -out crl/root_ca.crl

echo -e "\n\n Generate CRL for revoked_cbsd_ca"
openssl ca -gencrl -keyfile private/revoked_cbsd_ca.key -cert revoked_cbsd_ca.cert \
     -config ../../../cert/openssl.cnf -crldays 365 \
     -out crl/revoked_cbsd_ca.crl

echo -e "\n\n Generate CRL for revoked_sas_ca"
openssl ca -gencrl -keyfile private/revoked_sas_ca.key -cert revoked_sas_ca.cert \
     -config ../../../cert/openssl.cnf -crldays 365 \
     -out crl/revoked_sas_ca.crl

echo -e "\n\n Generate CRL for revoked_proxy_ca"
openssl ca -gencrl -keyfile private/revoked_proxy_ca.key -cert revoked_proxy_ca.cert \
     -config ../../../cert/openssl.cnf -crldays 365 \
     -out crl/revoked_proxy_ca.crl

# Generate trusted CA bundle.
echo -e "\n\nGenerate 'ca' bundle"
cat cbsd_ca.cert proxy_ca.cert sas_ca.cert root_ca.cert cbsd-ecc_ca.cert sas-ecc_ca.cert root-ecc_ca.cert \
    revoked_cbsd_ca.cert revoked_sas_ca.cert revoked_proxy_ca.cert > ca.cert
# Append the github cert, use to download test dump file.
echo | openssl s_client  -servername raw.githubusercontent.com -connect raw.githubusercontent.com:443 -prexit 2>&1 | \
    sed -n -e '/BEGIN\ CERTIFICATE/,/END\ CERTIFICATE/ p' >> ca.cert

# Create CA certificate chain containing the CRLs with revoked leaf certificates.
cat crl/cbsd_ca.crl crl/sas_ca.crl crl/proxy_ca.crl crl/root_ca.crl > crl/ca_sxs11.crl
cat ca.cert crl/ca_sxs11.crl > ca_crl_chain_sxs11.cert
cat crl/revoked_cbsd_ca.crl crl/revoked_sas_ca.crl crl/revoked_proxy_ca.crl crl/root_ca.crl > crl/ca_sxs16.crl
cat ca.cert crl/ca_sxs16.crl > ca_crl_chain_sxs16.cert

# Cleanup: remove all files not directly used by the testcases.
rm -rf root
rm *.csr

