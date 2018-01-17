#!/bin/bash

# Remove the unknown TEST extension to get useable certificate ...
sed -i '/TEST = critical, ASN1:NULL/d' ../../../cert/openssl.cnf

# Setup: build intermediate directories.
mkdir private
mkdir root
mkdir -p root/crl
touch index.txt
echo 00 > root/crlnumber
echo -n 'unique_subject = no' >> index.txt.attr

function gen_corrupt_cert()
{
cp $1 $3
cp $2 $4
# cert file have first header line with 28 char: we want to change the 20th cert character
   pos=48
hex_byte=$(xxd -seek $((10#$pos)) -l 1 -ps $4 -)

# increment this byte
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
echo "\n\nGenerate 'server'--> server_a certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server_a.csr -keyout server_a.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=localhost"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in server_a.csr \
    -out server_a.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

openssl ecparam -genkey -out  server-ecc.key -name secp521r1
openssl req -new -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out server-ecc.csr -key server-ecc.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=localhost"
openssl ca -cert sas-ecc_ca.cert -keyfile private/sas-ecc_ca.key -in server-ecc.csr \
    -out server-ecc.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
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
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=0014720239:234A65760123"
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



# Note: following server implementation, we could also put only the root_ca.cert
# on ca.cert, then append the intermediate on each leaf certificate:
#   cat root_ca.cert > ca.cert
#   cat cbsd_ca.cert >> client.cert
#   cat cbsd_ca.cert >> admin_client.cert
#   cat sas_ca.cert >>  server.cert

# Generate specific old security SCS_2 certificate/key.
echo "\n\nGenerate 'unknown_device' certificate/key"
openssl req -new -x509 -newkey rsa:4096 -sha384 -nodes -days 7300 \
    -extensions root_ca -config ../../../cert/openssl.cnf \
    -out unknown_ca.cert -keyout private/unknown_ca.key \
    -subj "/C=US/ST=CA/L=Somewhere/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Root CA-2"

openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out unknown_device.csr -keyout unknown_device.key \
    -subj "/C=US/ST=CA/L=Somewhere/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS CBSD unknown"
openssl ca -cert unknown_ca.cert -keyfile private/unknown_ca.key -in unknown_device.csr \
    -out unknown_device.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
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

#Certificate for test case WINNF.FT.S.SCS.15 - inapplicable fields certificate presented during registration
echo "\n\nGenerate 'inapplicable certificate for WINNF.FT.S.SCS.15' certificate/key"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in client.csr \
    -out client_inapplicable.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_inapplicable_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

#Certificate for test case WINNF.FT.S.SCS.16 -
openssl ca -revoke cbsd_ca.cert -keyfile private/root_ca.key -cert root_ca.cert \
     -config ../../../cert/openssl.cnf

echo "\n\n Generate CRL for root_ca"
openssl ca -gencrl -keyfile private/root_ca.key -cert root_ca.cert \
     -config ../../../cert/openssl.cnf  -crlhours 1\
     -out root/crl/root_ca.crl

echo "\n\n Generate CRL for cbsd_ca"
openssl ca -gencrl -keyfile private/cbsd_ca.key -cert cbsd_ca.cert \
     -config ../../../cert/openssl.cnf -crlhours 1 \
     -out root/crl/cbsd_ca.crl

# Certificate for WINNF.FT.S.SCS.17,WINNF.FT.S.SCS.18 and WINNF.FT.S.SCS.19
echo "Created short lived certificate for WINNF.FT.S.SCS.17"
current_time=`date -u  +%y%m%d%H%M%SZ`
offset=5
enddate_value=$(date -u -d "now + $offset minutes" '+%y%m%d%H%M%SZ')
# Generate normal operation short_lived_client certificate/key.
echo "\n\nGenerate 'short_lived_client' certificate/key"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts cbsd_req -config ../../../cert/openssl.cnf \
    -out short_lived_client.csr -keyout short_lived_client.key \
    -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS CBSD Example"
openssl ca -cert cbsd_ca.cert -keyfile private/cbsd_ca.key -in short_lived_client.csr \
    -out short_lived_client.cert -outdir ./root \
    -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384 -enddate $enddate_value

# Generate trusted CA bundle.
echo "\n\nGenerate 'ca' bundle"
cat cbsd_ca.cert sas_ca.cert root_ca.cert cbsd-ecc_ca.cert sas-ecc_ca.cert root-ecc_ca.cert > ca.cert

echo "Appended crl and create new trusted chain that contains revoked CA"
cat ca.cert root/crl/cbsd_ca.crl root/crl/root_ca.crl  > WINNF_FT_S_SCS_16_ca.cert

# cleanup: remove all files not directly used by the testcases.
rm -rf private
rm -rf root
rm index.txt*
rm *.csr
