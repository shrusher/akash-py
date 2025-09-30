#!/usr/bin/env python3
"""
Certificate mTLS module tests - validation and functional tests.

Validation tests: Validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Functional tests: Test enhanced certificate module with mTLS certificate generation,
gRPC client functionality, SSL context management, and secure provider communication
using mocking to isolate functionality and test error handling scenarios.

Run: python cert_mtls_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pytest
import sys
from unittest.mock import Mock, patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.modules.cert.client import CertClient


class TestmTLSCertificateGeneration:
    """Test mTLS certificate generation and file management."""

    def test_create_certificate_for_mtls_success(self):
        """Test successful mTLS certificate generation and file storage."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.tx.ec') as mock_ec, \
                patch('akash.modules.cert.tx.x509') as mock_x509, \
                patch('akash.modules.cert.tx.serialization') as mock_serialization, \
                patch('akash.modules.cert.tx.hashes') as mock_hashes, \
                patch('builtins.open', mock_open()) as mock_file, \
                patch('os.makedirs') as mock_makedirs:
            mock_private_key = Mock()
            mock_public_key = Mock()
            mock_private_key.public_key.return_value = mock_public_key
            mock_ec.generate_private_key.return_value = mock_private_key
            mock_ec.SECP256R1.return_value = "SECP256R1"

            mock_cert_builder = Mock()
            mock_cert = Mock()
            mock_cert.serial_number = 123456789
            mock_x509.CertificateBuilder.return_value = mock_cert_builder
            mock_cert_builder.subject_name.return_value = mock_cert_builder
            mock_cert_builder.issuer_name.return_value = mock_cert_builder
            mock_cert_builder.public_key.return_value = mock_cert_builder
            mock_cert_builder.serial_number.return_value = mock_cert_builder
            mock_cert_builder.not_valid_before.return_value = mock_cert_builder
            mock_cert_builder.not_valid_after.return_value = mock_cert_builder
            mock_cert_builder.sign.return_value = mock_cert

            mock_name = Mock()
            mock_x509.Name.return_value = mock_name

            mock_serialization.Encoding.PEM = "PEM"
            mock_serialization.Encoding.DER = "DER"
            mock_serialization.PrivateFormat.PKCS8 = "PKCS8"
            mock_serialization.PublicFormat.SubjectPublicKeyInfo = "SubjectPublicKeyInfo"
            mock_serialization.NoEncryption.return_value = "NoEncryption"

            cert_pem_bytes = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            key_pem_bytes = b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
            pubkey_der_bytes = b"test_public_key_der_data"

            mock_cert.public_bytes.return_value = cert_pem_bytes
            mock_private_key.private_bytes.return_value = key_pem_bytes
            mock_public_key.public_bytes.return_value = pubkey_der_bytes

            with patch.object(cert_client, 'publish_client_certificate') as mock_publish:
                mock_publish.return_value = Mock(success=True, tx_hash="TEST123")

                result = cert_client.create_certificate_for_mtls(mock_wallet)

                assert result["status"] == "success"
                assert result["tx_hash"] == "TEST123"
                assert "file_paths" in result
                assert "client_cert" in result["file_paths"]
                assert "client_key" in result["file_paths"]
                assert "ca_cert" in result["file_paths"]

    def test_create_certificate_for_mtls_file_creation(self):
        """Test that certificate files are created with correct content."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.tx.ec') as mock_ec, \
                patch('akash.modules.cert.tx.x509') as mock_x509, \
                patch('akash.modules.cert.tx.serialization') as mock_serialization, \
                patch('akash.modules.cert.tx.hashes'), \
                patch('builtins.open', mock_open()) as mock_file, \
                patch('os.makedirs') as mock_makedirs:
            mock_private_key = Mock()
            mock_public_key = Mock()
            mock_private_key.public_key.return_value = mock_public_key
            mock_ec.generate_private_key.return_value = mock_private_key
            mock_ec.SECP256R1.return_value = "SECP256R1"

            mock_cert_builder = Mock()
            mock_cert = Mock()
            mock_cert.serial_number = 123456789
            mock_x509.CertificateBuilder.return_value = mock_cert_builder
            mock_cert_builder.subject_name.return_value = mock_cert_builder
            mock_cert_builder.issuer_name.return_value = mock_cert_builder
            mock_cert_builder.public_key.return_value = mock_cert_builder
            mock_cert_builder.serial_number.return_value = mock_cert_builder
            mock_cert_builder.not_valid_before.return_value = mock_cert_builder
            mock_cert_builder.not_valid_after.return_value = mock_cert_builder
            mock_cert_builder.sign.return_value = mock_cert

            mock_name = Mock()
            mock_x509.Name.return_value = mock_name

            mock_serialization.Encoding.PEM = "PEM"
            mock_serialization.Encoding.DER = "DER"
            mock_serialization.PrivateFormat.PKCS8 = "PKCS8"
            mock_serialization.PublicFormat.SubjectPublicKeyInfo = "SubjectPublicKeyInfo"
            mock_serialization.NoEncryption.return_value = "NoEncryption"

            cert_pem_bytes = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            key_pem_bytes = b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
            pubkey_der_bytes = b"test_public_key_der_data"

            mock_cert.public_bytes.return_value = cert_pem_bytes
            mock_private_key.private_bytes.return_value = key_pem_bytes
            mock_public_key.public_bytes.return_value = pubkey_der_bytes

            with patch.object(cert_client, 'publish_client_certificate') as mock_publish:
                mock_publish.return_value = Mock(success=True, tx_hash="TEST123")

                result = cert_client.create_certificate_for_mtls(mock_wallet)

                mock_makedirs.assert_called_with("certs", exist_ok=True)

                assert mock_file().write.called
                assert result["status"] == "success"

    def test_create_certificate_for_mtls_transaction_failure(self):
        """Test mTLS certificate creation with transaction broadcast failure."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.tx.ec') as mock_ec, \
                patch('akash.modules.cert.tx.x509') as mock_x509, \
                patch('akash.modules.cert.tx.serialization') as mock_serialization, \
                patch('akash.modules.cert.tx.hashes'), \
                patch('builtins.open', mock_open()):
            mock_private_key = Mock()
            mock_public_key = Mock()
            mock_private_key.public_key.return_value = mock_public_key
            mock_ec.generate_private_key.return_value = mock_private_key
            mock_ec.SECP256R1.return_value = "SECP256R1"

            mock_cert_builder = Mock()
            mock_cert = Mock()
            mock_cert.serial_number = 123456789
            mock_x509.CertificateBuilder.return_value = mock_cert_builder
            mock_cert_builder.subject_name.return_value = mock_cert_builder
            mock_cert_builder.issuer_name.return_value = mock_cert_builder
            mock_cert_builder.public_key.return_value = mock_cert_builder
            mock_cert_builder.serial_number.return_value = mock_cert_builder
            mock_cert_builder.not_valid_before.return_value = mock_cert_builder
            mock_cert_builder.not_valid_after.return_value = mock_cert_builder
            mock_cert_builder.sign.return_value = mock_cert

            mock_name = Mock()
            mock_x509.Name.return_value = mock_name

            mock_serialization.Encoding.PEM = "PEM"
            mock_serialization.Encoding.DER = "DER"
            mock_serialization.PrivateFormat.PKCS8 = "PKCS8"
            mock_serialization.PublicFormat.SubjectPublicKeyInfo = "SubjectPublicKeyInfo"
            mock_serialization.NoEncryption.return_value = "NoEncryption"

            cert_pem_bytes = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            key_pem_bytes = b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
            pubkey_der_bytes = b"test_public_key_der_data"

            mock_cert.public_bytes.return_value = cert_pem_bytes
            mock_private_key.private_bytes.return_value = key_pem_bytes
            mock_public_key.public_bytes.return_value = pubkey_der_bytes

            with patch.object(cert_client, 'publish_client_certificate') as mock_publish:
                mock_publish.return_value = Mock(success=False, error="Network error")

                result = cert_client.create_certificate_for_mtls(mock_wallet)

                assert result["status"] == "error"
                assert "Network error" in result["error"]

    def test_create_certificate_for_mtls_cryptographic_error(self):
        """Test mTLS certificate creation with cryptographic errors."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.tx.ec.generate_private_key', side_effect=Exception("Crypto error")):
            result = cert_client.create_certificate_for_mtls(mock_wallet)

            assert result["status"] == "error"
            assert "Crypto error" in result["error"]

    def test_create_certificate_for_mtls_file_error(self):
        """Test mTLS certificate creation with file system errors."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.tx.ec') as mock_ec, \
                patch('akash.modules.cert.tx.x509') as mock_x509, \
                patch('akash.modules.cert.tx.serialization') as mock_serialization, \
                patch('akash.modules.cert.tx.hashes'):
            mock_private_key = Mock()
            mock_public_key = Mock()
            mock_private_key.public_key.return_value = mock_public_key
            mock_ec.generate_private_key.return_value = mock_private_key
            mock_ec.SECP256R1.return_value = "SECP256R1"

            mock_cert_builder = Mock()
            mock_cert = Mock()
            mock_cert.serial_number = 123456789
            mock_x509.CertificateBuilder.return_value = mock_cert_builder
            mock_cert_builder.subject_name.return_value = mock_cert_builder
            mock_cert_builder.issuer_name.return_value = mock_cert_builder
            mock_cert_builder.public_key.return_value = mock_cert_builder
            mock_cert_builder.serial_number.return_value = mock_cert_builder
            mock_cert_builder.not_valid_before.return_value = mock_cert_builder
            mock_cert_builder.not_valid_after.return_value = mock_cert_builder
            mock_cert_builder.sign.return_value = mock_cert

            mock_name = Mock()
            mock_x509.Name.return_value = mock_name

            mock_serialization.Encoding.PEM = "PEM"
            mock_serialization.Encoding.DER = "DER"
            mock_serialization.PrivateFormat.PKCS8 = "PKCS8"
            mock_serialization.PublicFormat.SubjectPublicKeyInfo = "SubjectPublicKeyInfo"
            mock_serialization.NoEncryption.return_value = "NoEncryption"

            cert_pem_bytes = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            key_pem_bytes = b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
            pubkey_der_bytes = b"test_public_key_der_data"

            mock_cert.public_bytes.return_value = cert_pem_bytes
            mock_private_key.private_bytes.return_value = key_pem_bytes
            mock_public_key.public_bytes.return_value = pubkey_der_bytes

            with patch.object(cert_client, 'publish_client_certificate') as mock_publish, \
                    patch('builtins.open', side_effect=IOError("Permission denied")):
                mock_publish.return_value = Mock(success=True, tx_hash="TEST123")
                result = cert_client.create_certificate_for_mtls(mock_wallet)

                assert result["status"] == "error"
                assert "Permission denied" in result["error"]

    def test_create_certificate_for_mtls_custom_ca(self):
        """Test mTLS certificate creation with custom CA certificate."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        ca_cert_path = "/path/to/custom/ca.pem"

        with patch('akash.modules.cert.tx.ec') as mock_ec, \
                patch('akash.modules.cert.tx.x509') as mock_x509, \
                patch('akash.modules.cert.tx.serialization') as mock_serialization, \
                patch('akash.modules.cert.tx.hashes'), \
                patch('builtins.open', mock_open(read_data="custom_ca_data")) as mock_file:
            mock_private_key = Mock()
            mock_public_key = Mock()
            mock_private_key.public_key.return_value = mock_public_key
            mock_ec.generate_private_key.return_value = mock_private_key
            mock_ec.SECP256R1.return_value = "SECP256R1"

            mock_cert_builder = Mock()
            mock_cert = Mock()
            mock_cert.serial_number = 123456789
            mock_x509.CertificateBuilder.return_value = mock_cert_builder
            mock_cert_builder.subject_name.return_value = mock_cert_builder
            mock_cert_builder.issuer_name.return_value = mock_cert_builder
            mock_cert_builder.public_key.return_value = mock_cert_builder
            mock_cert_builder.serial_number.return_value = mock_cert_builder
            mock_cert_builder.not_valid_before.return_value = mock_cert_builder
            mock_cert_builder.not_valid_after.return_value = mock_cert_builder
            mock_cert_builder.sign.return_value = mock_cert

            mock_name = Mock()
            mock_x509.Name.return_value = mock_name

            mock_serialization.Encoding.PEM = "PEM"
            mock_serialization.Encoding.DER = "DER"
            mock_serialization.PrivateFormat.PKCS8 = "PKCS8"
            mock_serialization.PublicFormat.SubjectPublicKeyInfo = "SubjectPublicKeyInfo"
            mock_serialization.NoEncryption.return_value = "NoEncryption"

            cert_pem_bytes = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            key_pem_bytes = b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
            pubkey_der_bytes = b"test_public_key_der_data"

            mock_cert.public_bytes.return_value = cert_pem_bytes
            mock_private_key.private_bytes.return_value = key_pem_bytes
            mock_public_key.public_bytes.return_value = pubkey_der_bytes

            with patch.object(cert_client, 'publish_client_certificate') as mock_publish:
                mock_publish.return_value = Mock(success=True, tx_hash="TEST123")

                result = cert_client.create_certificate_for_mtls(mock_wallet, ca_cert_path)

                assert result["status"] == "success"
                mock_file.assert_called()


class TestSSLContextGeneration:
    """Test SSL context generation for gRPC connections."""

    def test_create_ssl_context_success(self):
        """Test successful SSL context creation."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.utils.ssl') as mock_ssl, \
                patch('builtins.open', mock_open(read_data="cert_data")), \
                patch('os.path.exists', return_value=True):
            mock_context = Mock()
            mock_ssl.create_default_context.return_value = mock_context

            result = cert_client.create_ssl_context()

            assert result["status"] == "success"
            assert "ssl_context" in result
            assert result["ssl_context"] == mock_context

    def test_create_ssl_context_missing_files(self):
        """Test SSL context creation with missing certificate files."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('os.path.exists', return_value=False):
            result = cert_client.create_ssl_context()

            assert result["status"] == "error"
            assert "Certificate files not found" in result["error"]

    def test_create_ssl_context_file_read_error(self):
        """Test SSL context creation with file read errors."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('os.path.exists', return_value=True), \
                patch('akash.modules.cert.utils.ssl.create_default_context', side_effect=IOError("File read error")):
            result = cert_client.create_ssl_context()

            assert result["status"] == "error"
            assert "File read error" in result["error"]

    def test_create_ssl_context_ssl_error(self):
        """Test SSL context creation with SSL configuration errors."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('os.path.exists', return_value=True), \
                patch('builtins.open', mock_open(read_data="cert_data")), \
                patch('akash.modules.cert.utils.ssl.create_default_context', side_effect=Exception("SSL error")):
            result = cert_client.create_ssl_context()

            assert result["status"] == "error"
            assert "SSL error" in result["error"]


class TestCertificateValidation:
    """Test certificate validation and verification functions."""

    def test_validate_ssl_certificate_valid_pem(self):
        """Test SSL certificate validation with valid PEM format."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.tx.x509.load_pem_x509_certificate') as mock_load:
            mock_load.return_value = Mock()

            valid_cert_pem = """-----BEGIN CERTIFICATE-----
MIIBmjCCAUGgAwIBAgIHBjDlLlU04DAKBggqhkjOPQQDAjA3MTUwMwYDVQQDDCxh
a2FzaDFxbm5oaGd6eGoyNGYya2xkNXloeTV2NGg0czdyMjk1YWs1Z2p3NDAeFw0y
MzA5MjQxNjQ5NDZaFw0yNDA5MjMxNjQ5NDZaMDcxNTAzBgNVBAMMKmFrYXNoMXFu
bmhoZ3p4ajI0ZjJrbGQ1eWh5NXY0aDRzN3IyOTVhazVnanc0MFkwEwYHKoZIzj0C
AQYIKoZIzj0DAQcDQgAE8q7w1p5q5qR5X5r5q5r5q5r5q5r5q5r5q5r5q5r5q5r5
q5r5q5r5q5r5q5r5q5r5q5r5q5r5q5r5q5r5q5r5qKNTMFEwHQYDVR0OBBYEFI5/
5q5q5q5q5q5q5q5q5q5q5q5q5q5q5MB8GA1UdIwQYMBaAFI5/5q5q5q5q5q5q5q5q
5q5q5q5q5q5q5MA8GA1UdEwEB/wQCMAAwCgYIKoZIzj0EAwIDSAAwRQIhAP5q5q5q
5q5q5q5q5q5q5q5q5q5q5q5q5q5q5q5q5q5qAiByI5q5q5q5q5q5q5q5q5q5q5q5q
5q5q5q5q5q5q5q5q5g==
-----END CERTIFICATE-----"""

            result = cert_client.validate_ssl_certificate(valid_cert_pem)
            assert result == True
            mock_load.assert_called_once()

    def test_validate_ssl_certificate_invalid_pem(self):
        """Test SSL certificate validation with invalid PEM format."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        invalid_cert = "not a pem certificate"

        with patch('akash.modules.cert.utils.logger') as mock_logger:
            result = cert_client.validate_ssl_certificate(invalid_cert)
            assert result == False
            mock_logger.error.assert_called()

    def test_validate_ssl_certificate_missing_markers(self):
        """Test SSL certificate validation with missing BEGIN/END markers."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        invalid_cert = "MIIBmjCCAUGgAwIBAgIHBjDlLlU04D"

        with patch('akash.modules.cert.utils.logger') as mock_logger:
            result = cert_client.validate_ssl_certificate(invalid_cert)
            assert result == False
            mock_logger.error.assert_called()

    def test_validate_ssl_certificate_empty_input(self):
        """Test SSL certificate validation with empty input."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.utils.logger') as mock_logger:
            result = cert_client.validate_ssl_certificate("")
            assert result == False
            mock_logger.error.assert_called()

    def test_validate_ssl_certificate_none_input(self):
        """Test SSL certificate validation with None input."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.utils.logger') as mock_logger:
            result = cert_client.validate_ssl_certificate(None)
            assert result == False
            mock_logger.error.assert_called()


