#    Copyright 2026 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Fresh credentials for local transport tests, independent of lab certificates."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def create_certificates(directory):
  directory = Path(directory)
  now = datetime.now(timezone.utc)
  ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
  ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Local test CA')])
  ca_cert = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
             .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
             .not_valid_before(now - timedelta(days=1))
             .not_valid_after(now + timedelta(days=7))
             .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
             .add_extension(x509.KeyUsage(False, False, False, False, False,
                                          True, True, False, False), critical=True)
             .sign(ca_key, hashes.SHA256()))
  paths = {'ca': str(directory / 'ca.pem')}
  Path(paths['ca']).write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
  for role, usage in [('server', ExtendedKeyUsageOID.SERVER_AUTH),
                      ('client', ExtendedKeyUsageOID.CLIENT_AUTH)]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(ca_name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=7))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), False)
            .add_extension(x509.ExtendedKeyUsage([usage]), False)
            .sign(ca_key, hashes.SHA256()))
    paths[role + '_cert'] = str(directory / (role + '.pem'))
    paths[role + '_key'] = str(directory / (role + '.key'))
    Path(paths[role + '_cert']).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    Path(paths[role + '_key']).write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
  return paths
