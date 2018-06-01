#!/bin/bash

if [ -z "$1" ]
  then
    echo "Must give CN (e.g. 'foo.bar.com') as first arg."
    exit
fi

echo -e "\n\nGenerating 'SAS cert' certificate/key with CN=$1"

echo "Subject Alt Name should be of the form: 'DNS:foo.bar.com,DNS:bar.com'"
if [ -z "$2" ]
  then
    echo "Warning: no Subject Alt Name specified."
    echo "[san_ext]" > san.cnf
  else
    echo "Using SAN = $2"
    echo -e "[san_ext]\nsubjectAltName=$2" > san.cnf
fi

echo "Using the following SAN config:"
cat san.cnf

echo "Generating RSA cert"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out sas_uut.csr -keyout sas_uut.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=$1"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas_uut.csr \
    -out sas_uut.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384 \
    -extfile san.cnf -extensions san_ext

echo "Generating ECC cert"
openssl ecparam -genkey -out sas_uut-ecc.key -name secp521r1
openssl req -new -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out sas_uut-ecc.csr -key sas_uut-ecc.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=$1"
openssl ca -cert sas-ecc_ca.cert -keyfile private/sas-ecc_ca.key -in sas_uut-ecc.csr \
    -out sas_uut-ecc.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384 \
    -extfile san.cnf -extensions san_ext

# Clean up.
rm san.cnf

