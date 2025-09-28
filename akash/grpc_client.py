import grpc
import logging
import requests
import socket
import time
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class LeaseRPCStub:
    def __init__(self, channel):
        from akash.proto.akash.provider.lease.v1.service_pb2_grpc import (
            LeaseRPCStub as ProtobufLeaseRPCStub,
        )

        self._grpc_stub = ProtobufLeaseRPCStub(channel)
        self.channel = channel

    def SendManifest(self, request, timeout=None):
        """Send manifest to provider using gRPC call."""
        return self._grpc_stub.SendManifest(request, timeout=timeout)

    def ServiceStatus(self, request, timeout=None):
        """Get service status from provider using gRPC call."""
        return self._grpc_stub.ServiceStatus(request, timeout=timeout)

    def ServiceLogs(self, request, timeout=None):
        """Get service logs from provider using gRPC call."""
        return self._grpc_stub.ServiceLogs(request, timeout=timeout)

    def StreamServiceLogs(self, request, timeout=None):
        """Stream service logs from provider using gRPC streaming call."""
        return self._grpc_stub.StreamServiceLogs(request, timeout=timeout)


class ProviderRPCStub:
    """Provider RPC stub for off-chain provider status queries."""

    def __init__(self, channel):
        from akash.proto.akash.provider.v1.service_pb2_grpc import (
            ProviderRPCStub as ProtobufProviderRPCStub,
        )

        self._grpc_stub = ProtobufProviderRPCStub(channel)
        self.channel = channel

    def GetStatus(self, request, timeout=None):
        """Get provider status using gRPC call."""
        return self._grpc_stub.GetStatus(request, timeout=timeout)


