#!/bin/bash

# Remove the unknown TEST extension to get useable certificate ...
sed -i '/TEST = critical, ASN1:NULL/d' ../../../cert/openssl.cnf

# Setup: build intermediate directories.
mkdir private
mkdir root
touch index.txt
echo -n 'unique_subject = no' >> index.txt.attr

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
echo "\n\nGenerate 'root_ca' and 'root-ecc_ca' certificate/key"
openssl req -new -x509 -newkey rsa:4096 -sha384 -nodes -days 7300 \
    -extensions root_ca -config ../../../cert/openssl.cnf \
    -out root_ca.cert -keyout private/root_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Root CA-1"

openssl ecparam -genkey -out  private/root-ecc_ca.key -name secp521r1
openssl req -new -x509 -key private/root-ecc_ca.key -out root-ecc_ca.cert \
    -sha384 -nodes -days 7300 -extensions root_ca -config ../../../cert/openssl.cnf \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum ECC Root CA-1"

echo "\n\nGenerate 'sas_ca' and 'sas-ecc_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts sas_ca  -config ../../../cert/openssl.cnf \
    -out sas_ca.csr -keyout private/sas_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA SAS CA-1"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in sas_ca.csr \
    -policy policy_anything -extensions sas_ca_sign -config ../../../cert/openssl.cnf \
    -out sas_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

openssl ecparam -genkey -out  private/sas-ecc_ca.key -name secp521r1
openssl req -new -nodes \
    -reqexts sas_ca  -config ../../../cert/openssl.cnf \
    -out sas-ecc_ca.csr -key private/sas-ecc_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum ECC SAS CA-1"
openssl ca -cert root-ecc_ca.cert -keyfile private/root-ecc_ca.key -in sas-ecc_ca.csr \
    -policy policy_anything -extensions sas_ca_sign -config ../../../cert/openssl.cnf \
    -out sas-ecc_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

echo "\n\nGenerate 'cbsd_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts cbsd_ca  -config ../../../cert/openssl.cnf \
    -out cbsd_ca.csr -keyout private/cbsd_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA CBSD CA-1"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in cbsd_ca.csr \
    -policy policy_anything -extensions cbsd_ca_sign -config ../../../cert/openssl.cnf \
    -out cbsd_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

openssl ecparam -genkey -out  private/cbsd-ecc_ca.key -name secp521r1
openssl req -new -nodes \
    -reqexts cbsd_ca  -config ../../../cert/openssl.cnf \
    -out cbsd-ecc_ca.csr -key private/cbsd-ecc_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum ECC CBSD CA-1"
openssl ca -cert root-ecc_ca.cert -keyfile private/root-ecc_ca.key -in cbsd-ecc_ca.csr \
    -policy policy_anything -extensions cbsd_ca_sign -config ../../../cert/openssl.cnf \
    -out cbsd-ecc_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

# Generate fake server certificate/key.
echo "\n\nGenerate 'server' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server.csr -keyout server.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server.csr \
    -out server.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate fake server certificate/key for server_a.
echo "\n\nGenerate 'server' certificate/key for server_a"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server_a.csr -keyout server_a.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server_a.csr \
    -out server_a.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384


# Generate fake server certificate/key for server_b.
echo "\n\nGenerate 'server' certificate/key for server_b"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server_b.csr -keyout server_b.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server_b.csr \
    -out server_b.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate fake server certificate/key for server_c.
echo "\n\nGenerate 'server' certificate/key for server_c"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server_c.csr -keyout server_c.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server_c.csr \
    -out server_c.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

#######################
openssl ecparam -genkey -out  server-ecc.key -name secp521r1
openssl req -new -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server-ecc.csr -key server-ecc.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=localhost"
openssl ca -cert sas-ecc_ca.cert -keyfile private/sas-ecc_ca.key -in server-ecc.csr \
    -out server-ecc.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate sas server certificate/key.
echo "\n\nGenerate 'sas server' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out sas.csr -keyout sas.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS-1"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas.csr \
    -out sas.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate normal operation client certificate/key.
