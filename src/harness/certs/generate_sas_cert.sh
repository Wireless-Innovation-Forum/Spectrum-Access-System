#!/bin/bash

. include_crldp_base.sh
echo "Using CRL distribution points: $CRLDP_BASE<ca_name>.crl"

# Runs openssl using the database for a particular CA.
# $1 should match an existing db/* directory.
function openssl_db {
  OPENSSL_CNF_CA_DIR="db/$1" OPENSSL_CNF_CRLDP="$CRLDP_BASE$1.crl" \
      openssl "${@:2}" \
      -cert "$1.cert" -keyfile "private/$1.key"
}

# Make sure we have the CN.
if [ -z "$1" ]
  then
    echo "Must give CN (e.g. 'foo.bar.com') as first arg."
    exit
fi
echo -e "\n\nGenerating 'SAS cert' certificate/key with CN=$1"

# Detect or auto-create the SAN.
echo "Subject Alt Name should be of the form: 'DNS:foo.bar.com,DNS:bar.com'"
if [ -z "$2" ]
  then
    echo "Warning: no Subject Alt Name specified; auto-generating from CN."
    SAN="DNS:$1"
  else
    SAN=$2
fi
echo "Using SAN = $SAN"

# Create san.cnf
normal=`cat ../../../cert/openssl.cnf`
san_req="
[sas_req_san_ext]
subjectKeyIdentifier = hash
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, cRLSign
extendedKeyUsage = serverAuth,clientAuth
certificatePolicies=@cps,ROLE_SAS
crlDistributionPoints=@crl_section
subjectAltName = $SAN

[ sas_req_san_ext_sign ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, cRLSign
extendedKeyUsage = serverAuth,clientAuth
certificatePolicies=@cps,ROLE_SAS
crlDistributionPoints=@crl_section
subjectAltName = $SAN
"
echo -e "$normal$san_req" > san.cnf

# Generate the certs.
echo "Generating RSA cert"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req_san_ext -config san.cnf \
    -out sas_uut.csr -keyout sas_uut.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=$1"
openssl_db sas_ca ca -in sas_uut.csr \
    -out sas_uut.cert \
    -policy policy_anything -extensions sas_req_san_ext_sign -config san.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

echo "Generating ECC cert"
openssl ecparam -genkey -out sas_uut-ecc.key -name secp521r1
openssl req -new -nodes \
    -reqexts sas_req_san_ext -config san.cnf \
    -out sas_uut-ecc.csr -key sas_uut-ecc.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=$1"
openssl_db sas-ecc_ca ca -in sas_uut-ecc.csr \
    -out sas_uut-ecc.cert \
    -policy policy_anything -extensions sas_req_san_ext_sign -config san.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384

# Clean up.
rm san.cnf

