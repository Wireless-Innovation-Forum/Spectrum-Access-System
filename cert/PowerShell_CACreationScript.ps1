#Get to OpenSSL directory
$openssl = Read-Host -Prompt "Please enter the full directory path to your OpenSSL Bin folder. This folder should also have the openssl.cnf file present in it."
$cnf = Read-Host -Prompt "Enter the name of your configuration file (should be openssl.cnf)"
cd $openssl

#Set up storage files paths
#$dir = [environment]::GetFolderPath("MyDocuments")
$dir = New-Item -ItemType Directory -Force -Path "$openssl\root"
$papa = New-Item -ItemType Directory -Force -Path "$dir\ca"
$certi = New-Item -ItemType Directory -Force -Path "$papa\certs"
$crl = New-Item -ItemType Directory -Force -Path "$papa\crl"
$csr = New-Item -ItemType Directory -Force -Path "$papa\newcerts"
$key = New-Item -ItemType Directory -Force -Path "$papa\private"
$index = New-Item -ItemType file -Force $openssl\index.txt

#Root CA
$root = "wif_root_ca"
$sig = "_sign"
$ec = "ecc"
$rootValidity = "7300"
$intValidity = "5475"
$eeValidity = "1185"
$rootRSAKeysize = "4096"
$intRSAKeysize = "4096"
$eeRSAKeysize = "2048"

#RSA
Invoke-Expression "openssl req -new -x509 -newkey rsa:$rootRSAKeysize -sha384 -nodes -days $rootValidity -extensions $root -out $root.crt -keyout $root.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Root CA-1`" -config `"$openssl\$cnf`""
#EC
#Invoke-Expression "openssl ecparam -out wifECRoot.pkey -name secp384r1 -genkey" 
#Invoke-Expression "openssl req -new -x509 -key wifECRoot.pkey -sha384 -nodes -days 7300 -extensions wif_root_ca -out wifECRoot.crt -config `"$openssl\$cnf`""
#EC 2
#Invoke-Expression "openssl ecparam -out wifECRoot.pkey -name secp384r1 -genkey" 
#Invoke-Expression "openssl req -new -key wifECRoot.pkey -sha384 -nodes -days 7300 -extensions wif_root_ca -out wifECRoot.csr -config `"$openssl\$cnf`""
#Invoke-Expression "openssl ca -create_serial -out wifECRoot.crt -days 7300 -policy policy_anything -md sha384 -keyfile wifECRoot.pkey -selfsign -extensions wif_root_ca -config `"$openssl\$cnf`" -infiles wifECRoot.csr"

#SAS Intermediate
$sas = "wif_sas_ca"
$sas_sign = $sas + $sig

Invoke-Expression "openssl req -new -newkey rsa:$intRSAKeysize -nodes -reqexts $sas -out $sas.csr -keyout $sas.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA SAS CA-1`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir `"./root/ca/newcerts`" -batch -out $sas.crt -utf8 -days $intValidity -policy policy_anything -md sha384 -extensions $sas_sign -config `"$openssl\$cnf`" -in $sas.csr"

#SAS EE
$sas_ee = "wif_sas_req"
$sas_ee_sign = $sas_ee + $sig

Invoke-Expression "openssl req -new -newkey rsa:$eeRSAKeysize -nodes -reqexts $sas_ee -out $sas_ee.csr -keyout $sas_ee.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=SAS End-Entity Example`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $sas.crt -keyfile $sas.pkey -outdir `"./root/ca/newcerts`" -batch -out $sas_ee.crt -utf8 -days $eeValidity -policy policy_anything -md sha384 -extensions $sas_ee_sign -config `"$openssl\$cnf`" -in $sas_ee.csr"

#Operator Intermediate
$oper = "wif_oper_ca"
$oper_sign = $oper + $sig

Invoke-Expression "openssl req -new -newkey rsa:$intRSAKeysize -nodes -reqexts $oper -out $oper.csr -keyout $oper.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Operator CA-1`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir `"./root/ca/newcerts`" -batch -out $oper.crt -utf8 -days $intValidity -policy policy_anything -md sha384 -extensions $oper_sign -config `"$openssl\$cnf`" -in $oper.csr"

