import logging
from typing import Any, Dict

from ..auth.utils import validate_address

logger = logging.getLogger(__name__)


class DiscoveryUtils:
    """Utility methods for discovery operations."""

    def get_provider_status(
            self, provider_uri: str, use_https: bool = True
    ) -> Dict[str, Any]:
        """
        Get provider status using GRPC-first then HTTP fallback approach.

        Args:
            provider_uri: Provider's URI or blockchain address (e.g., 'provider.akash.network:8443' or 'akash1provider...')
            use_https: Whether to prefer HTTPS (default: True)

        Returns:
            Dict with provider status information
        """
        try:
            if not provider_uri or provider_uri.strip() == "":
                return {
                    "status": "failed",
                    "error": "Endpoint cannot be empty",
                    "provider": provider_uri,
                }

            logger.info(
                f"Getting provider status from {provider_uri} using GRPC-first approach"
            )

            if validate_address(provider_uri):
                logger.info(f"Valid blockchain address detected: {provider_uri}")
                grpc_result = self.grpc_client.get_provider_status(
                    provider_address=provider_uri, insecure=True, check_version=True
                )

                if grpc_result.get("status") == "success":
                    logger.info(
                        f"Successfully retrieved provider status via GRPC from {provider_uri}"
                    )
                    return self._format_grpc_response(grpc_result, provider_uri)
                else:
                    logger.warning(
                        f"GRPC failed for {provider_uri}: {grpc_result.get('error', 'Unknown error')}"
                    )

                    logger.info(f"Falling back to direct HTTP for {provider_uri}")
                    return self._http_fallback_status(provider_uri, use_https)
            else:
                logger.info(f"Direct endpoint URI detected: {provider_uri}")
                return self._test_direct_endpoint(provider_uri, use_https)

        except Exception as e:
            logger.error(f"Failed to get provider status: {e}")
            return {"status": "failed", "error": str(e), "provider": provider_uri}

    def get_providers_status(
            self, provider_uris: list[str], use_https: bool = True
    ) -> Dict[str, Any]:
        """
        Get status information for multiple providers.

        Args:
            provider_uris: List of provider URIs to check
            use_https: Whether to use HTTPS for connections

        Returns:
            Dict with status check results for all providers
        """
        try:
            logger.info(f"Checking status for {len(provider_uris)} providers")

            discovery_results = {
                "total_providers": len(provider_uris),
                "successful_connections": 0,
                "failed_connections": 0,
                "providers": {},
                "summary": {
                    "total_resources": {"cpu": 0, "memory": 0, "storage": 0, "gpu": 0},
                    "total_leases": 0,
                    "online_providers": 0,
                },
            }

            for provider_uri in provider_uris:
                try:
                    status_result = self.get_provider_status(provider_uri, use_https)

                    if status_result["status"] == "success":
                        discovery_results["successful_connections"] += 1
                        discovery_results["providers"][provider_uri] = {
                            "endpoint": provider_uri,
                            "status": status_result["provider_status"],
                            "accessible": True,
                        }

                        provider_status = status_result["provider_status"]
                        cluster_inventory = (
                            provider_status.get("cluster", {})
                            .get("inventory", {})
                            .get("cluster", {})
                        )

                        if cluster_inventory:
                            cpu_val = cluster_inventory.get("cpu", {})
                            if isinstance(cpu_val, dict) and "val" in cpu_val:
                                discovery_results["summary"]["total_resources"][
                                    "cpu"
                                ] += (int(cpu_val["val"]) if cpu_val["val"] else 0)

                            memory_val = cluster_inventory.get("memory", {})
                            if isinstance(memory_val, dict) and "val" in memory_val:
                                discovery_results["summary"]["total_resources"][
                                    "memory"
                                ] += (
                                    int(memory_val["val"]) if memory_val["val"] else 0
                                )

                            gpu_val = cluster_inventory.get("gpu", {})
                            if isinstance(gpu_val, dict) and "val" in gpu_val:
                                discovery_results["summary"]["total_resources"][
                                    "gpu"
                                ] += (int(gpu_val["val"]) if gpu_val["val"] else 0)

                        if (
                                provider_status.get("cluster", {})
                                        .get("leases", {})
                                        .get("active")
                        ):
                            discovery_results["summary"][
                                "total_leases"
                            ] += provider_status["cluster"]["leases"]["active"]

                        discovery_results["summary"]["online_providers"] += 1

                    else:
                        discovery_results["failed_connections"] += 1
                        discovery_results["providers"][provider_uri] = {
                            "endpoint": provider_uri,
                            "error": status_result.get("error", "Unknown error"),
                            "accessible": False,
                        }

                except Exception as e:
                    discovery_results["failed_connections"] += 1
                    discovery_results["providers"][provider_uri] = {
                        "error": f"Discovery failed: {e}",
                        "accessible": False,
                    }

            logger.info(
                f"Provider discovery complete: {discovery_results['successful_connections']}/{discovery_results['total_providers']} providers accessible"
            )
            return {"status": "success", "discovery_results": discovery_results}

        except Exception as e:
            logger.error(f"Provider discovery failed: {e}")
            return {"status": "failed", "error": str(e)}

    def get_provider_capabilities(
            self, provider_uri: str, use_https: bool = True
    ) -> Dict[str, Any]:
        """
        Get provider capabilities and inventory via gRPC-first with HTTP fallback.

        Args:
            provider_uri: Provider's URI
            use_https: Whether to use HTTPS for HTTP fallback

        Returns:
            Dict with provider capabilities
        """
        try:
            logger.info(f"Getting provider capabilities from {provider_uri}")

            status_result = self.get_provider_status(provider_uri, use_https)

            if status_result["status"] == "success":
                provider_status = status_result["provider_status"]
                cluster_inventory = (
                    provider_status.get("cluster", {})
                    .get("inventory", {})
                    .get("cluster", {})
                )

                capabilities = {
                    "storage": cluster_inventory.get("ephemeral_storage", {}),
                    "cpu": cluster_inventory.get("cpu", {}),
                    "memory": cluster_inventory.get("memory", {}),
                    "gpu": cluster_inventory.get("gpu", {}),
                }

                return {"status": "success", "capabilities": capabilities}
            else:
                return status_result

        except Exception as e:
            logger.error(f"Failed to get provider capabilities: {e}")
            return {"status": "failed", "error": str(e)}

    def get_provider_resources(
            self, provider_uri: str, use_https: bool = True
    ) -> Dict[str, Any]:
        """
        Get provider resource availability via gRPC-first with HTTP fallback.

        Args:
            provider_uri: Provider's URI
            use_https: Whether to use HTTPS

        Returns:
            Dict with provider resources
        """
        try:
            logger.info(f"Getting provider resources from {provider_uri}")

            status_result = self.get_provider_status(provider_uri, use_https)

            if status_result["status"] == "success":
                provider_status = status_result["provider_status"]
                cluster_data = (
                    provider_status.get("cluster", {})
                    .get("inventory", {})
                    .get("cluster", {})
                )
                reservations = (
                    provider_status.get("cluster", {})
                    .get("inventory", {})
                    .get("reservations", {})
                )

                available_resources = {"cpu": 0, "memory": 0, "ephemeral_storage": 0, "gpu": 0}

                # Try nodes format first
                nodes = cluster_data.get("nodes", [])
                if nodes:
                    for node in nodes:
                        node_resources = node.get("resources", {})
                        for resource_type in available_resources.keys():
                            resource_info = node_resources.get(resource_type, {})

                            allocatable = None
                            if "quantity" in resource_info:
                                allocatable = resource_info.get("quantity", {}).get("allocatable", {})
                            else:
                                allocatable = resource_info.get("allocatable", {})

                            if isinstance(allocatable, dict) and "string" in allocatable:
                                try:
                                    value_str = allocatable["string"]
                                    if resource_type == "cpu" and value_str.endswith("m"):
                                        value = int(value_str[:-1])
                                    else:
                                        value = int(value_str)
                                    available_resources[resource_type] += value
                                except (ValueError, TypeError):
                                    pass
                else:
                    for resource_type in available_resources.keys():
                        resource_info = cluster_data.get(resource_type, {})
                        if isinstance(resource_info, dict) and "val" in resource_info:
                            try:
                                available_resources[resource_type] = resource_info["val"]
                            except (ValueError, TypeError):
                                pass

                pending_resources = {"cpu": 0, "memory": 0, "ephemeral_storage": 0, "gpu": 0}
                if reservations.get("pending", {}).get("resources"):
                    pending_res = reservations["pending"]["resources"]
                    for resource_type in pending_resources.keys():
                        resource_data = pending_res.get(resource_type, {})
                        if isinstance(resource_data, dict):
                            if "val" in resource_data:
                                try:
                                    pending_resources[resource_type] = resource_data["val"]
                                except (ValueError, TypeError):
                                    pass
                            elif "string" in resource_data:
                                try:
                                    value_str = resource_data["string"]
                                    if resource_type == "cpu" and value_str.endswith("m"):
                                        pending_resources[resource_type] = int(value_str[:-1])
                                    else:
                                        pending_resources[resource_type] = int(value_str)
                                except (ValueError, TypeError):
                                    pass

                resources = {
                    "available": available_resources,
                    "pending": pending_resources,
                }

                return {"status": "success", "resources": resources}
            else:
                return status_result

        except Exception as e:
            logger.error(f"Failed to get provider resources: {e}")
            return {"status": "failed", "error": str(e)}

    def get_provider_capacity(
            self,
            provider_uri: str,
            required_resources: Dict[str, Any],
            use_https: bool = True,
    ) -> Dict[str, Any]:
        """
        Check if provider has sufficient capacity for required resources via gRPC-first with HTTP fallback.

        Args:
            provider_uri: Provider's URI
            required_resources: Dict of required resources (cpu, memory, storage)
            use_https: Whether to use HTTPS for HTTP fallback

        Returns:
            Dict with capacity check results
        """
        try:
            logger.info(f"Checking provider capacity for {provider_uri}")

            resources_result = self.get_provider_resources(provider_uri, use_https)

            if resources_result["status"] == "success":
                available = resources_result["resources"]["available"]

                sufficient = {}
                has_capacity = True

                for resource_type, required_value in required_resources.items():
                    lookup_key = "ephemeral_storage" if resource_type == "storage" else resource_type
                    available_value = available.get(lookup_key, 0)

                    if isinstance(available_value, dict):
                        available_value = available_value.get("val", 0)

                    if resource_type == "cpu":
                        if isinstance(available_value, str):
                            try:
                                available_int = int(available_value.rstrip("m"))
                                required_int = int(str(required_value).rstrip("m"))
                                sufficient[resource_type] = (
                                        available_int >= required_int
                                )
                            except BaseException:
                                sufficient[resource_type] = False
                        else:
                            try:
                                available_millicores = int(available_value) * 1000
                                required_str = str(required_value)

                                if required_str.endswith("m"):
                                    required_millicores = int(required_str[:-1])
                                else:
                                    required_millicores = int(required_str) * 1000

                                sufficient[resource_type] = (
                                        available_millicores >= required_millicores
                                )
                            except (ValueError, TypeError):
                                sufficient[resource_type] = False
                    elif resource_type in ["memory", "ephemeral_storage", "storage"]:

                        def parse_bytes(value):
                            if isinstance(value, str):
                                if value.endswith("Gi"):
                                    return int(float(value[:-2]) * 1024 * 1024 * 1024)
                                elif value.endswith("Mi"):
                                    return int(float(value[:-2]) * 1024 * 1024)
                                elif value.endswith("Ki"):
                                    return int(float(value[:-2]) * 1024)
                            try:
                                return int(value) if value else 0
                            except (ValueError, TypeError):
                                return 0

                        try:
                            available_bytes = parse_bytes(available_value)
                            required_bytes = parse_bytes(required_value)
                            sufficient[resource_type] = (
                                    available_bytes >= required_bytes
                            )
                        except BaseException:
                            sufficient[resource_type] = False
                    else:
                        try:
                            sufficient[resource_type] = int(available_value or 0) >= int(
                                required_value or 0
                            )
                        except (ValueError, TypeError):
                            sufficient[resource_type] = False

                    if not sufficient[resource_type]:
                        has_capacity = False

                return {
                    "status": "success",
                    "has_capacity": has_capacity,
                    "sufficient": sufficient,
                }
            else:
                return resources_result

        except Exception as e:
            logger.error(f"Failed to check provider capacity: {e}")
            return {"status": "failed", "error": str(e)}

    def _parse_cluster_status(self, response) -> Dict[str, Any]:
        """Parse cluster status from gRPC response."""
        if not hasattr(response, "cluster") or not response.cluster:
            return {}

        cluster = response.cluster

        return {
            "nodes": {
                "available_cpu": (
                    getattr(cluster, "available_cpu", 0)
                    if hasattr(cluster, "available_cpu")
                    else 0
                ),
                "available_memory": (
                    getattr(cluster, "available_memory", "")
                    if hasattr(cluster, "available_memory")
                    else ""
                ),
                "available_storage": (
                    getattr(cluster, "available_storage", "")
                    if hasattr(cluster, "available_storage")
                    else ""
                ),
            },
            "public_hostname": (
                getattr(cluster, "public_hostname", "")
                if hasattr(cluster, "public_hostname")
                else ""
            ),
            "leases": {
                "active": (
                    getattr(cluster.leases, "active", 0)
                    if hasattr(cluster, "leases")
                    else 0
                ),
                "total": (
                    getattr(cluster.leases, "total", 0)
                    if hasattr(cluster, "leases")
                    else 0
                ),
            },
        }

    def _parse_inventory_response(self, inventory) -> Dict[str, Any]:
        """Parse inventory from gRPC response."""
        result = {
            "cpu": {"quantity": 0},
            "memory": {"quantity": ""},
            "storage": [],
            "gpu": [],
        }

        if hasattr(inventory, "cpu") and inventory.cpu:
            result["cpu"]["quantity"] = getattr(inventory.cpu.quantity, "value", 0)

        if hasattr(inventory, "memory") and inventory.memory:
            result["memory"]["quantity"] = getattr(
                inventory.memory.quantity, "value", ""
            )

        if hasattr(inventory, "storage") and inventory.storage:
            for storage in inventory.storage:
                result["storage"].append(
                    {
                        "class": getattr(storage, "class_", ""),
                        "quantity": getattr(storage.quantity, "value", ""),
                    }
                )

        if hasattr(inventory, "gpu") and inventory.gpu:
            for gpu in inventory.gpu:
                result["gpu"].append(
                    {
                        "vendor": getattr(gpu, "vendor", ""),
                        "model": getattr(gpu, "model", ""),
                        "quantity": getattr(gpu.quantity, "value", 0),
                    }
                )

        return result

    def _format_discovery_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format discovery results for client consumption."""
        total_providers = len(raw_results)
        accessible_count = sum(
            1 for p in raw_results.values() if p.get("accessible", False)
        )
        discovery_percentage = (
            (accessible_count / total_providers * 100) if total_providers > 0 else 0.0
        )

        return {
            "total_providers": total_providers,
            "discovery_percentage": discovery_percentage,
            "providers": raw_results,
        }

    def _aggregate_inventory_resources(
            self, inventory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate resources from inventory data."""
        if not inventory_data:
            return {"cpu": 0, "memory": 0, "storage": 0, "gpu": 0}

        active_resources = inventory_data.get("active", [])
        if not active_resources:
            return {"cpu": 0, "memory": 0, "storage": 0, "gpu": 0}

        total_cpu = 0
        total_memory = 0
        total_storage = 0
        total_gpu = 0

        for resource in active_resources:
            total_cpu += resource.get("cpu", 0)
            total_memory += resource.get("memory", 0)
            total_storage += resource.get("storage_ephemeral", 0)
            total_gpu += resource.get("gpu", 0)

        return {
            "cpu": total_cpu,
            "memory": total_memory,
            "storage": total_storage,
            "gpu": total_gpu,
        }

    def _format_grpc_response(
            self, grpc_result: Dict[str, Any], provider_uri: str
    ) -> Dict[str, Any]:
        """Format GRPC response to match discovery client expected format."""
        try:
            response_data = grpc_result.get("response", {})
            cluster_data = response_data.get("cluster", {})
            inventory_data = cluster_data.get("inventory", {})

            provider_status = {
                "provider": provider_uri,
                "cluster": {
                    "leases": {"active": cluster_data.get("leases", 0)},
                    "inventory": inventory_data,
                    "resources": self._aggregate_inventory_resources(inventory_data),
                },
                "bid_engine": response_data.get("bid_engine", {}),
                "manifest": response_data.get("manifest", {}),
                "errors": response_data.get("errors", []),
                "timestamp": response_data.get("timestamp", ""),
                "public_hostnames": response_data.get("public_hostnames", []),
                "status": "online",
                "method": "GRPC",
            }

            return {"status": "success", "provider_status": provider_status}

        except Exception as e:
            logger.error(f"Failed to format GRPC response: {e}")
            return {
                "status": "failed",
                "error": f"GRPC response formatting failed: {e}",
                "provider": provider_uri,
            }

    def _http_fallback_status(
            self, provider_uri: str, use_https: bool = True
    ) -> Dict[str, Any]:
        """Fallback HTTP method when GRPC fails."""
        try:
            logger.info(f"Using HTTP fallback for {provider_uri}")

            if "://" not in provider_uri:
                protocol = "https" if use_https else "http"
                if ":" in provider_uri and not provider_uri.startswith("http"):
                    host, port = provider_uri.rsplit(":", 1)
                    if port.isdigit():
                        status_url = f"{protocol}://{host}:{port}/status"
                    else:
                        status_url = f"{protocol}://{provider_uri}/status"
                else:
                    status_url = f"{protocol}://{provider_uri}/status"
            else:
                if provider_uri.endswith("/"):
                    status_url = f"{provider_uri}status"
                else:
                    status_url = f"{provider_uri}/status"

            logger.info(f"Fetching provider status from fallback URL: {status_url}")

            import requests
            import urllib3

            attempts = []
            if status_url.startswith("https://"):
                attempts = [
                    ("HTTPS (verified)", status_url, True),
                    ("HTTPS (insecure)", status_url, False),
                    (
                        "HTTP (fallback)",
                        status_url.replace("https://", "http://"),
                        False,
                    ),
                ]
            else:
                attempts = [("HTTP", status_url, False)]

            last_error = None

            for attempt_name, url, verify_ssl in attempts:
                try:
                    logger.debug(f"Trying {attempt_name}: {url}")

                    if not verify_ssl and url.startswith("https://"):
                        urllib3.disable_warnings(
                            urllib3.exceptions.InsecureRequestWarning
                        )

                    response = requests.get(url, timeout=10, verify=verify_ssl)
                    response.raise_for_status()

                    status_data = response.json()

                    cluster_data = status_data.get("cluster", {})

                    provider_status = {
                        "provider": provider_uri,
                        "cluster": {
                            "leases": cluster_data.get("leases", {}),
                            "inventory": cluster_data.get("inventory", {}),
                            "resources": self._aggregate_inventory_resources(
                                cluster_data.get("inventory", {})
                            ),
                        },
                        "bid_engine": status_data.get("bid_engine", {}),
                        "manifest": status_data.get("manifest", {}),
                        "errors": status_data.get("errors", []),
                        "timestamp": status_data.get("timestamp", ""),
                        "public_hostnames": status_data.get("public_hostnames", []),
                        "status": "online",
                        "method": f"HTTP ({attempt_name})",
                    }

                    logger.info(
                        f"Successfully retrieved provider status via {attempt_name} from {provider_uri}"
                    )
                    return {"status": "success", "provider_status": provider_status}

                except requests.exceptions.SSLError as e:
                    last_error = f"SSL Error with {attempt_name}: {str(e)}"
                    logger.debug(f"SSL error for {attempt_name}, trying next method...")
                    continue
                except requests.exceptions.RequestException as e:
                    last_error = f"Request failed for {attempt_name}: {str(e)}"
                    logger.debug(
                        f"Request error for {attempt_name}, trying next method..."
                    )
                    continue

            return {
                "status": "failed",
                "error": f"All HTTP methods failed. Last error: {last_error}",
                "provider": provider_uri,
            }

        except Exception as e:
            logger.error(f"HTTP fallback failed: {e}")
            return {
                "status": "failed",
                "error": f"HTTP fallback failed: {e}",
                "provider": provider_uri,
            }

    def _test_direct_endpoint(
            self, provider_uri: str, use_https: bool = True
    ) -> Dict[str, Any]:
        """Test direct endpoint with GRPC-first, then HTTP fallback approach."""
        try:
            logger.info(f"Testing direct endpoint: {provider_uri}")

            if provider_uri.startswith("https://"):
                hostname = provider_uri.replace("https://", "").split(":")[0]
                original_port = "8443"
                if ":" in provider_uri.replace("https://", ""):
                    original_port = provider_uri.split(":")[-1]

                grpc_ports = [
                    original_port,
                    "8444" if original_port != "8444" else "8443",
                ]

                for port in grpc_ports:
                    try:
                        endpoint = f"{hostname}:{port}"
                        logger.info(f"Trying GRPC on {endpoint}")

                        import asyncio

                        grpc_result = asyncio.run(
                            self.grpc_client._get_provider_status_async(
                                endpoint, retries=1, timeout=5
                            )
                        )

                        if grpc_result.get("status") == "success":
                            logger.info(f"✅ GRPC connection successful on {endpoint}")
                            return self._format_grpc_response(grpc_result, provider_uri)

                    except Exception as e:
                        logger.debug(f"GRPC failed on {endpoint}: {e}")
                        continue

                logger.info(f"GRPC failed, falling back to HTTP for {provider_uri}")

            return self._http_fallback_status(provider_uri, use_https)

        except Exception as e:
            logger.error(f"Direct endpoint test failed: {e}")
            return {
                "status": "failed",
                "error": f"Direct endpoint test failed: {e}",
                "provider": provider_uri,
            }
