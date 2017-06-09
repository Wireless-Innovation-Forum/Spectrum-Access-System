This directory contains the certificates used by the test harness to connect
with the SAS under test.

The certificates which are checked into GitHub are merely placeholders. SAS
administrators should replace them with valid certificates before testing.

* client.[cert|key] - used in all tests not concerned with security-related
  features and tests utilizing a domain proxy

* ca.cert - used by the test harness to authenticate the SAS under test

* admin_client.[cert|key] - used to authenticate the test harness when
  connecting to the SAS testing API