echo "\n\nGenerate 'client' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out client.csr -keyout client.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS CBSD Example"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in client.csr \
    -out client.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

echo "\n\nGenerate 'certs for devices' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out device_a.csr -keyout device_a.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=device_a"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_a.csr \
    -out device_a.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out device_c.csr -keyout device_c.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=device_c"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in device_c.csr \
    -out device_c.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

echo "\n\nGenerate 'admin_client' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out admin_client.csr -keyout admin_client.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS client admin Example"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in admin_client.csr \
    -out admin_client.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate Domain Proxy certificate/key.
echo "\n\nGenerate 'proxy_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts oper_ca  -config ../../../cert/openssl.cnf \
    -out proxy_ca.csr -keyout private/proxy_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Domain Proxy CA"
openssl ca -cert root_ca.cert -keyfile private/root_ca.key -in proxy_ca.csr \
    -policy policy_anything -extensions oper_ca_sign -config ../../../cert/openssl.cnf \
    -out proxy_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384
echo "\n\nGenerate 'domain_proxy' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out domain_proxy.csr -keyout domain_proxy.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=domainProxy_a"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy.csr \
    -out domain_proxy.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate certificates for test case WINNF.FT.S.SCS.6 - Unrecognized root of trust certificate presented during registration
echo "\n\nGenerate 'unrecognized_device' certificate/key"
openssl req -new -x509 -newkey rsa:4096 -sha384 -nodes -days 7300 \
    -extensions root_ca -config ../../../cert/openssl.cnf \
    -out unrecognized_root_ca.cert -keyout private/unrecognized_root_ca.key \
    -subj "/C=US/ST=CA/L=Somewhere/O=Generic Certification Organization/OU=www.example.org/CN=Generic RSA Root CA"

openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out unrecognized_device.csr -keyout unrecognized_device.key \
    -subj "/C=US/ST=CA/L=Somewhere/O=Generic Certification Organization/OU=www.example.org/CN=Unrecognized CBSD"
openssl ca -cert unrecognized_root_ca.cert -keyfile private/unrecognized_root_ca.key -in unrecognized_device.csr \
    -out unrecognized_device.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificates for test case WINNF.FT.S.SCS.7 - corrupted certificate, based on client.cert
echo "\n\nGenerate 'corrupted_client' certificate/key"
gen_corrupt_cert client.key client.cert corrupted_client.key corrupted_client.cert

#Certificate for test case WINNF.FT.S.SCS.8 - Self-signed certificate presented during registration
#Using the same CSR that was created for normal operation
echo "\n\nGenerate 'self_signed_client' certificate/key"
openssl x509 -signkey client.key -in client.csr \
    -out self_signed_client.cert \
    -req -days 1185

#Certificate for test case WINNF.FT.S.SCS.9 - Non-CBRS trust root signed certificate presented during registration
openssl req -new -x509 -newkey rsa:4096 -sha384 -nodes -days 7300 \
    -extensions root_ca -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_ca.cert -keyout private/non_cbrs_root_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Root CA-2"

echo "\n\nGenerate 'non_cbrs_signed_cbsd_ca' certificate/key"
openssl req -new -newkey rsa:4096 -nodes \
    -reqexts cbsd_ca  -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_cbsd_ca.csr -keyout private/non_cbrs_root_signed_cbsd_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA CBSD CA-2"
openssl ca -cert non_cbrs_root_ca.cert -keyfile private/non_cbrs_root_ca.key -in non_cbrs_root_signed_cbsd_ca.csr \
    -policy policy_anything -extensions cbsd_ca_sign -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_cbsd_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

#Generate CBSD certifcate signed by a intermediate CBSD CA which is signed by a non-CBRS root CA
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out non_cbrs_signed_device.csr -keyout non_cbrs_signed_device.key \
    -subj "/C=US/ST=CA/L=Somewhere/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS CBSD unknown"
openssl ca -cert non_cbrs_root_signed_cbsd_ca.cert -keyfile private/non_cbrs_root_signed_cbsd_ca.key -in non_cbrs_signed_device.csr \
    -out non_cbrs_signed_device.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

