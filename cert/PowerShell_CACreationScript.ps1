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


#Get to OpenSSL directory
$openssl = Read-Host -Prompt "Please enter the full directory path to your OpenSSL Bin folder. This folder should also have the openssl.cnf file present in it."
$cnf = Read-Host -Prompt "Enter the name of your configuration file (should be openssl.cnf)"
cd $openssl

#Set up storage files paths
#$top_dir = [environment]::GetFolderPath("MyDocuments")
$top_dir = New-Item -ItemType Directory -Force -Path "$openssl\root"
$ca_dir = New-Item -ItemType Directory -Force -Path "$top_dir\ca"
$cert_dir = New-Item -ItemType Directory -Force -Path "$ca_dir\certs"
$crl_dir = New-Item -ItemType Directory -Force -Path "$ca_dir\crl"
$csr_dir = New-Item -ItemType Directory -Force -Path "$ca_dir\newcerts"
$key_dir = New-Item -ItemType Directory -Force -Path "$ca_dir\private"
$index_file = New-Item -ItemType file -Force $openssl\index.txt

#Declare global variables
#Nomenclature
$sig = "_sign"
$ec = "ecc_"
#Validity periods
$root_validity = "7300"
$int_validity = "5475"
$10y_validity = "3650"
$39m_validity = "1185"
$27m_validity = "820"
$15m_validity = "455"
#Key Sizes
#RSA
$rsa_root_keysize = "2048"
$rsa_int_keysize = "2048"
$rsa_ee_keysize = "2048"
#ECC
$ecc_root_keysize = "384"
$ecc_int_keysize = "384"
$ecc_ee_keysize = "256"
#Subject DN Info
$country = "US"
$state = "District of Columbia"
$city = "Washington"
$organization = "Wireless Innovation Forum"
$organization_unit = "www.wirelessinnovation.org"

#Create the Root CAs
$root = "root_ca"
$root_ca_cn = "WInnForum RSA Root CA-1"
#Create the RSA Root CA
Invoke-Expression "openssl req -new -x509 -newkey rsa:$rsa_root_keysize -sha384 -nodes -days $root_validity -extensions $root -out $root.crt -keyout $root.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$root_ca_cn`" -config `"$openssl\$cnf`""

#TODO: Create the ECC Root CA
#Invoke-Expression "openssl ecparam -out $ec$root.pkey -name secp384r1 -genkey" 
#Invoke-Expression "openssl req -new -x509 -key $ec$root.pkey -sha384 -nodes -days $root_validity -extensions $root -out $ec$root.crt -config `"$openssl\$cnf`""
#EC 2
#Invoke-Expression "openssl ecparam -out $ec$root.pkey -name secp384r1 -genkey" 
#Invoke-Expression "openssl req -new -key $ec$root.pkey -sha384 -nodes -days $root_validity -extensions $root -out $ec$root.csr -config `"$openssl\$cnf`""
#Invoke-Expression "openssl ca -create_serial -out $ec$root.crt -days $root_validity -policy policy_anything -md sha384 -keyfile $ec$root.pkey -selfsign -extensions $root -config `"$openssl\$cnf`" -infiles $ec$root.csr"

#Create the RSA SAS Intermediate CA
$sas = "sas_ca"
$sas_sign = $sas + $sig
$sas_ca_cn = "WInnForum RSA SAS CA-1"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_int_keysize -nodes -reqexts $sas -out $sas.csr -keyout $sas.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$sas_ca_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir $csr_dir -batch -out $sas.crt -utf8 -days $int_validity -policy policy_anything -md sha384 -extensions $sas_sign -config `"$openssl\$cnf`" -in $sas.csr"

#Sign an example RSA SAS end-entity certificate with the RSA SAS Intermediate CA
$sas_ee = "sas_req"
$sas_ee_sign = $sas_ee + $sig
$sas_ee_cn = "SAS End-Entity Example"

