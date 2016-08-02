This directory contains a sample openssl configuration for working
with SAS certificates.

To run the examples, use the CACreationScript scripts (PowerShell or BASH)
provided. These will generate a root/ directory containing the CA management
and tracking data, as well as several role-specific certificates.

-------------------------------------------------

You can also use the openssl.cnf file directly to experiment with the
certificates:

To set up, create a CA structure in a sub-directory:

```
mkdir sasCA
mkdir sasCA/newcerts
touch sasCA/index.txt
```

This creates the structure for a test CA management system.

Use this command to create the certificate outline which will become the CA root of trust:
```
openssl req -new -newkey rsa:2048 -keyout cakey.pem -out careq.pem -config openssl.cnf  -reqexts v3_req_sas_ca
```

This creates a private key file in `cakey.pem` and an unsigned certificate in `careq.pem` with the SAS-CA
extensions. Note: the certificate included has the password "sasca". The certificate can be examined using the command

```
openssl req -in careq.pem -text
```

Self-sign the certificate with this command:
```
openssl ca -create_serial -out cacert.pem -days 10000 -keyfile cakey.pem -selfsign -extensions v3_ca -config openssl.cnf -infiles careq.pem
```

This creates a self-signed cert at `cacert.pem` valid for many years. It can be viewed with

```
openssl x509 -in cacert.pem -text
```

Now move the files into the `sasCA` location and clean up:

```
mv cacert.pem sasCA
mkdir sasCA/private
mv cakey.pem sasCA/private
rm careq.pem
```

Congratulations! You have created and installed a test SAS CA authority
root of trust which can be used with the `openssl` tool to manage the PKI.
If you wish to use the root of trust checked into the repository, the CA
password is "sasca".

*Working with the CA*

To create certificates of various kinds, use these commands:

```
openssl req -new -newkey rsa:2048 -nodes -keyout saskey.pem -out sasreq.pem -config openssl.cnf -reqexts sas_req
```

This request can again be viewed with `openssl req -in sasreq.pem -text`

The request can be signed with the CA using this command:

```
openssl ca -config openssl.cnf -days 600 -out sascert.pem -infiles sasreq.pem
```

Other certificate requests can be created using the other extension sections in the `openssl.cnf` file.
They can all be signed using the same mechanism. Examples:

```
openssl req -new -newkey rsa:2048 -nodes -keyout palkey.pem -out palreq.pem -config openssl.cnf -reqexts pal_req

openssl req -new -newkey rsa:2048 -nodes -keyout devkey.pem -out devreq.pem -config openssl.cnf -reqexts device_req

openssl req -new -newkey rsa:2048 -nodes -keyout inskey.pem -out insreq.pem -config openssl.cnf -reqexts installer_req

openssl req -new -newkey rsa:2048 -nodes -keyout operkey.pem -out operreq.pem -config openssl.cnf -reqexts oper_req
```

There is also a section for creating equipment requests, which can then be signed with
the DEVICE intermediate certificate. To use it use `-reqexts unit_req`. A DEVICE intermediate
can be managed in the same way the `/sasCA` certificate is managed.

A note about TEST:TRUE: This extension explicitly marks a certificate as not being a
live production certificate. Clearly security should never rely on this marker; it
should only rely on the live root of trust certificate. The extension is simply used
for explicit marking of test certificates so they can easily be detected by generic
tooling and provide for simple disambiguation of any internal processes in the CBRS
ecosystem.