#Certificate for test case WINNF.FT.S.SCS.10 - Certificate of wrong type presented during registration
#Creating a wrong type certificate by reusing the server.csr and having it signed by cbsd_ca.
echo "\n\nGenerate wrong type certificate/key"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in server.csr \
    -out wrong_type_client.cert -outdir ./root \
    -policy policy_anything -extensions wrong_cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

#Certificate for test case WINNF.FT.S.SCS.12 - Expired certificate presented during registration
echo "\n\nGenerate 'client_expired' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out client_expired.csr -keyout client_expired.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS CBSD Example"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in client_expired.csr \
    -out client_expired.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -startdate 20150214120000Z -enddate 20160214120000Z -md sha384

#Certificate for test case WINNF.FT.S.SCS.15 - Certificate with inapplicable fields presented during registration
echo "\n\nGenerate 'inapplicable certificate for WINNF.FT.S.SCS.15' certificate/key"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in client.csr \
    -out client_inapplicable.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_inapplicable_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate certificates for test case WINNF.FT.S.SDS.6 - Unrecognized root of trust certificate presented during registration
echo "\n\nGenerate 'unrecognized_domain_proxy' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out unrecognized_domain_proxy.csr -keyout unrecognized_domain_proxy.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Unrecognized Domain Proxy"
openssl ca -cert unrecognized_root_ca.cert -keyfile private/unrecognized_root_ca.key -in unrecognized_domain_proxy.csr \
    -out unrecognized_domain_proxy.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificates for test case WINN.FT.S.SDS.7 - corrupted certificate, based on domain_proxy.cert
echo "\n\nGenerate 'corrupted_domain_proxy' certificate/key"
gen_corrupt_cert domain_proxy.key domain_proxy.cert corrupted_domain_proxy.key corrupted_domain_proxy.cert

#Certificate for test case WINNF.FT.S.SDS.8 - Self-signed certificate presented during registration
#Using the same CSR that was created for normal operation
echo "\n\nGenerate 'self_signed_domain_proxy' certificate/key"
openssl x509 -signkey domain_proxy.key -in domain_proxy.csr \
    -out self_signed_domain_proxy.cert \
    -req -days 1185

#Certificate for test case WINNF.FT.S.SDS.9 - Non-CBRS trust root signed certificate presented during registration
echo "\n\nGenerate non_cbrs_root_signed_oper_ca.csr certificate/key"

openssl req -new -newkey rsa:4096 -nodes \
    -reqexts oper_ca -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_oper_ca.csr -keyout private/non_cbrs_root_signed_oper_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Domain Proxy CA-2"

openssl ca -cert non_cbrs_root_ca.cert -keyfile private/non_cbrs_root_ca.key -in non_cbrs_root_signed_oper_ca.csr \
    -policy policy_anything -extensions oper_ca_sign -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_oper_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

#Generate a Domain Proxy certifcate signed by an intermediate Domain Proxy CA which is signed by a non-CBRS root CA
echo "\n\nGenerate domain_proxy certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out non_cbrs_signed_domain_proxy.csr -keyout non_cbrs_signed_domain_proxy.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Domain Proxy Unknown"
openssl ca -cert non_cbrs_root_signed_oper_ca.cert -keyfile private/non_cbrs_root_signed_oper_ca.key -in non_cbrs_signed_domain_proxy.csr \
    -out non_cbrs_signed_domain_proxy.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificate for test case WINNF.FT.S.SDS.10 - Certificate of wrong type presented during registration
# Creating a wrong type certificate by reusing the server.csr and having it signed by proxy_ca.
echo "\n\nGenerate wrong type certificate/key"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in server.csr \
    -out wrong_type_domain_proxy.cert -outdir ./root \
    -policy policy_anything -extensions wrong_oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

#Certificate for test case WINNF.FT.S.SDS.12 - Expired certificate presented during registration
echo "\n\nGenerate 'domain_proxy_expired' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts oper_req -config ../../../cert/openssl.cnf \
    -out domain_proxy_expired.csr -keyout domain_proxy_expired.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Domain Proxy - Expired"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy_expired.csr \
    -out domain_proxy_expired.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -startdate 20150214120000Z -enddate 20160214120000Z -md sha384

