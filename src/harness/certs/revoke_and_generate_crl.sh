#!/bin/bash
set -e

mkdir -p crl

# If this appears in an error message, then you should use openssl_db instead.
export OPENSSL_CNF_CA_DIR="_use_openssl_db_instead_"

# Runs openssl using the database for a particular CA.
# $1 should match an existing db/ directory.
function openssl_db {
  OPENSSL_CNF_CA_DIR="db/$1" openssl "${@:2}" \
      -config ../../../cert/openssl.cnf \
      -cert "$1.cert" -keyfile "private/$1.key"
}

function revoke_certificate() {
  # Argument1: Name of the certificate to be revoked.

  # Fetch the Common Name to find out the issuer.
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
  openssl_db $CA ca -revoke $1
  generate_crl_chain
}

declare -ra CA_NAMES=(
  cbsd_ca
  proxy_ca
  revoked_cbsd_ca
  revoked_proxy_ca
  revoked_sas_ca
  root_ca
  sas_ca
)

function generate_crl_chain() {
  # Create a CRL with the revoked certificates from each CA.
  for ca in "${CA_NAMES[@]}"; do
    printf "\n\n"
    echo "Generating crl/$ca.crl"
    openssl_db "$ca" ca -gencrl -crldays 365 -out "crl/$ca.crl"
  done

  # Create CA certificate chain containing the CRLs of revoked leaf certificates.
  # TODO: CRLs should be DER-encoded, with one file per CA:
  #       https://tools.ietf.org/html/rfc5280#section-4.2.1.13
  cat crl/cbsd_ca.crl crl/sas_ca.crl crl/proxy_ca.crl crl/root_ca.crl \
      crl/revoked_cbsd_ca.crl crl/revoked_sas_ca.crl crl/revoked_proxy_ca.crl > crl/ca.crl
}

# Argument1: Type (-r, -u)
if [ "$1" == "-r" ]; then
  revoke_certificate $2
elif [ "$1" == "-u" ]; then
  generate_crl_chain
else
  echo "Wrong option other than (-r, -u)"
  exit -1
fi
