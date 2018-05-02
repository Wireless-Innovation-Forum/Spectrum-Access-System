#!/bin/bash 

mkdir -p crl

function revoke_certificate()
{
  #Argument1: Name of the certificate to be revoked.

  #Fetch the Common Name to find out the issuer.
  local CN=`openssl x509 -issuer -in $1 -noout | sed 's/^.*CN=//'`
  local CA=''
  if [ "$CN" == "WInnForum RSA CBSD CA-1" ]; then
    CA=cbsd_ca
  elif [ "$CN" == "WInnForum RSA Domain Proxy CA" ]; then
    CA=proxy_ca
  elif [ "$CN" == "WInnForum RSA SAS CA-1" ]; then
    CA=sas_ca
  elif [ "$CN" == "WInnForum RSA Root CA-1" ]; then
    CA=root_ca
  elif [ "$CN" == "WInnForum CBSD CA-1 - Revoked" ]; then
    CA=revoked_cbsd_ca
  elif [ "$CN" == "WInnForum RSA Domain Proxy CA - Revoked" ]; then
    CA=revoked_proxy_ca
  elif [ "$CN" == "WInnForum RSA SAS CA-1 - Revoked" ]; then
    CA=revoked_sas_ca
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
  echo -e "\n\n Generate CRL for blacklisted_cbsd_ca"
  openssl ca -gencrl -keyfile private/blacklisted_cbsd_ca.key -cert blacklisted_cbsd_ca.cert \
      -config ../../../cert/openssl.cnf -crldays 365 \
      -out crl/blacklisted_cbsd_ca.crl
  echo -e "\n\n Generate CRL for blacklisted_sas_ca"
  openssl ca -gencrl -keyfile private/blacklisted_sas_ca.key -cert blacklisted_sas_ca.cert \
      -config ../../../cert/openssl.cnf -crldays 365 \
      -out crl/blacklisted_sas_ca.crl
  echo -e "\n\n Generate CRL for blacklisted_proxy_ca"
  openssl ca -gencrl -keyfile private/blacklisted_proxy_ca.key -cert blacklisted_proxy_ca.cert \
      -config ../../../cert/openssl.cnf -crldays 365 \
      -out crl/blacklisted_proxy_ca.crl

  # Create CA certificate chain containing the CRLs of revoked leaf certificates.
  cat crl/cbsd_ca.crl crl/sas_ca.crl crl/proxy_ca.crl crl/root_ca.crl \
      crl/blacklisted_cbsd_ca.crl crl/blacklisted_sas_ca.crl crl/blacklisted_proxy_ca.crl > crl/ca.crl
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
