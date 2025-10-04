import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ManifestQuery:
    """
    Mixin for manifest query operations.
    """

    def get_deployment_manifest(
        self,
        provider_endpoint: str,
        lease_id: Dict[str, Any],
        cert_pem: str,
        key_pem: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Query deployment manifest from provider's cluster.

        Provider version detection and fallback:
            - Legacy providers (v0.6.x): Standard client cert → mtls. fallback
            - Modern providers (v0.7+): mtls. only
            - Unknown version: mtls. → standard fallback

        Args:
            provider_endpoint: Provider endpoint URL
            lease_id: Lease identifier
                - dseq (str): Deployment sequence
                - gseq (int): Group sequence
                - oseq (int): Order sequence
            cert_pem: Client certificate PEM
            key_pem: Client private key PEM
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Dict with manifest data or error
                - status (str): "success" or "error"
                - provider_version (str): Detected provider version (e.g., "v0.8.3-rc10" or "unknown")
                - method (str): Query method used ("standard", "mtls-socket", "mtls-socket (fallback)", or "standard (fallback)")
                - manifest (List[Dict]): Manifest groups (if success)
                    - name (str): Group name
                    - services (List[Dict]): Services in group
                        - name (str): Service name
                        - image (str): Container image
                        - command (List[str], optional): Command override
                        - args (List[str], optional): Arguments
                        - env (List[str], optional): Environment variables
                        - resources (Dict): Resource requirements
                            - cpu (Dict): CPU allocation
                                - units (Dict): CPU units
                                    - val (str): CPU millicores as string (e.g., "100" for 0.1 CPU)
                            - memory (Dict): Memory allocation
                                - size (Dict): Memory size
                                    - val (str): Memory in bytes as string (e.g., "134217728" for 128Mi)
                            - storage (List[Dict], optional): Storage volumes
                                - name (str): Storage volume name (e.g., "default")
                                - size (Dict): Storage size
                                    - val (str): Storage in bytes as string (e.g., "536870912" for 512Mi)
                            - gpu (Dict, optional): GPU allocation
                                - units (Dict): GPU units
                                    - val (str): Number of GPUs as string
                                - attributes (List[Dict], optional): GPU attributes/requirements
                                    - key (str): Attribute key (e.g., "vendor/nvidia/model/rtx4090")
                        - expose (List[Dict]): Port exposures
                            - port (int): Container port
                            - externalPort (int): External port mapping
                            - proto (str): Protocol (TCP/UDP)
                            - global (bool): Global exposure
                        - params (Dict, optional): Service parameters for storage mounts
                            - storage (List[Dict]): Storage mount configurations
                                - name (str): Storage volume name (must match a storage resource)
                                - mount (str): Container mount path
                                - readOnly (bool): Whether mount is read-only
                        - credentials (Dict, optional): Private container registry credentials
                            - host (str): Registry hostname (e.g., "docker.io", "ghcr.io")
                            - username (str): Registry username
                            - password (str): Registry password/token
                            - email (str): Registry email (optional)
                        - count (int): Number of replicas
                - error (str): Error message (if error)
        """
        logger.info(f"Querying manifest from provider: {provider_endpoint}")

        provider_version = self._detect_provider_version(provider_endpoint)
        if not provider_version:
            logger.warning("Could not detect provider version, trying modern approach")
            provider_version = "unknown"

        is_legacy = self._is_legacy_provider(provider_version)

        dseq = lease_id.get("dseq")
        gseq = lease_id.get("gseq", 1)
        oseq = lease_id.get("oseq", 1)
        path = f"/lease/{dseq}/{gseq}/{oseq}/manifest"

        logger.info(f"Provider version: {provider_version} ({'legacy' if is_legacy else 'modern/unknown'})")
        logger.info(f"Lease ID: dseq={dseq}, gseq={gseq}, oseq={oseq}")

        if is_legacy:
            logger.info("Legacy provider - trying standard client cert auth first")
            result = self._query_manifest_standard(
                provider_endpoint, path, cert_pem, key_pem, timeout
            )

            if result.get("status") == "error" and "401" in result.get("error", ""):
                logger.info("Standard auth failed, trying mtls. approach as fallback")
                result = self._query_manifest_mtls(
                    provider_endpoint, path, cert_pem, key_pem, timeout
                )
                result["method"] = "mtls-socket (fallback)"
            else:
                result["method"] = "standard"
        elif provider_version == "unknown":
            logger.info("Unknown provider version - trying mtls. approach first")
            result = self._query_manifest_mtls(
                provider_endpoint, path, cert_pem, key_pem, timeout
            )

            if result.get("status") == "error":
                logger.info("mtls. approach failed, trying standard client cert as fallback")
                result = self._query_manifest_standard(
                    provider_endpoint, path, cert_pem, key_pem, timeout
                )
                result["method"] = "standard (fallback)"
            else:
                result["method"] = "mtls-socket"
        else:
            logger.info("Modern provider - using mtls. approach")
            result = self._query_manifest_mtls(
                provider_endpoint, path, cert_pem, key_pem, timeout
            )
            result["method"] = "mtls-socket"

        result["provider_version"] = provider_version
        return result

    def _query_manifest_standard(
        self,
        provider_endpoint: str,
        path: str,
        cert_pem: str,
        key_pem: str,
        timeout: int
    ) -> Dict[str, Any]:
        """Query manifest using standard requests library with client cert."""
        try:
            import requests
            import tempfile
            import os

            url = f"{provider_endpoint}{path}"
            logger.debug(f"Standard query to: {url}")

            cert_file = tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False)
            key_file = tempfile.NamedTemporaryFile(mode="w", suffix=".key", delete=False)

            try:
                cert_file.write(cert_pem)
                cert_file.flush()
                key_file.write(key_pem)
                key_file.flush()

                response = requests.get(
                    url,
                    cert=(cert_file.name, key_file.name),
                    timeout=timeout,
                    verify=False
                )

                if response.status_code == 200:
                    manifest_data = response.json()
                    logger.info(f"Successfully retrieved manifest (standard method)")
                    return {
                        "status": "success",
                        "manifest": manifest_data
                    }
                elif response.status_code == 404:
                    logger.warning(f"Lease not found: {url}")
                    return {
                        "status": "error",
                        "error": f"Lease not found on provider (404)"
                    }
                else:
                    logger.warning(f"Standard query failed with status {response.status_code}")
                    return {
                        "status": "error",
                        "error": f"Provider returned status {response.status_code}: {response.text}"
                    }

            finally:
                cert_file.close()
                key_file.close()
                os.unlink(cert_file.name)
                os.unlink(key_file.name)

        except Exception as e:
            logger.warning(f"Standard query failed: {e}")
            return {"status": "error", "error": str(e)}

    def _query_manifest_mtls(
        self,
        provider_endpoint: str,
        path: str,
        cert_pem: str,
        key_pem: str,
        timeout: int
    ) -> Dict[str, Any]:
        """Query manifest using socket-based mTLS with mtls. prefix."""
        try:
            import tempfile
            import os
            import ssl
            import socket
            import json
            from urllib.parse import urlparse

            parsed_uri = urlparse(provider_endpoint)
            hostname = parsed_uri.hostname
            port = parsed_uri.port or 8443

            cert_file = tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False)
            key_file = tempfile.NamedTemporaryFile(mode="w", suffix=".key", delete=False)

            try:
                cert_file.write(cert_pem)
                cert_file.flush()
                key_file.write(key_pem)
                key_file.flush()

                logger.debug(f"Using mtls. prefix: mtls.{hostname}")

                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.load_cert_chain(cert_file.name, key_file.name)

                sock = socket.create_connection((hostname, port), timeout=timeout)
                ssl_sock = ctx.wrap_socket(sock, server_hostname=f"mtls.{hostname}")

                request_str = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {hostname}\r\n"
                    f"Accept: application/json\r\n"
                    f"Connection: close\r\n"
                    f"\r\n"
                )

                logger.debug(f"Sending request to {hostname}:{port}{path}")
                ssl_sock.sendall(request_str.encode())

                response_data = b""
                while True:
                    chunk = ssl_sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk

                ssl_sock.close()

                response_str = response_data.decode('utf-8', errors='ignore')

                if "\r\n\r\n" in response_str:
                    headers_part, body_part = response_str.split("\r\n\r\n", 1)
                else:
                    logger.error("Invalid HTTP response format")
                    return {
                        "status": "error",
                        "error": "Invalid HTTP response format"
                    }

                status_line = headers_part.split("\r\n")[0]
                if "200 OK" in status_line:
                    try:
                        manifest_data = json.loads(body_part)
                        logger.info(f"Successfully retrieved manifest (mtls method)")
                        return {
                            "status": "success",
                            "manifest": manifest_data
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        logger.error(f"Body: {body_part[:500]}")
                        return {
                            "status": "error",
                            "error": f"Failed to parse JSON response: {e}"
                        }
                elif "404" in status_line:
                    logger.warning(f"Lease not found: {hostname}{path}")
                    logger.warning(f"Response: {body_part[:500]}")
                    return {
                        "status": "error",
                        "error": f"Lease not found on provider (404)"
                    }
                else:
                    logger.error(f"Provider returned: {status_line}")
                    logger.error(f"Response body: {body_part[:500]}")
                    return {
                        "status": "error",
                        "error": f"Provider returned: {status_line}. Body: {body_part[:200]}"
                    }

            finally:
                cert_file.close()
                key_file.close()
                os.unlink(cert_file.name)
                os.unlink(key_file.name)

        except Exception as e:
            logger.error(f"mtls query failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}
