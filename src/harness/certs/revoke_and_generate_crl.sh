#!/bin/bash 
set -e

mkdir -p crl

function revoke_certificate()
{
  #Argument1: Name of the certificate to be revoked.

  #Fetch the Common Name to find out the issuer
  local CN=`openssl x509 -issuer -in $1 -noout | sed 's/^.*CN=//'`
  local CA=''
  if [[ "$CN" == *"CBSD OEM CA - Revoked"* ]]; then
    CA=revoked_cbsd_ca
  elif [[ "$CN" == *"Domain Proxy CA - Revoked"* ]]; then
    CA=revoked_proxy_ca
  elif [[ "$CN" == *"SAS Provider CA - Revoked"* ]]; then
    CA=revoked_sas_ca
  elif [[ "$CN" == *"CBSD OEM CA"* ]]; then
    CA=cbsd_ca
  elif [[ "$CN" == *"Domain Proxy CA"* ]]; then
    CA=proxy_ca
  elif [[ "$CN" == *"SAS Provider CA"* ]]; then
    CA=sas_ca
  elif [[ "$CN" == *"Root CA"* ]]; then
    CA=root_ca
  else
    echo "Unknown issuer CN=$CN for certificate $1"
    exit -1
  fi
  # Revoke certificate.
  openssl ca -revoke $1 -keyfile private/$CA.key -cert $CA.cert \
      -config ../../../cert/openssl.cnf
  generate_crl_chain
}

function generate_crl_chain()
{
  # Create a CRL for root CA containing the revoked intermediate CA certificate.
  echo -e "\n\n Generate CRL for root_ca"
  openssl ca -gencrl -keyfile private/root_ca.key -cert root_ca.cert \
      -config ../../../cert/openssl.cnf -crldays 365 \
      -out crl/root_ca.crl
  echo -e "\n\n Generate CRL for sas_ca"
  openssl ca -gencrl -keyfile private/sas_ca.key -cert sas_ca.cert \
      -config ../../../cert/openssl.cnf -crldays 365 \
      -out crl/sas_ca.crl
  echo -e "\n\n Generate CRL for proxy_ca"
  openssl ca -gencrl -keyfile private/proxy_ca.key -cert proxy_ca.cert \
      -config ../../../cert/openssl.cnf -crldays 365 \
      -out crl/proxy_ca.crl
  echo -e "\n\n Generate CRL for cbsd_ca"
  openssl ca -gencrl -keyfile private/cbsd_ca.key -cert cbsd_ca.cert \
      -config ../../../cert/openssl.cnf -crldays 365 \
      -out crl/cbsd_ca.crl
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

  # Create CA certificate chain containing the CRLs of revoked leaf certificates.
  cat crl/cbsd_ca.crl crl/sas_ca.crl crl/proxy_ca.crl crl/root_ca.crl \
      crl/revoked_cbsd_ca.crl crl/revoked_sas_ca.crl crl/revoked_proxy_ca.crl > crl/ca.crl
}
#Argument1 : Type (-r,-u)
if [ "$1" == "-r" ]; then
  revoke_certificate  $2
elif [ "$1" == "-u" ]; then
  generate_crl_chain
else
  echo "Wrong option other than (-r, -u)"
  exit -1
fi
