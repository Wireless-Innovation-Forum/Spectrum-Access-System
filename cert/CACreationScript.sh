#!/bin/bash

#=============
#Copyright 2016 SAS Project Authors. All Rights Reserved.
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
#=============

echo Run this script from the directory containing the CBRS openssl.cnf file present in it. The openssl command must be present on the path.

echo Usage: ./CACreationScript.sh

echo Run this script with below arguments in order to generate CBSD EndEntity Certificate using pre define key/CSR

echo Usage: ./CACreationScript.sh pkey cbsd_ee.pkey
echo Usage: ./CACreationScript.sh csr cbsd_ee.csr

DIR=./root
PAPA=$DIR/ca
CERTI=$PAPA/certs
CRL=$PAPA/crl
CSR=$PAPA/newcerts
KEY=$PAPA/private
INDEX=./index.txt

mkdir -p $DIR
mkdir -p $PAPA
mkdir -p $CERTI
mkdir -p $CRL
mkdir -p $CSR
mkdir -p $KEY
touch $INDEX

ROOT=root_ca
SIG=_sign
EC=ecc
ROOT_VALIDITY=7300
INT_VALIDITY=5475
EE_VALIDITY=1185
ROOT_RSA_KEY_SIZE=4096
INT_RSA_KEY_SIZE=4096
EE_RSA_KEY_SIZE=2048

