#!/bin/bash -e

# Remove the unknown TEST extension to get usable certificate ...
sed -i '/TEST = critical, ASN1:NULL/d' ../../../cert/openssl.cnf

# Setup: build intermediate directories.
rm -rf root/
mkdir root
touch index.txt
echo -n 'unique_subject = no' >> index.txt.attr

function generate_cbsd_short_lived_certificate()
{
#   Argument1: Name of the certificate to be generated
#   Argument2: Time (in minutes)

#   Create certificate for test case which use short lived certificate
    if [ -f cbsd_ca.cert -a -f cbsd_ca.key ]; then
        echo "Create short lived certificate"
        current_time=`date -u  +%y%m%d%H%M%SZ`
        offset=$2
        enddate_value=$(date -u -d "now + $offset minutes" '+%y%m%d%H%M%SZ')

        # Generate normal operation short_lived certificate/key.
        echo "\n\nGenerate 'short_lived' certificate/key"
        openssl req -new -newkey rsa:2048 -nodes \
            -reqexts cbsd_req -config ../../../cert/openssl.cnf \
            -out $1.csr -keyout $1.key \
            -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN=short lived device"
        openssl ca -cert cbsd_ca.cert -keyfile cbsd_ca.key -in $1.csr \
            -out $1.cert -outdir ./root \
            -policy policy_anything -extensions cbsd_req_sign -config ../../../cert/openssl.cnf \
            -batch -notext -create_serial -utf8 -days 1185 -md sha384 -enddate $enddate_value
        return 0
    fi
    echo "The intermediate cbsd ca file not found"
    return -1
}

function generate_dp_short_lived_certificate()
{
#   Argument1: Name of the certificate to be generated
#   Argument2: Time (in minutes)

# Create certificate for test case which use short lived domain proxy certificate\
    if [ -f proxy_ca.cert -a -f proxy_ca.key ]; then
        echo "Create short lived certificate"
        current_time=`date -u  +%y%m%d%H%M%SZ`
        offset=$2
        enddate_value=$(date -u -d "now + $offset minutes" '+%y%m%d%H%M%SZ')

        # Generate normal operation short_lived domain proxy certificate/key.
        echo "\n\nGenerate 'short_lived' certificate/key"
        openssl req -new -newkey rsa:2048 -nodes \
            -reqexts oper_req -config ../../../cert/openssl.cnf \
            -out $1.csr -keyout $1.key \
            -subj "/C=US/ST=District of Columbia/L=Washington/O=Wireless Innovation Forum/OU=www.wirelessinnovation.org/CN= short lived domain proxy"
        openssl ca -cert proxy_ca.cert -keyfile proxy_ca.key -in $1.csr \
            -out $1.cert -outdir ./root \
            -policy policy_anything -extensions oper_req_sign -config ../../../cert/openssl.cnf \
            -batch -notext -create_serial -utf8 -days 1185 -md sha384 -enddate $enddate_value
        return 0
    fi
    echo "The intermediate domain proxy ca file not found"
    return -1
}
# Argument1 : Type (CBSD, DomainProxy)
if [ "$1" == "CBSD"  ]; then
    generate_cbsd_short_lived_certificate  $2 $3
elif [ "$1" == "DomainProxy"  ]; then
    generate_dp_short_lived_certificate   $2 $3
else
    echo "wrong option other than (CBSD, Domain_Proxy)"
    exit -1
fi
rm -rf root
rm index.txt*
rm *.csr
