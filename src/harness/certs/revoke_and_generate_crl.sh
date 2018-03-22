#!/bin/bash 

mkdir -p crl

function blacklist_certificate()
{
  #Argument1: Name of the certificate to be  blacklisted.
  #Argument2: Intermediate CA to generate CRL.

  # Revoke certificate.
  openssl ca -revoke $1 -keyfile private/$2.key -cert $2.cert \
      -config ../../../cert/openssl.cnf
  generate_crl_chain
}

function generate_crl_chain()
{
  #Create a CRL for root CA containing the revoked intermediate CA certificate.
  echo "\n\n Generate CRL for root_ca"
  openssl ca -gencrl -keyfile private/root_ca.key -cert root_ca.cert \
      -config ../../../cert/openssl.cnf -crlhours 1 \
      -out crl/root_ca.crl

  #Creating CRL for blacklisted certificates SxS.11 test cases.
  echo "\n\n Generate CRL for sas_ca"
  openssl ca -gencrl -keyfile private/sas_ca.key -cert sas_ca.cert \
      -config ../../../cert/openssl.cnf -crlhours 1 \
      -out crl/sas_ca.crl
  echo "\n\n Generate CRL for proxy_ca"
  openssl ca -gencrl -keyfile private/proxy_ca.key -cert proxy_ca.cert \
      -config ../../../cert/openssl.cnf -crlhours 1 \
      -out crl/proxy_ca.crl
  echo "\n\n Generate CRL for cbsd_ca"
  openssl ca -gencrl -keyfile private/cbsd_ca.key -cert cbsd_ca.cert \
      -config ../../../cert/openssl.cnf -crlhours 1 \
      -out crl/cbsd_ca.crl

  #Create CA certificate chain containing the CRLs of revoked leaf certificates.
  cat crl/cbsd_ca.crl crl/sas_ca.crl crl/proxy_ca.crl crl/root_ca.crl > crl/ca.crl
}

#Argument1 : Type (CBSD,DP,SAS,-u)
if [ "$1" == "CBSD" ]; then
  blacklist_certificate  $2 cbsd_ca
elif [ "$1" == "DP" ]; then
  blacklist_certificate  $2 proxy_ca
elif [ "$1" == "SAS" ]; then
  blacklist_certificate  $2 sas_ca
elif [ "$1" == "-u" ]; then
  generate_crl_chain
else
  echo "Wrong option other than (CBSD,DP,SAS,-u)"
  exit -1
fi
