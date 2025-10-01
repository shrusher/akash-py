import base64
import datetime
import hashlib
import logging
import os
import ssl
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CertUtils:
    """
    Mixin for certificate utilities.
    """

    def __init__(self):
        if not hasattr(self, 'cert_dir'):
            self.cert_dir = "certs"

    def validate_certificate(self, cert_data: Dict) -> bool:
        """
        Validate certificate structure and data.

        Args:
            cert_data: Certificate data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            required_fields = ["serial", "certificate"]

            for field in required_fields:
                if field not in cert_data:
                    logger.error(f"Missing required field: {field}")
                    return False

            cert = cert_data["certificate"]
            cert_required_fields = ["state", "cert", "pubkey"]

            for field in cert_required_fields:
                if field not in cert:
                    logger.error(f"Missing required certificate field: {field}")
                    return False

            valid_states = ["valid", "revoked", "invalid"]
            if cert["state"] not in valid_states:
                logger.error(f"Invalid certificate state: {cert['state']}")
                return False

            try:
                base64.b64decode(cert["cert"])
                base64.b64decode(cert["pubkey"])
            except Exception:
                logger.error("Certificate data must be base64 encoded")
                return False

            if not self._validate_certificate_format(cert["cert"]):
                logger.error("Certificate data is not in valid X.509/PEM format")
                return False

            if not self._validate_public_key_format(cert["pubkey"]):
                logger.error("Public key data is not in valid format")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating certificate: {e}")
            return False

    def _validate_certificate_format(self, cert_b64: str) -> bool:
        """
        Validate that certificate data is in valid X.509/PEM format.

        Args:
            cert_b64: Base64 encoded certificate data

        Returns:
            bool: True if valid format, False otherwise
        """
        try:
            cert_data = base64.b64decode(cert_b64)
            cert_str = cert_data.decode()

            if (
                    "-----BEGIN CERTIFICATE-----" in cert_str
                    and "-----END CERTIFICATE-----" in cert_str
            ):
                return True

            logger.warning("Certificate not in expected PEM format")
            return False

        except Exception as e:
            logger.error(f"Certificate format validation failed: {e}")
            return False

    def _validate_public_key_format(self, pubkey_b64: str) -> bool:
        """
        Validate that public key data is in valid format.

        Args:
            pubkey_b64: Base64 encoded public key data

        Returns:
            bool: True if valid format, False otherwise
        """
        try:
            pubkey_data = base64.b64decode(pubkey_b64)
            pubkey_str = pubkey_data.decode()

            valid_formats = [
                "-----BEGIN PUBLIC KEY-----",
                "-----BEGIN EC PUBLIC KEY-----",
                "-----BEGIN RSA PUBLIC KEY-----",
            ]

            format_valid = any(fmt in pubkey_str for fmt in valid_formats)
            if not format_valid:
                logger.warning("Public key not in expected PEM format")
                return False

            return True

        except Exception as e:
            logger.error(f"Public key format validation failed: {e}")
            return False

    def generate_certificate_serial(self, owner: str, cert_data: bytes) -> str:
        """
        Generate a deterministic serial number for a certificate.

        Args:
            owner: Certificate owner address
            cert_data: Certificate data in bytes

        Returns:
            str: Generated serial number
        """
        try:
            logger.info(f"Generating certificate serial for owner {owner}")
            combined_data = owner.encode() + cert_data
            hash_object = hashlib.sha256(combined_data)
            serial = hash_object.hexdigest()[:16]
            logger.info(f"Generated serial: {serial}")
            return serial
        except Exception as e:
            logger.error(f"Failed to generate certificate serial: {e}")
            return ""

    def verify_certificate_files(self) -> Dict[str, Any]:
        """
        Verify that certificate files exist and are readable.

        Returns:
            Dict with verification status
        """
        try:
            cert_paths = {
                "client_cert": f"{self.cert_dir}/client.pem",
                "client_key": f"{self.cert_dir}/client-key.pem",
                "ca_cert": f"{self.cert_dir}/ca.pem",
            }

            verification = {"status": "success", "files": {}}

            for name, path in cert_paths.items():
                if os.path.exists(path):
                    try:
                        with open(path, "r") as f:
                            content = f.read()
                        verification["files"][name] = {
                            "exists": True,
                            "readable": True,
                            "size": len(content),
                        }
                    except Exception as e:
                        verification["files"][name] = {
                            "exists": True,
                            "readable": False,
                            "error": str(e),
                        }
                        verification["status"] = "partial"
                else:
                    verification["files"][name] = {"exists": False, "readable": False}
                    verification["status"] = "failed"

            logger.info(f"Certificate verification: {verification['status']}")
            return verification

        except Exception as e:
            logger.error(f"Certificate verification failed: {e}")
            return {"status": "error", "error": str(e)}

    def cleanup_certificates(self) -> Dict[str, Any]:
        """
        Clean up locally stored certificate files.

        Returns:
            Dict with cleanup status
        """
        try:
            if not os.path.exists(self.cert_dir):
                return {
                    "status": "success",
                    "message": "No certificate files to clean up",
                }

            cert_files = ["client.pem", "client-key.pem", "ca.pem"]

            cleaned = []
            for cert_file in cert_files:
                file_path = f"{self.cert_dir}/{cert_file}"
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned.append(cert_file)

            try:
                os.rmdir(self.cert_dir)
            except OSError:
                pass

            logger.info(f"Cleaned up {len(cleaned)} certificate files")
            return {
                "status": "success",
                "cleaned_files": cleaned,
                "message": f"Removed {len(cleaned)} certificate files",
            }

        except Exception as e:
            logger.error(f"Certificate cleanup failed: {e}")
            return {"status": "error", "error": str(e)}

    def create_ssl_context(self) -> Dict[str, Any]:
        """
        Create SSL context for mTLS connections.

        Returns:
            Dict with SSL context or error information
        """
        try:
            cert_paths = self.get_cert_file_paths()
            client_cert_path = cert_paths["client_cert"]
            client_key_path = cert_paths["client_key"]
            ca_cert_path = cert_paths["ca_cert"]

            missing_files = []
            for path in [client_cert_path, client_key_path, ca_cert_path]:
                if not os.path.exists(path):
                    missing_files.append(path)

            if missing_files:
                return {
                    "status": "error",
                    "error": f"Certificate files not found: {', '.join(missing_files)}",
                }

            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED

            context.load_cert_chain(client_cert_path, client_key_path)

            context.load_verify_locations(ca_cert_path)

            return {"status": "success", "ssl_context": context}

        except ssl.SSLError as e:
            logger.error(f"SSL context creation failed: {e}")
            return {"status": "error", "error": f"SSL error: {e}"}
        except (IOError, OSError) as e:
            logger.error(f"SSL context creation failed: {e}")
            return {"status": "error", "error": f"File read error: {e}"}
        except Exception as e:
            logger.error(f"SSL context creation failed: {e}")
            return {"status": "error", "error": str(e)}

    def validate_ssl_certificate(self, cert_pem: str) -> bool:
        """
        Validate SSL certificate PEM format.

        Args:
            cert_pem: Certificate in PEM format

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            try:
                if not cert_pem or not isinstance(cert_pem, str):
                    logger.error("Certificate data is empty or invalid")
                    return False
            except TypeError:
                if not cert_pem:
                    logger.error("Certificate data is empty or invalid")
                    return False

            if "-----BEGIN CERTIFICATE-----" not in cert_pem:
                logger.error("Missing BEGIN CERTIFICATE marker")
                return False

            if "-----END CERTIFICATE-----" not in cert_pem:
                logger.error("Missing END CERTIFICATE marker")
                return False

            try:
                x509.load_pem_x509_certificate(cert_pem.encode())
                return True
            except Exception as parse_error:
                logger.error(f"Certificate parsing failed: {parse_error}")
                return False

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def get_cert_file_paths(self) -> Dict[str, str]:
        """
        Get standard certificate file paths.

        Returns:
            Dict with certificate file paths
        """
        return {
            "client_cert": f"{self.cert_dir}/client.pem",
            "client_key": f"{self.cert_dir}/client-key.pem",
            "ca_cert": f"{self.cert_dir}/ca.pem",
        }

    def check_cert_files_exist(self) -> bool:
        """
        Check if certificate files exist.

        Returns:
            bool: True if all certificate files exist, False otherwise
        """
        cert_paths = self.get_cert_file_paths()

        for name, path in cert_paths.items():
            if not os.path.exists(path):
                return False

        return True

    def check_expiry(self, certificate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check certificate expiry status.

        Args:
            certificate: Certificate dictionary from query_certificates or similar

        Returns:
            Dict with expiry information:
                - expired: bool
                - valid_until: datetime string (if parseable)
                - days_remaining: int (if not expired)
                - message: str description
        """
        try:
            import base64
            from datetime import datetime, timezone

            cert_b64 = None
            if isinstance(certificate, dict):
                if (
                        "certificate" in certificate
                        and "cert" in certificate["certificate"]
                ):
                    cert_b64 = certificate["certificate"]["cert"]
                elif "cert" in certificate:
                    cert_b64 = certificate["cert"]

            if not cert_b64:
                return {
                    "expired": False,
                    "valid_until": None,
                    "days_remaining": None,
                    "message": "Unable to extract certificate data",
                }

            try:
                cert_der = base64.b64decode(cert_b64)
                cert_str = cert_der.decode()
                if "-----BEGIN CERTIFICATE-----" in cert_str:
                    cert = x509.load_pem_x509_certificate(cert_str.encode())
                else:
                    cert = x509.load_der_x509_certificate(cert_der)
            except UnicodeDecodeError:
                cert = x509.load_der_x509_certificate(cert_der)

            not_after = cert.not_valid_after_utc
            now = datetime.now(timezone.utc)

            days_remaining = (not_after - now).days

            return {
                "expired": now > not_after,
                "valid_until": not_after.isoformat(),
                "days_remaining": days_remaining if days_remaining > 0 else 0,
                "message": f"Certificate {'expired' if now > not_after else f'valid for {days_remaining} days'}",
            }

        except Exception as e:
            logger.error(f"Failed to check certificate expiry: {e}")
            return {
                "expired": False,
                "valid_until": None,
                "days_remaining": None,
                "message": f"Error checking expiry: {str(e)}",
            }

    def _generate_mtls_certificate(self, wallet, ca_cert_path: Optional[str] = None):
        """
        Private method to generate mTLS certificate.

        Args:
            wallet: Wallet for certificate generation
            ca_cert_path: Optional CA certificate path

        Returns:
            Tuple of (private_key, certificate)
        """
        private_key = ec.generate_private_key(ec.SECP256R1())

        wallet_id = wallet if isinstance(wallet, str) else wallet.address
        subject = issuer = self._create_x509_name(wallet_id)

        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(int(__import__('uuid').uuid4().hex[:16], 16))
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .sign(private_key, hashes.SHA256())
        )

        return (private_key, certificate)

    def _create_x509_name(self, common_name: str) -> Any:
        """
        Create X509 name for certificate subject.

        Args:
            common_name: Common name for certificate

        Returns:
            X509 Name object
        """
        return x509.Name(
            [x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, common_name)]
        )

    def ensure_certificate(self, wallet) -> tuple:
        """
        Ensure certificate exists for mTLS communication.
        Simplifies the certificate creation/loading process.

        Args:
            wallet: AkashWallet instance

        Returns:
            Tuple of (success, cert_pem, key_pem)
        """
        import os
        try:
            if (hasattr(self.akash_client, "_certificate_store") and
                    wallet.address in self.akash_client._certificate_store):
                cert_info = self.akash_client._certificate_store[wallet.address]
                logger.info("Using existing certificate from store")
                return True, cert_info["certificate_pem"], cert_info["private_key_pem"]

            cert_path = os.path.join(self.cert_dir, "client.pem")
            key_path = os.path.join(self.cert_dir, "client-key.pem")

            if os.path.exists(cert_path) and os.path.exists(key_path):
                try:
                    with open(cert_path, 'r') as f:
                        cert_pem = f.read()
                    with open(key_path, 'r') as f:
                        key_pem = f.read()

                    from cryptography import x509
                    from cryptography.hazmat.primitives import serialization
                    import datetime

                    local_cert = x509.load_pem_x509_certificate(cert_pem.encode())
                    local_serial = str(local_cert.serial_number)

                    # Check expiration
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if local_cert.not_valid_after_utc < now:
                        logger.warning(f"Local certificate expired on {local_cert.not_valid_after_utc}")
                        os.remove(cert_path)
                        os.remove(key_path)
                    elif local_cert.not_valid_before_utc > now:
                        logger.warning(f"Local certificate not yet valid (valid from {local_cert.not_valid_before_utc})")
                        os.remove(cert_path)
                        os.remove(key_path)
                    else:
                        chain_cert_response = self.get_certificates(
                            owner=wallet.address,
                            serial=local_serial,
                            state="valid"
                        )

                        found_on_chain = False
                        if chain_cert_response and chain_cert_response.get('certificates'):
                            for chain_cert in chain_cert_response['certificates']:
                                if chain_cert['serial'] == local_serial:
                                    found_on_chain = True

                                    try:
                                        private_key = serialization.load_pem_private_key(
                                            key_pem.encode(),
                                            password=None
                                        )
                                        local_pubkey = local_cert.public_key().public_bytes(
                                            encoding=serialization.Encoding.DER,
                                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                                        )
                                        file_pubkey = private_key.public_key().public_bytes(
                                            encoding=serialization.Encoding.DER,
                                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                                        )

                                        if local_pubkey != file_pubkey:
                                            logger.error("Certificate and private key do not match!")
                                            os.remove(cert_path)
                                            os.remove(key_path)
                                            break

                                        if not hasattr(self.akash_client, "_certificate_store"):
                                            self.akash_client._certificate_store = {}

                                        self.akash_client._certificate_store[wallet.address] = {
                                            "certificate_pem": cert_pem,
                                            "private_key_pem": key_pem,
                                            "cert_path": cert_path,
                                            "key_path": key_path
                                        }

                                        logger.info(f"Using validated certificate (serial: {local_serial})")
                                        return True, cert_pem, key_pem

                                    except Exception as e:
                                        logger.error(f"Private key validation failed: {e}")
                                        os.remove(cert_path)
                                        os.remove(key_path)
                                        break

                        if not found_on_chain:
                            logger.warning(f"Local certificate (serial: {local_serial}) not found on blockchain")
                            os.remove(cert_path)
                            os.remove(key_path)

                except Exception as e:
                    logger.warning(f"Failed to validate local certificate: {e}")
                    try:
                        os.remove(cert_path)
                        os.remove(key_path)
                    except:
                        pass

            logger.info("Creating new certificate for mTLS")
            cert_result = self.create_certificate_for_mtls(wallet)

            if cert_result.get("status") == "success":
                if os.path.exists(cert_path) and os.path.exists(key_path):
                    with open(cert_path, 'r') as f:
                        cert_pem = f.read()
                    with open(key_path, 'r') as f:
                        key_pem = f.read()

                    logger.info("Certificate created successfully")
                    return True, cert_pem, key_pem

            logger.error(f"Certificate creation failed: {cert_result.get('error')}")
            return False, None, None

        except Exception as e:
            logger.error(f"Certificate setup failed: {e}")
            return False, None, None
