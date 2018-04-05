# SAS test cases

## Organization

The current test cases are based on the [WinnForum test specification](https://workspace.winnforum.org/higherlogic/ws/public/download/5637/WINNF-TS-0061-V1.1.0%20-%20WG4%20SAS%20Test%20and%20Certification%20Spec.pdf) v1.1 (Jan 2018)

## Security Test Cases

The SCS.11/16, SDS.11/16 and SSS.11/16 TCs just expect the handshake failure and do not validate the reason for failure.<br>
The correct way to run the fake_sas for these test cases is
<pre>
<code>
<b> $python fake_sas.py --verify_crl --ca ca_crl_chain.cert </b>
</code>
</pre>

To obtain the CRL file, the <b>simple CRL server</b> in <b>master</b> branch needs to be 
executed and a CRL chain can be retrieved from this server.

The steps are

1. Run the ‘simple CRL server’
<b> $ python simple_crl_server.py </b>
2. Use the menu option to blacklist a certificate (client cert or DP cert or SAS cert).
3. Use wget on the simple CRL server URL to get the CRL chain file.
<b> wget http://localhost:9007/ca.crl </b>
4. Concatenate the CA chain file and the CRL file to create a combined CA chain and CRL chain file.
<b> cat certs/ca.cert ca.crl > ca_crl_chain.cert </b>
5. Run the fake_sas with the <b>--verify_crl</b> and <b>--ca ca_crl_chain.cert</b> option.

The details of using the <b>simple CRL server</b> is documented under <b>harness/CRLServer-README.md file</b>. 
The simple CRL server is also enhanced with simpler menu option and ability to blacklist intermediate CAs.

If a SAS UUT is used for testing the CRL test cases then the steps to manually download the CRL file using wget and 
concatenating it with the CA chain would not be needed as the <b>simple CRL server</b> is used to mimic an actual 
CRL server and the CDP URL field of the certificates is updated with the URL of the <b>simple CRL server</b>. 
As fake_sas updates are on a best effort basis and the intention is to keep it simple, the automatic retrieval of 
CRL file is not implemented in fake_sas.

However to make it bit more easier to run the SXS.11/16 test cases, a default CRL file containing the CA chain and 
the CRL chain containing the blacklisted certificates for SXS.11/16 test cases is created. 
So the fake_sas can be run with the ca file <b>ca_crl_chain_sxs11.cert</b> without running the <b>simple CRL server</b>.