#TODO: Create the ECC SAS Intermediate CA
#TODO: Sign an example ECC SAS end-entity certificate with the ECC SAS Intermediate CA

Invoke-Expression "openssl req -new -newkey rsa:$rsa_ee_keysize -nodes -reqexts $sas_ee -out $sas_ee.csr -keyout $sas_ee.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$sas_ee_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $sas.crt -keyfile $sas.pkey -outdir $csr_dir -batch -out $sas_ee.crt -utf8 -days $15m_validity -policy policy_anything -md sha384 -extensions $sas_ee_sign -config `"$openssl\$cnf`" -in $sas_ee.csr"

#Create the RSA CBSD Manufacturer Intermediate CA
$cbsd = "cbsd_ca"
$cbsd_sign = $cbsd + $sig
$cbsd_ca_cn = "WInnForum RSA CBSD CA-1"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_int_keysize -nodes -reqexts $cbsd -out $cbsd.csr -keyout $cbsd.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$cbsd_ca_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir $csr_dir -batch -out $cbsd.crt -utf8 -days $int_validity -policy policy_anything -md sha384 -extensions $cbsd_sign -config `"$openssl\$cnf`" -in $cbsd.csr"

#Sign an example RSA CBSD Manufacturer end-entity certificate with the RSA CBSD Manufacturer Intermediate CA
$cbsd_ee = "cbsd_req"
$cbsd_ee_sign = $cbsd_ee + $sig
$cbsd_ee_cn = "CBSD End-Entity Example"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_ee_keysize -nodes -reqexts $cbsd_ee -out $cbsd_ee.csr -keyout $cbsd_ee.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$cbsd_ee_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $cbsd.crt -keyfile $cbsd.pkey -outdir $csr_dir -batch -out $cbsd_ee.crt -utf8 -days $10y_validity -policy policy_anything -md sha384 -extensions $cbsd_ee_sign -config `"$openssl\$cnf`" -in $cbsd_ee.csr"

#TODO: Create the ECC CBSD Intermediate CA
#TODO: Sign an example ECC CBSD end-entity certificate with the ECC CBSD Intermediate CA

#Create the RSA CBSD OEM Intermediate CA
$cbsd_oem = "cbsd_oem_ca"
$cbsd_oem_sign = $cbsd_oem + $sig
$cbsd_oem_ca_cn = "WInnForum RSA CBSD OEM CA-1"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_int_keysize -nodes -reqexts $cbsd_oem -out $cbsd_oem.csr -keyout $cbsd_oem.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$cbsd_oem_ca_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $cbsd.crt -keyfile $cbsd.pkey -outdir $csr_dir -batch -out $cbsd_oem.crt -utf8 -days $int_validity -policy policy_anything -md sha384 -extensions $cbsd_oem_sign -config `"$openssl\$cnf`" -in $cbsd_oem.csr"

#Sign an example RSA CBSD OEM end-entity certificate with the RSA CBSD OEM Intermediate CA
$cbsd_oem_ee = "cbsd_oem_req"
$cbsd_oem_ee_sign = $cbsd_oem_ee + $sig
$cbsd_oem_ee_cn = "CBSD OEM End-Entity Example"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_ee_keysize -nodes -reqexts $cbsd_oem_ee -out $cbsd_oem_ee.csr -keyout $cbsd_oem_ee.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$cbsd_oem_ee_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $cbsd_oem.crt -keyfile $cbsd_oem.pkey -outdir $csr_dir -batch -out $cbsd_oem_ee.crt -utf8 -days $10y_validity -policy policy_anything -md sha384 -extensions $cbsd_oem_ee_sign -config `"$openssl\$cnf`" -in $cbsd_oem_ee.csr"

#TODO: Create the ECC CBSD OEM Intermediate CA
#TODO: Sign an example ECC CBSD OEM end-entity certificate with the ECC CBSD OEM Intermediate CA