class TestCertificateFileManagement:
    """Test certificate file management operations."""

    def test_get_cert_file_paths(self):
        """Test certificate file path generation."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        paths = cert_client.get_cert_file_paths()

        assert "client_cert" in paths
        assert "client_key" in paths
        assert "ca_cert" in paths
        assert paths["client_cert"].endswith("client.pem")
        assert paths["client_key"].endswith("client-key.pem")
        assert paths["ca_cert"].endswith("ca.pem")

    def test_check_cert_files_exist_all_present(self):
        """Test certificate file existence check when all files exist."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('os.path.exists', return_value=True):
            result = cert_client.check_cert_files_exist()
            assert result == True

    def test_check_cert_files_exist_missing_files(self):
        """Test certificate file existence check with missing files."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('os.path.exists', return_value=False):
            result = cert_client.check_cert_files_exist()
            assert result == False

    def test_check_cert_files_exist_partial_files(self):
        """Test certificate file existence check with some files missing."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        def mock_exists(path):
            return "client.pem" in path

        with patch('os.path.exists', side_effect=mock_exists):
            result = cert_client.check_cert_files_exist()
            assert result == False


class TestPrivateCertificateHelpers:
    """Test private certificate helper methods."""

    def test_generate_certificate_serial(self):
        """Test certificate serial generation."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        owner = "akash1test"
        cert_data = b"test_certificate_data"

        serial = cert_client.generate_certificate_serial(owner, cert_data)

        assert len(serial) == 16
        assert isinstance(serial, str)


class TestmTLSIntegrationScenarios:
    """Test complete mTLS integration scenarios."""

    def test_full_mtls_workflow_success(self):
        """Test complete mTLS workflow from certificate generation to SSL context."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('akash.modules.cert.tx.ec') as mock_ec, \
                patch('akash.modules.cert.tx.x509') as mock_x509, \
                patch('akash.modules.cert.tx.serialization') as mock_serialization, \
                patch('akash.modules.cert.tx.hashes'), \
                patch('akash.modules.cert.utils.ssl') as mock_ssl, \
                patch('builtins.open', mock_open()) as mock_file, \
                patch('os.makedirs'), \
                patch('os.path.exists', return_value=True):
            mock_private_key = Mock()
            mock_public_key = Mock()
            mock_private_key.public_key.return_value = mock_public_key
            mock_ec.generate_private_key.return_value = mock_private_key
            mock_ec.SECP256R1.return_value = "SECP256R1"

            mock_cert_builder = Mock()
            mock_cert = Mock()
            mock_cert.serial_number = 123456789
            mock_x509.CertificateBuilder.return_value = mock_cert_builder
            mock_cert_builder.subject_name.return_value = mock_cert_builder
            mock_cert_builder.issuer_name.return_value = mock_cert_builder
            mock_cert_builder.public_key.return_value = mock_cert_builder
            mock_cert_builder.serial_number.return_value = mock_cert_builder
            mock_cert_builder.not_valid_before.return_value = mock_cert_builder
            mock_cert_builder.not_valid_after.return_value = mock_cert_builder
            mock_cert_builder.sign.return_value = mock_cert

            mock_name = Mock()
            mock_x509.Name.return_value = mock_name

            mock_serialization.Encoding.PEM = "PEM"
            mock_serialization.Encoding.DER = "DER"
            mock_serialization.PrivateFormat.PKCS8 = "PKCS8"
            mock_serialization.PublicFormat.SubjectPublicKeyInfo = "SubjectPublicKeyInfo"
            mock_serialization.NoEncryption.return_value = "NoEncryption"

            cert_pem_bytes = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            key_pem_bytes = b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
            pubkey_der_bytes = b"test_public_key_der_data"

            mock_cert.public_bytes.return_value = cert_pem_bytes
            mock_private_key.private_bytes.return_value = key_pem_bytes
            mock_public_key.public_bytes.return_value = pubkey_der_bytes

            with patch.object(cert_client, 'publish_client_certificate') as mock_publish:
                mock_publish.return_value = Mock(success=True, tx_hash="TEST123")

                cert_result = cert_client.create_certificate_for_mtls(mock_wallet)
                assert cert_result["status"] == "success"

                mock_context = Mock()
                mock_ssl.create_default_context.return_value = mock_context

                ssl_result = cert_client.create_ssl_context()
                assert ssl_result["status"] == "success"
                assert ssl_result["ssl_context"] == mock_context

    def test_mtls_workflow_certificate_creation_failure(self):
        """Test mTLS workflow with certificate creation failure."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch.object(cert_client, 'publish_client_certificate', side_effect=Exception("Network error")):
            cert_result = cert_client.create_certificate_for_mtls(mock_wallet)
            assert cert_result["status"] == "error"

    def test_mtls_workflow_ssl_context_failure(self):
        """Test mTLS workflow with SSL context creation failure."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('os.path.exists', return_value=False):
            ssl_result = cert_client.create_ssl_context()
            assert ssl_result["status"] == "error"


