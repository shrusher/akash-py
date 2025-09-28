import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InventoryQuery:
    """
    Mixin for inventory query operations.

    Inventory is an OFF-CHAIN module that queries provider status endpoints
    to retrieve cluster resource information from Akash providers.
    """

    def query_cluster_inventory(
        self, provider_endpoint: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Query cluster inventory from provider status endpoint.

        The Akash inventory system is internal to each provider and exposed through
        the provider's status endpoint at /status, not separate inventory endpoints.

        Args:
            provider_endpoint: Provider endpoint (e.g., "provider.example.com:8443")
            timeout: Connection timeout in seconds

        Returns:
            Dict with cluster inventory data or error information
        """
        try:
            logger.info(
                f"Querying cluster inventory from provider: {provider_endpoint}"
            )

            if not provider_endpoint:
                return {
                    "status": "error",
                    "error": "provider_endpoint is required for inventory queries",
                }

            if not hasattr(self, "client") or not self.client:
                return {
                    "status": "error",
                    "error": "InventoryClient requires a valid AkashClient for provider queries",
                    "details": "Use akash_client.inventory.query_cluster_inventory() instead",
                }

            status_result = self.client.discovery.get_provider_status(
                provider_endpoint, use_https=True
            )

            if status_result.get("status") != "success":
                return {
                    "status": "error",
                    "error": f"Failed to get provider status: {status_result.get('error', 'Unknown error')}",
                    "details": "Cannot retrieve inventory without provider status",
                }

            provider_status = status_result.get("provider_status", {})
            cluster_info = provider_status.get("cluster", {})

            cluster_data = {
                "status": "success",
                "nodes": [],
                "storage": [],
                "provider": provider_endpoint,
            }

            inventory = cluster_info.get("inventory", {})
            available = inventory.get("available", {})

            available_nodes = available.get("nodes", [])
            for node_info in available_nodes:
                if not isinstance(node_info, dict):
                    continue

                allocatable = node_info.get("allocatable", {})
                node_available = node_info.get("available", {})

                node_data = {
                    "name": node_info.get("name", "unknown"),
                    "resources": {
                        "cpu": {
                            "allocatable": str(allocatable.get("cpu", 0)),
                            "available": str(node_available.get("cpu", 0)),
                            "capacity": str(allocatable.get("cpu", 0)),
                        },
                        "memory": {
                            "allocatable": str(allocatable.get("memory", 0)),
                            "available": str(node_available.get("memory", 0)),
                            "capacity": str(allocatable.get("memory", 0)),
                        },
                        "gpu": {
                            "allocatable": str(allocatable.get("gpu", 0)),
                            "available": str(node_available.get("gpu", 0)),
                            "capacity": str(allocatable.get("gpu", 0)),
                        },
                        "ephemeral_storage": {
                            "allocatable": str(allocatable.get("storage_ephemeral", 0)),
                            "available": str(
                                node_available.get("storage_ephemeral", 0)
                            ),
                            "capacity": str(allocatable.get("storage_ephemeral", 0)),
                        },
                    },
                    "capabilities": {
                        "storage_classes": []  # Will be populated from storage section
                    },
                }
                cluster_data["nodes"].append(node_data)

            available_storage = available.get("storage", [])
            storage_classes = set()

            for storage_info in available_storage:
                if not isinstance(storage_info, dict):
                    continue

                storage_class = storage_info.get("class", "unknown")
                storage_classes.add(storage_class)

                storage_data = {
                    "class": storage_class,
                    "allocatable": str(storage_info.get("allocatable", 0)),
                    "available": str(storage_info.get("available", 0)),
                    "capacity": str(storage_info.get("allocatable", 0)),
                }
                cluster_data["storage"].append(storage_data)

            for node in cluster_data["nodes"]:
                node["capabilities"]["storage_classes"] = list(storage_classes)

            if not cluster_data["nodes"]:
                cluster_data["nodes"].append(
                    {
                        "name": f"{provider_endpoint}-default",
                        "resources": {
                            "cpu": {
                                "available": "0",
                                "allocated": "0",
                                "capacity": "0",
                            },
                            "memory": {
                                "available": "0",
                                "allocated": "0",
                                "capacity": "0",
                            },
                            "gpu": {
                                "available": "0",
                                "allocated": "0",
                                "capacity": "0",
                            },
                            "ephemeral_storage": {
                                "available": "0",
                                "allocated": "0",
                                "capacity": "0",
                            },
                        },
                        "capabilities": {"storage_classes": []},
                    }
                )

            logger.info(
                f"Successfully retrieved cluster inventory: {len(cluster_data['nodes'])} nodes, {len(cluster_data['storage'])} storage classes"
            )
            return cluster_data

        except Exception as e:
            logger.error(f"Failed to query cluster inventory: {e}")
            return {"status": "error", "error": str(e)}

    def _parse_node_resources(self, resources: Dict) -> Dict[str, Any]:
        """Parse node resources from inventory response."""
        parsed = {}

        resource_types = [
            "cpu",
            "memory",
            "gpu",
            "ephemeral_storage",
            "volumes_attached",
            "volumes_mounted",
        ]

        for resource_type in resource_types:
            resource_data = resources.get(resource_type, {})

            if resource_type in ["cpu", "memory", "gpu"]:
                quantity = resource_data.get("quantity", {})
                info = resource_data.get("info", [])

                parsed[resource_type] = {
                    "allocatable": str(quantity.get("allocatable", "0")),
                    "allocated": str(quantity.get("allocated", "0")),
                    "capacity": str(quantity.get("capacity", "0")),
                    "info": info if isinstance(info, list) else [],
                }
            else:
                parsed[resource_type] = {
                    "allocatable": str(resource_data.get("allocatable", "0")),
                    "allocated": str(resource_data.get("allocated", "0")),
                    "capacity": str(resource_data.get("capacity", "0")),
                }

        return parsed

    def query_node_inventory(
        self, provider_endpoint: str, node_name: str = "", timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Query individual node inventory from provider status endpoint.

        Since Akash providers don't expose individual node inventory externally,
        this method extracts node-level information from the cluster inventory.

        Args:
            provider_endpoint: Provider endpoint
            node_name: Specific node name to query (optional filter)
            timeout: Connection timeout in seconds

        Returns:
            Dict with node inventory data or error information
        """
        try:
            logger.info(
                f"Querying node inventory from {provider_endpoint}: {node_name or 'cluster aggregate'}"
            )

            cluster_result = self.query_cluster_inventory(provider_endpoint, timeout)

            if cluster_result.get("status") != "success":
                return {
                    "status": "error",
                    "error": f"Failed to get cluster inventory: {cluster_result.get('error', 'Unknown error')}",
                    "details": "Cannot retrieve node inventory without cluster data",
                }

            nodes = cluster_result.get("nodes", [])

            if node_name:
                for node in nodes:
                    if node.get("name", "").lower().find(node_name.lower()) >= 0:
                        return {"status": "success", **node}

                return {
                    "status": "error",
                    "error": f"Node '{node_name}' not found in cluster inventory",
                    "details": f"Available nodes: {[n.get('name', 'unknown') for n in nodes]}",
                }

            if nodes:
                primary_node = nodes[0]
                return {"status": "success", **primary_node}
            else:
                return {
                    "status": "error",
                    "error": "No nodes found in cluster inventory",
                    "details": "Provider may not have inventory data available",
                }

        except Exception as e:
            logger.error(f"Failed to query node inventory: {e}")
            return {"status": "error", "error": str(e)}