class ProviderGRPCClient:
    """
    gRPC client for connecting to Akash providers.

    Handles mTLS authentication, connection management, and error handling
    for provider-side operations (manifest, inventory, discovery).
    """

    def __init__(self, akash_client, timeout: int = 30, retries: int = 3):
        """
        Initialize provider gRPC client.

        Args:
            akash_client: Parent AkashClient instance
            timeout: Default timeout for gRPC calls in seconds
            retries: Default number of retries for failed calls
        """
        self.akash_client = akash_client
        self.timeout = timeout
        self.retries = retries
        self.logger = logger
        self._channels: Dict[str, grpc.Channel] = {}
        self._grpc_channel_cache = {}
        self._channel_keepalive_ms = 5 * 60 * 1000  # 5 minutes
        self.logger.info("Initialized ProviderGRPCClient with connection pooling")

    def _create_secure_channel(
        self, endpoint: str, owner: str, use_mtls: bool = True, insecure: bool = False
    ) -> grpc.Channel:
        """
        Create a secure gRPC channel with optional mTLS authentication.

        Args:
            endpoint: Provider endpoint
            owner: Certificate owner for mTLS
            use_mtls: Whether to use mTLS authentication
            insecure: Skip certificate verification

        Returns:
            gRPC Channel object
        """
        try:
            import os

            if insecure:
                import ssl

                try:
                    logger.info(
                        f"Attempting insecure SSL connection via custom context to {endpoint}"
                    )

                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    ssl_context.set_ciphers(
                        "HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA"
                    )

                    os.environ["GRPC_SSL_CIPHER_SUITES"] = "HIGH"

                    import ssl as ssl_module

                    original_create_default_context = ssl_module.create_default_context

                    def patched_create_default_context(*args, **kwargs):
                        import ssl

                        context = original_create_default_context(*args, **kwargs)
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        return context

                    ssl_module.create_default_context = patched_create_default_context

                    try:
                        credentials = grpc.ssl_channel_credentials()
                        options = [
                            ("grpc.ssl_target_name_override", "localhost"),
                            ("grpc.default_authority", "localhost"),
                            ("grpc.so_reuseport", 1),
                        ]

                        channel = grpc.secure_channel(
                            endpoint, credentials, options=options
                        )
                        self._channels[endpoint] = channel
                        logger.info(
                            f"Successfully created insecure SSL channel to {endpoint} via custom context"
                        )
                        return channel
                    finally:
                        ssl_module.create_default_context = (
                            original_create_default_context
                        )

                except Exception as ctx_error:
                    logger.warning(f"Custom SSL context method failed: {ctx_error}")

                try:
                    logger.info(f"Trying original insecure SSL approach to {endpoint}")

                    credentials = grpc.ssl_channel_credentials(root_certificates=None)

                    options = [
                        ("grpc.ssl_target_name_override", "localhost"),
                        ("grpc.default_authority", "localhost"),
                    ]

                    channel = grpc.secure_channel(
                        endpoint, credentials, options=options
                    )
                    self._channels[endpoint] = channel
                    logger.info(
                        f"Using insecure SSL channel to {endpoint} (bypassing certificate validation)"
                    )
                    return channel
                except Exception as fallback_error:
                    logger.warning(
                        f"Original insecure SSL approach also failed: {fallback_error}"
                    )
                    raise fallback_error

            ca_cert_path = "certs/ca.pem"
            ca_cert = None

            if os.path.exists(ca_cert_path):
                with open(ca_cert_path, "rb") as f:
                    ca_cert = f.read()

            client_key = None
            client_cert = None

            if use_mtls:
                cert_paths = {
                    "client_cert": "certs/client.pem",
                    "client_key": "certs/client-key.pem",
                }

                missing_files = []
                for name, path in cert_paths.items():
                    if not os.path.exists(path):
                        missing_files.append(path)

                if missing_files:
                    raise Exception(
                        f"mTLS requested but certificate files not found: {missing_files}"
                    )

                with open(cert_paths["client_cert"], "rb") as f:
                    client_cert = f.read()

                with open(cert_paths["client_key"], "rb") as f:
                    client_key = f.read()

            credentials = grpc.ssl_channel_credentials(
                root_certificates=ca_cert,
                private_key=client_key,
                certificate_chain=client_cert,
            )

            channel = grpc.secure_channel(endpoint, credentials)
            self._channels[endpoint] = channel

            return channel

        except Exception as e:
            if "ssl" in str(type(e)).lower():
                raise Exception(f"SSL error: {e}")
            elif "grpc" in str(type(e)).lower():
                raise Exception(f"Failed to create secure gRPC channel: {e}")
            else:
                raise Exception(f"Failed to create secure gRPC channel: {e}")

    def _get_lease_stub(
        self, endpoint: str, owner: str, use_mtls: bool = True, insecure: bool = True
    ):
        """Get lease service stub."""
        if not endpoint or not endpoint.strip():
            raise Exception("Endpoint cannot be empty")
        if not owner or not owner.strip():
            raise Exception("Owner cannot be empty")
        channel = self._create_secure_channel(endpoint, owner, use_mtls, insecure)
        return LeaseRPCStub(channel)

    def _get_provider_stub(
        self, endpoint: str, owner: str, use_mtls: bool = False, insecure: bool = True
    ) -> ProviderRPCStub:
        """Get provider service stub."""
        if not endpoint or not endpoint.strip():
            raise Exception("Endpoint cannot be empty")
        if not owner or not owner.strip():
            raise Exception("Owner cannot be empty")
        channel = self._create_secure_channel(endpoint, owner, use_mtls, insecure)
        return ProviderRPCStub(channel)

    def call_with_retry(
        self,
        stub_factory: Callable,
        method_name: str,
        request,
        endpoint: str = "localhost:8443",
        owner: str = "test",
        retries: Optional[int] = None,
        timeout: Optional[int] = None,
        use_mtls: bool = True,
        insecure: bool = True,
    ) -> Dict[str, Any]:
        """
        Call a gRPC method with retry logic.

        Args:
            stub_factory: Function that creates a gRPC stub
            method_name: Name of the method to call on the stub
            request: Request object to pass to the method
            endpoint: gRPC endpoint
            owner: Certificate owner for mTLS
            retries: Number of retries (override default)
            timeout: Timeout override
            use_mtls: Whether to use mTLS
            insecure: Skip certificate verification (default: True)

        Returns:
            Dict with status and response
        """
        actual_timeout = timeout or self.timeout
        actual_retries = retries or self.retries
        last_exception = None

        for attempt in range(actual_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{actual_retries}")
                    time.sleep(min(2**attempt, 10))  # Exponential backoff

                start_time = time.time()
                stub = stub_factory(endpoint, owner, use_mtls, insecure)
                method = getattr(stub, method_name)
                result = method(request, timeout=actual_timeout)
                end_time = time.time()

                call_duration = (
                    end_time - start_time
                ) * 1000  # Convert to milliseconds
                logger.debug(
                    f"gRPC call {method_name} completed in {call_duration:.2f}ms"
                )

                if attempt > 0:
                    logger.info(f"Call succeeded on attempt {attempt + 1}")

                return {
                    "status": "success",
                    "response": result,
                    "attempts": attempt + 1,
                }

            except grpc.RpcError as e:
                last_exception = e

                error_code = None
                error_details = str(e)

                if hasattr(e, "code"):
                    if callable(e.code):
                        error_code = e.code()
                    else:
                        error_code = e.code

                if hasattr(e, "details") and callable(e.details):
                    error_details = e.details()

                if error_code:
                    formatted_error = f"gRPC {error_code.name}: {error_details}"
                else:
                    formatted_error = f"gRPC error: {error_details}"

                last_exception = Exception(formatted_error)

                logger.warning(
                    f"gRPC error on attempt {attempt + 1}: {formatted_error}"
                )

                if error_code and error_code in [
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                ]:
                    if attempt < actual_retries:
                        continue

                break

            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < actual_retries:
                    continue
                break

        logger.error(f"All {actual_retries + 1} attempts failed")
        return {
            "status": "error",
            "error": (
                str(last_exception) if last_exception else "All retry attempts failed"
            ),
            "attempts": actual_retries + 1,
        }

    def get_provider_status(
        self,
        provider_address: str,
        retries: Optional[int] = None,
        timeout: Optional[int] = None,
        insecure: bool = True,
        check_version: bool = True,
    ) -> Dict[str, Any]:
        """
        Get provider status information via gRPC or REST API.

        Protocol selection:
        1. Checks provider version via REST /version endpoint if check_version=True
        2. Uses gRPC for providers version >= 0.5.0
        3. Falls back to REST /status endpoint for older providers
        4. Bypasses SSL certificate validation for all connections

        Args:
            provider_address: Provider's address on blockchain
            retries: Number of retries (override default)
            timeout: Timeout override in seconds
            insecure: Must be True (only insecure connections are supported)
            check_version: Enable version checking for protocol selection

        Returns:
            Dict with status and response or error details
        """
        if not insecure:
            self.logger.warning("Only insecure=True is supported")
            return {
                "status": "error",
                "error": "Only insecure connections are supported",
                "attempts": 0,
            }

        if check_version:
            version_info = self.get_provider_version(
                provider_address, timeout=(timeout or 5) * 1000
            )

            if version_info and version_info.get("akash_version"):
                akash_version = version_info["akash_version"]
                self.logger.info(
                    f"Provider {provider_address[:20]}... version {akash_version}"
                )

                try:
                    from packaging import version as pkg_version

                    if pkg_version.parse(akash_version) < pkg_version.parse("0.5.0"):
                        self.logger.info(
                            f"Using REST API for provider {provider_address[:20]}... (version {akash_version})"
                        )
                        return self.get_provider_status_rest(
                            provider_address, timeout=(timeout or 10) * 1000
                        )
                except Exception as e:
                    self.logger.warning(f"Version comparison failed: {e}, using gRPC")
            else:
                self.logger.debug(
                    f"Version unavailable for provider {provider_address[:20]}..., using gRPC"
                )

        try:
            import asyncio

            endpoint = self.akash_client.get_provider_endpoint(provider_address)

            # Validate DNS
            hostname = endpoint.split(":")[0] if ":" in endpoint else endpoint
            if hostname.startswith("https://"):
                hostname = hostname.replace("https://", "")
            if hostname.startswith("http://"):
                hostname = hostname.replace("http://", "")
            if (
                hostname.endswith(".test")
                or hostname.endswith(".local")
                or not hostname
                or hostname.startswith("$")
            ):
                return {
                    "status": "error",
                    "error": f"Invalid domain: {hostname}",
                    "attempts": 0,
                }

            try:
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(2)
                socket.gethostbyname(hostname)
                self.logger.debug(f"DNS resolution successful for {hostname}")
                socket.setdefaulttimeout(original_timeout)
            except socket.error as e:
                socket.setdefaulttimeout(original_timeout)
                return {
                    "status": "error",
                    "error": f"DNS resolution failed for {hostname}: {e}",
                    "attempts": 0,
                }

            if ":8443" in endpoint:
                ports_to_try = [8443, 8444]
                base_endpoint = endpoint.replace(":8443", "")
            elif ":8444" in endpoint:
                ports_to_try = [8444, 8443]
                base_endpoint = endpoint.replace(":8444", "")
            else:
                ports_to_try = [8443, 8444]
                base_endpoint = endpoint

            last_error = None
            for port in ports_to_try:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    result = sock.connect_ex((hostname, port))
                    sock.close()

                    if result == 0:  # Open
                        test_endpoint = (
                            f"{base_endpoint}:{port}"
                            if base_endpoint
                            else f"{hostname}:{port}"
                        )
                        self.logger.info(
                            f"Found open port {port} on {hostname}, trying gRPC on {test_endpoint}"
                        )

                        grpc_result = asyncio.run(
                            self._get_provider_status_async(
                                test_endpoint, retries, timeout
                            )
                        )

                        if grpc_result.get("status") == "success":
                            self.logger.info(
                                f"Successful gRPC connection on port {port}"
                            )
                            return grpc_result
                        else:
                            last_error = grpc_result.get("error", "gRPC call failed")
                            self.logger.debug(
                                f"gRPC failed on port {port}: {last_error}"
                            )
                    else:
                        self.logger.debug(f"Port {port} not reachable on {hostname}")

                except Exception as e:
                    last_error = f"Port {port} test failed: {e}"
                    self.logger.debug(last_error)
                    continue

            return {
                "status": "error",
                "error": f"No working gRPC ports found on {hostname}. Last error: {last_error}",
                "attempts": len(ports_to_try),
            }

        except ImportError as e:
            return {
                "status": "error",
                "error": f"Missing dependency: {e}",
                "attempts": 0,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to query provider status for {provider_address}: {e}",
                "attempts": 0,
            }

    async def _get_provider_status_async(
        self, endpoint: str, retries: Optional[int], timeout: Optional[int]
    ) -> Dict[str, Any]:
        """Async implementation of provider status query using grpclib."""
        import asyncio
        import ssl
        from grpclib.client import Channel
        from grpclib.exceptions import GRPCError
        from akash.proto.akash.provider.v1.status_pb2 import Status
        from google.protobuf.empty_pb2 import Empty
        from google.protobuf.json_format import MessageToDict

        actual_timeout = timeout or self.timeout
        actual_retries = retries or self.retries
        last_error = None
        host, port = endpoint.rsplit(":", 1) if ":" in endpoint else (endpoint, 8444)
        port = int(port)

        for attempt in range(actual_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{actual_retries}")
                    await asyncio.sleep(min(2**attempt, 10))

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                channel = Channel(host=host, port=port, ssl=ssl_context)

                try:
                    self.logger.info(f"Created grpclib channel to {endpoint}")

                    from grpclib.client import UnaryUnaryMethod

                    method = UnaryUnaryMethod(
                        channel,
                        "/akash.provider.v1.ProviderRPC/GetStatus",
                        Empty,
                        Status,
                    )

                    response = await method(Empty(), timeout=actual_timeout)

                    try:
                        status_dict = MessageToDict(
                            response,
                            preserving_proto_field_name=True,
                            always_print_fields_with_no_presence=True,
                        )
                    except TypeError:
                        # Older protobuf
                        status_dict = MessageToDict(
                            response,
                            preserving_proto_field_name=True,
                            including_default_value_fields=True,
                        )
                    self.logger.info(
                        f"Successfully retrieved provider status from {endpoint}"
                    )
                    return {
                        "status": "success",
                        "response": status_dict,
                        "attempts": attempt + 1,
                    }

                finally:
                    channel.close()

            except GRPCError as e:
                last_error = f"gRPC error: {e}"
                self.logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                if attempt < actual_retries:
                    continue
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                self.logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                if attempt < actual_retries:
                    continue

        return {
            "status": "error",
            "error": f"All {actual_retries + 1} attempts failed: {last_error}",
            "attempts": actual_retries + 1,
        }

    def get_provider_version(
        self, provider_address: str, timeout: int = 5000
    ) -> Optional[Dict[str, str]]:
        """
        Get provider version information from REST endpoint.

        Args:
            provider_address: Provider's address on blockchain
            timeout: Timeout in milliseconds

        Returns:
            Dict with akash version and cosmos SDK version, or None if failed
        """
        try:
            host_uri = self.akash_client.get_provider_endpoint(provider_address)

            response = requests.get(
                f"{host_uri}/version",
                timeout=timeout / 1000,  # Seconds
                verify=False,  # Skip SSL verification
            )

            if response.status_code == 200:
                data = response.json()
                akash_data = data.get("akash", {})

                cosmos_sdk_ver = akash_data.get("cosmosSdkVersion") or akash_data.get(
                    "cosmos_sdk_version"
                )

                return {
                    "akash_version": akash_data.get("version"),
                    "cosmos_sdk_version": cosmos_sdk_ver,
                }

        except Exception as e:
            self.logger.debug(f"Failed to get provider version: {e}")

        return None

    def get_provider_status_rest(
        self, provider_address: str, timeout: int = 10000
    ) -> Dict[str, Any]:
        """
        Get provider status via REST API (for older providers < v0.5.0).

        Args:
            provider_address: Provider's address on blockchain
            timeout: Timeout in milliseconds

        Returns:
            Dict with status information or error
        """
        try:
            host_uri = self.akash_client.get_provider_endpoint(provider_address)

            response = requests.get(
                f"{host_uri}/status",
                timeout=timeout / 1000,  # Seconds
                verify=False,  # Skip SSL verification
            )

            if response.status_code == 200:
                data = response.json()

                return {
                    "status": "success",
                    "response": data,
                    "attempts": 1,
                    "method": "REST",
                }
            else:
                return {
                    "status": "error",
                    "error": f"REST status request failed with status {response.status_code}",
                    "attempts": 1,
                }

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": f"REST request timeout after {timeout}ms",
                "attempts": 1,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"REST status request failed: {e}",
                "attempts": 1,
            }

    def cleanup_connections(self):
        """Clean up all gRPC connections."""
        try:
            closed_count = len(self._channels)
            for endpoint, channel in self._channels.items():
                try:
                    channel.close()
                    logger.info(f"Closed channel to {endpoint}")
                except Exception as e:
                    logger.error(f"Error closing channel to {endpoint}: {e}")

            self._channels.clear()
            return {"status": "success", "closed_channels": closed_count}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_connections()