#Operator EE
$oper_ee = "wif_oper_req"
$oper_ee_sign = $oper_ee + $sig

Invoke-Expression "openssl req -new -newkey rsa:$eeRSAKeysize -nodes -reqexts $oper_ee -out $oper_ee.csr -keyout $oper_ee.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Operator End-Entity Example`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $oper.crt -keyfile $oper.pkey -outdir `"./root/ca/newcerts`" -batch -out $oper_ee.crt -utf8 -days $eeValidity -policy policy_anything -md sha384 -extensions $oper_ee_sign -config `"$openssl\$cnf`" -in $oper_ee.csr"

#Professional Installer Intermediate
$pi = "wif_pi_ca"
$pi_sign = $pi + $sig

Invoke-Expression "openssl req -new -newkey rsa:$intRSAKeysize -nodes -reqexts $pi -out $pi.csr -keyout $pi.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Installer CA-1`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir `"./root/ca/newcerts`" -batch -out $pi.crt -utf8 -days $intValidity -policy policy_anything -md sha384 -extensions $pi_sign -config `"$openssl\$cnf`" -in $pi.csr"

#Professional Installer EE
$pi_ee = "wif_pi_req"
$pi_ee_sign = $pi_ee + $sig

Invoke-Expression "openssl req -new -newkey rsa:$eeRSAKeysize -nodes -reqexts $pi_ee -out $pi_ee.csr -keyout $pi_ee.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Installer End-Entity Example`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $pi.crt -keyfile $pi.pkey -outdir `"./root/ca/newcerts`" -batch -out $pi_ee.crt -utf8 -days $eeValidity -policy policy_anything -md sha384 -extensions $pi_ee_sign -config `"$openssl\$cnf`" -in $pi_ee.csr"

#PAL Intermediate
$pal = "wif_pal_ca"
$pal_sign = $pal + $sig

Invoke-Expression "openssl req -new -newkey rsa:$intRSAKeysize -nodes -reqexts $pal -out $pal.csr -keyout $pal.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA PAL CA-1`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir `"./root/ca/newcerts`" -batch -out $pal.crt -utf8 -days $intValidity -policy policy_anything -md sha384 -extensions $pal_sign -config `"$openssl\$cnf`" -in $pal.csr"

#PAL EE
$pal_ee = "wif_pal_req"
$pal_ee_sign = $pal_ee + $sig

Invoke-Expression "openssl req -new -newkey rsa:$eeRSAKeysize -nodes -reqexts $pal_ee -out $pal_ee.csr -keyout $pal_ee.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=PAL End-Entity Example`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $pal.crt -keyfile $pal.pkey -outdir `"./root/ca/newcerts`" -batch -out $pal_ee.crt -utf8 -days $eeValidity -policy policy_anything -md sha384 -extensions $pal_ee_sign -config `"$openssl\$cnf`" -in $pal_ee.csr"

#Device Manufacturer Intermediate
$dm = "wif_dm_ca"
$dm_sign = $dm + $sig

Invoke-Expression "openssl req -new -newkey rsa:$intRSAKeysize -nodes -reqexts $dm -out $dm.csr -keyout $dm.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=WInnForum RSA Device Manufacturer CA-1`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $root.crt -keyfile $root.pkey -outdir `"./root/ca/newcerts`" -batch -out $dm.crt -utf8 -days $intValidity -policy policy_anything -md sha384 -extensions $dm_sign -config `"$openssl\$cnf`" -in $dm.csr"

#Device Manufacturer EE
$dm_ee = "wif_dm_req"
$dm_ee_sign = $dm_ee + $sig

Invoke-Expression "openssl req -new -newkey rsa:$eeRSAKeysize -nodes -reqexts $dm_ee -out $dm_ee.csr -keyout $dm_ee.pkey -subj `"/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=Device Manufacturer End-Entity Example`" -config `"$openssl\$cnf`""
Invoke-Expression "openssl ca -create_serial -cert $dm.crt -keyfile $dm.pkey -outdir `"./root/ca/newcerts`" -batch -out $dm_ee.crt -utf8 -days $eeValidity -policy policy_anything -md sha384 -extensions $dm_ee_sign -config `"$openssl\$cnf`" -in $dm_ee.csr"