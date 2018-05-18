#!/bin/bash

if [ -z "$1" ]
  then
    echo "Must give CN (e.g. 'foo.bar.com') as first arg."
    exit
fi


echo -e "\n\nGenerating 'SAS cert' certificate/key with CN=$1"
openssl req -new -newkey rsa:2048 -nodes \
    -reqexts sas_req -config ../../../cert/openssl.cnf \
    -out sas.csr -keyout sas.key \
    -subj "/C=US/O=Wireless Innovation Forum/OU=WInnForum SAS Provider Certificate/CN=$1"
openssl ca -cert sas_ca.cert -keyfile private/sas_ca.key -in sas.csr \
    -out sas.cert -outdir ./root \
    -policy policy_anything -extensions sas_req_sign -config ../../../cert/openssl.cnf \
    -batch -notext -create_serial -utf8 -days 1185 -md sha384