#Create the RSA Operator Intermediate CA
$oper = "oper_ca"
$oper_sign = $oper + $sig
$oper_ca_cn = "WInnForum RSA Operator CA-1"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_int_keysize -nodes -reqexts $oper -out $oper.csr -keyout $oper.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$oper_ca_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir $csr_dir -batch -out $oper.crt -utf8 -days $int_validity -policy policy_anything -md sha384 -extensions $oper_sign -config `"$openssl\$cnf`" -in $oper.csr"

#Sign an example RSA Operator end-entity certificate with the RSA Operator Intermediate CA
$oper_ee = "oper_req"
$oper_ee_sign = $oper_ee + $sig
$oper_ee_cn = "Operator End-Entity Example"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_ee_keysize -nodes -reqexts $oper_ee -out $oper_ee.csr -keyout $oper_ee.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$oper_ee_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $oper.crt -keyfile $oper.pkey -outdir $csr_dir -batch -out $oper_ee.crt -utf8 -days $15m_validity -policy policy_anything -md sha384 -extensions $oper_ee_sign -config `"$openssl\$cnf`" -in $oper_ee.csr"

#TODO: Create the ECC Operator Intermediate CA
#TODO: Sign an example ECC Operator end-entity certificate with the ECC Operator Intermediate CA

#Create the RSA Professional Installer Intermediate CA
$pi = "pi_ca"
$pi_sign = $pi + $sig
$pi_ca_cn = "WInnForum RSA Installer CA-1"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_int_keysize -nodes -reqexts $pi -out $pi.csr -keyout $pi.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$pi_ca_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir $csr_dir -batch -out $pi.crt -utf8 -days $int_validity -policy policy_anything -md sha384 -extensions $pi_sign -config `"$openssl\$cnf`" -in $pi.csr"

#Sign an example RSA Professional Installer end-entity certificate with the RSA Professional Installer Intermediate CA
$pi_ee = "pi_req"
$pi_ee_sign = $pi_ee + $sig
$pi_ee_cn = "Installer End-Entity Example"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_ee_keysize -nodes -reqexts $pi_ee -out $pi_ee.csr -keyout $pi_ee.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$pi_ee_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $pi.crt -keyfile $pi.pkey -outdir $csr_dir -batch -out $pi_ee.crt -utf8 -days $27m_validity -policy policy_anything -md sha384 -extensions $pi_ee_sign -config `"$openssl\$cnf`" -in $pi_ee.csr"

#TODO: Create the ECC Professional Installer Intermediate CA
#TODO: Sign an example ECC Professional Installer end-entity certificate with the ECC Professional Installer Intermediate CA

#Create the RSA PAL Intermediate CA
$pal = "pal_ca"
$pal_sign = $pal + $sig
$pal_ca_cn = "WInnForum RSA PAL CA-1"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_int_keysize -nodes -reqexts $pal -out $pal.csr -keyout $pal.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$pal_ca_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir $csr_dir -batch -out $pal.crt -utf8 -days $int_validity -policy policy_anything -md sha384 -extensions $pal_sign -config `"$openssl\$cnf`" -in $pal.csr"

#Sign an example RSA PAL end-entity certificate with the RSA PAL Intermediate CA
$pal_ee = "pal_req"
$pal_ee_sign = $pal_ee + $sig
$pal_ee_cn = "PAL End-Entity Example"

Invoke-Expression "openssl req -new -newkey rsa:$rsa_ee_keysize -nodes -reqexts $pal_ee -out $pal_ee.csr -keyout $pal_ee.pkey -subj `"/C=$country/ST=$state/L=$city/O=$organization/OU=$organization_unit/CN=$pal_ee_cn`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $pal.crt -keyfile $pal.pkey -outdir $csr_dir -batch -out $pal_ee.crt -utf8 -days $39m_validity -policy policy_anything -md sha384 -extensions $pal_ee_sign -config `"$openssl\$cnf`" -in $pal_ee.csr"

#TODO: Create the ECC PAL Intermediate CA
#TODO: Sign an example ECC PAL end-entity certificate with the ECC PAL Intermediate CA