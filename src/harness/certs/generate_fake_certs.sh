#!/bin/bash

# Remove the unknown TEST extension to get useable certificate ...
sed -i '/TEST = critical, ASN1:NULL/d' ../../../cert/openssl.cnf

# Setup: build intermediate directories.
mkdir private
mkdir root
touch index.txt
echo -n 'unique_subject = no' >> index.txt.attr

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