class TestmTLSErrorHandling:
    """Test complete error handling for mTLS operations."""

    def test_mtls_certificate_generation_all_errors(self):
        """Test mTLS certificate generation handles all possible errors."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"
        mock_wallet.private_key_bytes = b"test_private_key"

        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        error_scenarios = [
            ("Key generation error", "akash.modules.cert.tx.ec.generate_private_key"),
            ("Certificate builder error", "akash.modules.cert.tx.x509.CertificateBuilder"),
            ("Serialization error", "akash.modules.cert.tx.serialization.Encoding"),
            ("File write error", "builtins.open"),
        ]

        for error_desc, patch_target in error_scenarios:
            with patch(patch_target, side_effect=Exception(error_desc)), \
                    patch.object(cert_client, 'publish_client_certificate') as mock_publish:

                mock_publish.return_value = Mock(success=True, tx_hash="TEST123")
                result = cert_client.create_certificate_for_mtls(mock_wallet)
                assert result["status"] == "error"
                assert "error" in result
                assert len(result["error"]) > 0

    def test_ssl_context_creation_all_errors(self):
        """Test SSL context creation handles all possible errors."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        with patch('os.path.exists', return_value=True), \
                patch('builtins.open', mock_open()), \
                patch('akash.modules.cert.utils.ssl.create_default_context',
                      side_effect=Exception("SSL context creation error")):
            result = cert_client.create_ssl_context()
            assert result["status"] == "error"
            assert "SSL context creation error" in result["error"]

        with patch('os.path.exists', return_value=True), \
                patch('builtins.open', mock_open()), \
                patch('akash.modules.cert.utils.ssl.create_default_context') as mock_ssl_context:
            mock_context = Mock()
            mock_context.load_cert_chain.side_effect = Exception("Certificate load error")
            mock_ssl_context.return_value = mock_context

            result = cert_client.create_ssl_context()
            assert result["status"] == "error"
            assert "Certificate load error" in result["error"]

    def test_certificate_validation_edge_cases(self):
        """Test certificate validation with various edge cases."""
        mock_akash_client = Mock()
        cert_client = CertClient(mock_akash_client)

        edge_cases = [
            None,
            "",
            "   ",
            "-----BEGIN CERTIFICATE-----",  # Missing END
            "-----END CERTIFICATE-----",  # Missing BEGIN
            "-----BEGIN CERTIFICATE-----\n\n-----END CERTIFICATE-----",  # Empty content
            "-----BEGIN CERTIFICATE-----\ninvalid_base64_!@#\n-----END CERTIFICATE-----",  # Invalid base64
        ]

        for case in edge_cases:
            with patch('akash.modules.cert.utils.logger'):
                result = cert_client.validate_ssl_certificate(case)
                assert result == False


if __name__ == '__main__':
    print("Running certificate mTLS module tests")
    print("=" * 70)
    print()
    print("mTLS tests: testing mTLS certificate generation, SSL context creation,")
    print("certificate validation, file management, and gRPC SSL integration.")
    print()
    print("These tests cover certificate functionality for secure provider communication.")
    print()

    pytest.main([__file__, '-v'])