if [ $# -eq 2 ]
then
  if [ "$1" == "pkey" ]
  then
    cp $2 cbsd_req.pkey  
    #cp $2 cbsd_oem_req.pkey
  elif [ "$1" == "csr" ]
  then
    cp $2 cbsd_req.csr  
    #cp $2 cbsd_oem_req.csr
  fi
else
  rm cbsd_req.pkey cbsd_req.csr
  #rm cbsd_oem_req.pkey cbsd_oem_req.csr 
fi
  
#ROOT

#RSA
openssl req -new -x509 -newkey rsa:$ROOT_RSA_KEY_SIZE -sha384 -nodes -days $ROOT_VALIDITY -extensions $ROOT -out $ROOT.crt -keyout $ROOT.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Root CA-1" -config openssl.cnf

#EC
#openssl ecparam -out wifECRoot.pkey -name secp384r1 -genkey
#openssl req -new -x509 -key wifECRoot.pkey -sha384 -nodes -days $ROOT_VALIDITY -extensions $ROOT -out wifECRoot.crt -config openssl.cnf
#EC 2
#openssl ecparam -out wifECRoot.pkey -name secp384r1 -genkey
#openssl req -new -key wifECRoot.pkey -sha384 -nodes -days $ROOT_VALIDITY -extensions $ROOT -out wifECRoot.csr -config openssl.cnf
#openssl ca -create_serial -out wifECRoot.crt -days $ROOT_VALIDITY -policy policy_anything -md sha384 -keyfile wifECRoot.pkey -selfsign -extensions root_ca -config openssl.cnf -infiles wifECRoot.csr

#SAS Intermediate
SAS=sas_ca
SAS_SIGN=$SAS$SIG

openssl req -new -newkey rsa:$INT_RSA_KEY_SIZE -nodes -reqexts $SAS -out $SAS.csr -keyout $SAS.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA SAS CA-1" -config openssl.cnf

openssl ca -create_serial -cert $ROOT.crt -keyfile $ROOT.pkey -outdir ./root/ca/newcerts -batch -out $SAS.crt -utf8 -days $INT_VALIDITY -policy policy_anything -md sha384 -extensions $SAS_SIGN -config openssl.cnf -in $SAS.csr

#SAS EE
SAS_EE=sas_req
SAS_EE_SIGN=$SAS_EE$SIG

openssl req -new -newkey rsa:$EE_RSA_KEY_SIZE -nodes -reqexts $SAS_EE -out $SAS_EE.csr -keyout $SAS_EE.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS End-Entity Example" -config openssl.cnf

openssl ca -create_serial -cert $SAS.crt -keyfile $SAS.pkey -outdir $CSR -batch -out $SAS_EE.crt -utf8 -days $EE_VALIDITY -policy policy_anything -md sha384 -extensions $SAS_EE_SIGN -config openssl.cnf -in $SAS_EE.csr

#Operator Intermediate
OPER=oper_ca
OPER_SIGN=$OPER$SIG

openssl req -new -newkey rsa:$INT_RSA_KEY_SIZE -nodes -reqexts $OPER -out $OPER.csr -keyout $OPER.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Operator CA-1" -config openssl.cnf

openssl ca -create_serial -cert $ROOT.crt -keyfile $ROOT.pkey -outdir $CSR -batch -out $OPER.crt -utf8 -days $INT_VALIDITY -policy policy_anything -md sha384 -extensions $OPER_SIGN -config openssl.cnf -in $OPER.csr

#Operator EE
OPER_EE=oper_req
OPER_EE_SIGN=$OPER_EE$SIG

openssl req -new -newkey rsa:$EE_RSA_KEY_SIZE -nodes -reqexts $OPER_EE -out $OPER_EE.csr -keyout $OPER_EE.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Operator End-Entity Example" -config openssl.cnf

openssl ca -create_serial -cert $OPER.crt -keyfile $OPER.pkey -outdir $CSR -batch -out $OPER_EE.crt -utf8 -days $EE_VALIDITY -policy policy_anything -md sha384 -extensions $OPER_EE_SIGN -config openssl.cnf -in $OPER_EE.csr

#Professional Installer Intermediate
PI=pi_ca
PI_SIGN=$PI$SIG

openssl req -new -newkey rsa:$INT_RSA_KEY_SIZE -nodes -reqexts $PI -out $PI.csr -keyout $PI.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Installer CA-1" -config openssl.cnf

openssl ca -create_serial -cert $ROOT.crt -keyfile $ROOT.pkey -outdir $CSR -batch -out $PI.crt -utf8 -days $INT_VALIDITY -policy policy_anything -md sha384 -extensions $PI_SIGN -config openssl.cnf -in $PI.csr

#Professional Installer EE
PI_EE=pi_req
PI_EE_SIGN=$PI_EE$SIG

openssl req -new -newkey rsa:$EE_RSA_KEY_SIZE -nodes -reqexts $PI_EE -out $PI_EE.csr -keyout $PI_EE.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Installer End-Entity Example" -config openssl.cnf

openssl ca -create_serial -cert $PI.crt -keyfile $PI.pkey -outdir $CSR -batch -out $PI_EE.crt -utf8 -days $EE_VALIDITY -policy policy_anything -md sha384 -extensions $PI_EE_SIGN -config openssl.cnf -in $PI_EE.csr

#PAL: TODO

#Device Intermediate
CBSD=cbsd_ca
CBSD_SIGN=$CBSD$SIG

openssl req -new -newkey rsa:$INT_RSA_KEY_SIZE -nodes -reqexts $CBSD -out $CBSD.csr -keyout $CBSD.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA CBSD CA-1" -config openssl.cnf

openssl ca -create_serial -cert $ROOT.crt -keyfile $ROOT.pkey -outdir $CSR -batch -out $CBSD.crt -utf8 -days $INT_VALIDITY -policy policy_anything -md sha384 -extensions $CBSD_SIGN -config openssl.cnf -in $CBSD.csr

#Device EE
CBSD_EE=cbsd_req
CBSD_EE_SIGN=$CBSD_EE$SIG

if [ -f $CBSD_EE.pkey ]
then
  openssl req -new -nodes -reqexts $CBSD_EE -out $CBSD_EE.csr -key $CBSD_EE.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=CBSD End-Entity Example" -config openssl.cnf
elif [ ! -f $CBSD_EE.csr ]
then
  openssl req -new -newkey rsa:$EE_RSA_KEY_SIZE -nodes -reqexts $CBSD_EE -out $CBSD_EE.csr -keyout $CBSD_EE.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=CBSD End-Entity Example" -config openssl.cnf
fi

openssl ca -create_serial -cert $CBSD.crt -keyfile $CBSD.pkey -outdir $CSR -batch -out $CBSD_EE.crt -utf8 -days $EE_VALIDITY -policy policy_anything -md sha384 -extensions $CBSD_EE_SIGN -config openssl.cnf -in $CBSD_EE.csr

#Device OEM Intermediate
CBSD_OEM=cbsd_oem_ca
CBSD_OEM_SIGN=$CBSD_OEM$SIG

openssl req -new -newkey rsa:$INT_RSA_KEY_SIZE -nodes -reqexts $CBSD_OEM -out $CBSD_OEM.csr -keyout $CBSD_OEM.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA CBSD OEM CA-1" -config openssl.cnf

openssl ca -create_serial -cert $CBSD.crt -keyfile $CBSD.pkey -outdir $CSR -batch -out $CBSD_OEM.crt -utf8 -days $INT_VALIDITY -policy policy_anything -md sha384 -extensions $CBSD_OEM_SIGN -config openssl.cnf -in $CBSD_OEM.csr

#Device OEM EE
CBSD_OEM_EE=cbsd_oem_req
CBSD_OEM_EE_SIGN=$CBSD_OEM_EE$SIG

if [ -f $CBSD_OEM_EE.pkey ]
then
  openssl req -new -nodes -reqexts $CBSD_OEM_EE -out $CBSD_OEM_EE.csr -key $CBSD_OEM_EE.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=CBSD OEM End-Entity Example" -config openssl.cnf
elif [ ! -f $CBSD_OEM_EE.csr ]
then
  openssl req -new -newkey rsa:$EE_RSA_KEY_SIZE -nodes -reqexts $CBSD_OEM_EE -out $CBSD_OEM_EE.csr -keyout $CBSD_OEM_EE.pkey -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=CBSD OEM End-Entity Example" -config openssl.cnf
fi

openssl ca -create_serial -cert $CBSD_OEM.crt -keyfile $CBSD_OEM.pkey -outdir $CSR -batch -out $CBSD_OEM_EE.crt -utf8 -days $EE_VALIDITY -policy policy_anything -md sha384 -extensions $CBSD_OEM_EE_SIGN -config openssl.cnf -in $CBSD_OEM_EE.csr

