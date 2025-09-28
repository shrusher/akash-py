import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InventoryUtils:
    """
    Mixin for inventory utilities.
    """

    def aggregate_inventory_data(self, inventory_results: list) -> Dict[str, Any]:
        """
        Aggregate inventory data from multiple providers.

        Args:
            inventory_results: List of inventory query results from providers

        Returns:
            Dictionary with aggregated inventory statistics
        """
        try:
            logger.info(
                f"Aggregating inventory data from {len(inventory_results)} providers"
            )

            if not inventory_results:
                return {
                    "status": "error",
                    "error": "No inventory results provided for aggregation",
                }

            total_nodes = 0
            total_storage_classes = set()
            resource_totals = {
                "cpu": {"allocatable": 0, "allocated": 0, "capacity": 0},
                "memory": {"allocatable": 0, "allocated": 0, "capacity": 0},
                "gpu": {"allocatable": 0, "allocated": 0, "capacity": 0},
                "ephemeral_storage": {"allocatable": 0, "allocated": 0, "capacity": 0},
            }

            successful_providers = 0
            errors = []

            for result in inventory_results:
                if result.get("status") == "success":
                    successful_providers += 1
                    nodes = result.get("nodes", [])
                    total_nodes += len(nodes)

                    for node in nodes:
                        resources = node.get("resources", {})
                        for resource_type in resource_totals.keys():
                            if resource_type in resources:
                                for metric in ["allocatable", "allocated", "capacity"]:
                                    try:
                                        value = resources[resource_type].get(
                                            metric, "0"
                                        )
                                        numeric_value = self._parse_k8s_resource(value)
                                        resource_totals[resource_type][
                                            metric
                                        ] += numeric_value
                                    except (ValueError, KeyError):
                                        pass

                        capabilities = node.get("capabilities", {})
                        storage_classes = capabilities.get("storage_classes", [])
                        total_storage_classes.update(storage_classes)

                    storage = result.get("storage", [])
                    for storage_entry in storage:
                        total_storage_classes.add(storage_entry.get("class", ""))

                else:
                    errors.append(
                        {
                            "provider": result.get("provider", "unknown"),
                            "error": result.get("error", "unknown error"),
                        }
                    )

            aggregated_data = {
                "status": "success",
                "summary": {
                    "total_providers_queried": len(inventory_results),
                    "successful_providers": successful_providers,
                    "failed_providers": len(errors),
                    "total_nodes": total_nodes,
                    "storage_classes": sorted(list(total_storage_classes)),
                },
                "resources": resource_totals,
                "errors": errors,
            }

            logger.info(
                f"Aggregated inventory: {successful_providers}/{len(inventory_results)} providers, {total_nodes} nodes"
            )
            return aggregated_data

        except Exception as e:
            logger.error(f"Failed to aggregate inventory data: {e}")
            return {"status": "error", "error": str(e)}

    def _parse_k8s_resource(self, value: str) -> int:
        """
        Parse Kubernetes resource format (e.g., "1000m", "1Gi", "100Mi").

        Args:
            value: Resource value string

        Returns:
            Numeric value in base units
        """
        if not value or value == "0":
            return 0

        if value.endswith("m"):
            return int(value[:-1])

        unit_multipliers = {
            "Ki": 1024,
            "Mi": 1024**2,
            "Gi": 1024**3,
            "Ti": 1024**4,
            "K": 1000,
            "M": 1000**2,
            "G": 1000**3,
            "T": 1000**4,
        }

        for unit, multiplier in unit_multipliers.items():
            if value.endswith(unit):
                return int(float(value[: -len(unit)]) * multiplier)

        return int(float(value))