#Certificate for test case WINNF.FT.S.SDS.15 -Certificate with inapplicable fields presented during registration
echo "\n\nGenerate 'inapplicable certificate for WINNF.FT.S.SDS.15' certificate"
openssl ca -cert proxy_ca.cert -keyfile private/proxy_ca.key -in domain_proxy.csr \
    -out domain_proxy_inapplicable.cert -outdir ./root \
    -policy policy_anything -extensions oper_req_inapplicable_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Generate certificates for test case WINNF.FT.S.SSS.6 - Unrecognized root of trust certificate presented during registration
echo "\n\nGenerate 'unrecognized_sas' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out unrecognized_sas.csr -keyout unrecognized_sas.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Unrecognized SAS"
openssl ca -cert unrecognized_root_ca.cert -keyfile private/unrecognized_root_ca.key -in unrecognized_sas.csr \
    -out unrecognized_sas.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Certificates for test case WINN.FT.S.SSS.7 - corrupted certificate, based on sas.cert
echo "\n\nGenerate 'corrupted_sas' certificate/key"
gen_corrupt_cert sas.key sas.cert corrupted_sas.key corrupted_sas.cert

#Certificate for test case WINNF.FT.S.SSS.8 - Self-signed certificate presented during registration
#Using the same CSR that was created for normal operation
echo "\n\nGenerate 'self_signed_sas' certificate/key"
openssl x509 -signkey sas.key -in sas.csr \
    -out self_signed_sas.cert \
    -req -days 1185

#Certificate for test case WINNF.FT.S.SSS.9 - Non-CBRS trust root signed certificate presented during registration
echo "\n\nGenerate non_cbrs_root_signed_sas_ca.csr certificate/key"

openssl req -new -newkey rsa:4096 -nodes \
    -reqexts sas_ca -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_sas_ca.csr -keyout private/non_cbrs_root_signed_sas_ca.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA SAS CA-2"

openssl ca -cert non_cbrs_root_ca.cert -keyfile private/non_cbrs_root_ca.key -in non_cbrs_root_signed_sas_ca.csr \
    -policy policy_anything -extensions sas_ca_sign -config ../../../cert/openssl.cnf \
    -out non_cbrs_root_signed_sas_ca.cert -outdir ./root \
    -batch -notext -create_serial -utf8 -days 5475 -md sha384

#Generate a SAS certifcate signed by an intermediate SAS CA which is signed by a non-CBRS root CA
echo "\n\nGenerate sas certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out non_cbrs_signed_sas.csr -keyout non_cbrs_signed_sas.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS Unknown"
openssl ca -cert non_cbrs_root_signed_sas_ca.cert -keyfile private/non_cbrs_root_signed_sas_ca.key -in non_cbrs_signed_sas.csr \
    -out non_cbrs_signed_sas.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

#Certificate for test case WINNF.FT.S.SSS.12 - Expired certificate presented during registration
echo "\n\nGenerate 'sas_expired' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_client_mode_req -config ../../../cert/openssl.cnf \
    -out sas_expired.csr -keyout sas_expired.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS - Expired"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas_expired.csr \
    -out sas_expired.cert -outdir ./root \
    -policy policy_anything -extensions sas_client_mode_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -startdate 20150214120000Z -enddate 20160214120000Z -md sha384

# Generate trusted CA bundle.
echo "\n\nGenerate 'ca' bundle"
cat cbsd_ca.cert proxy_ca.cert sas_ca.cert root_ca.cert cbsd-ecc_ca.cert sas-ecc_ca.cert root-ecc_ca.cert > ca.cert
# Note: following server implementation, we could also put only the root_ca.cert
# on ca.cert, then append the intermediate on each leaf certificate:
#   cat root_ca.cert > ca.cert
#   cat cbsd_ca.cert >> client.cert
#   cat cbsd_ca.cert >> admin_client.cert
#   cat sas_ca.cert >>  server.cert

# cleanup: remove all files not directly used by the testcases.
rm -rf private
rm -rf root
rm index.txt*
rm *.csr
