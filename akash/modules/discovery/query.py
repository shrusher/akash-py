import logging
import platform
import sys
from typing import Dict, Any, Optional

from akash import __version__

logger = logging.getLogger(__name__)


class DiscoveryQuery:
    """
    Mixin for discovery query operations from blockchain.

    Handles blockchain queries to discover providers and their
    on-chain attributes, as well as RPC client information.
    """

    def get_providers(
            self,
            limit: Optional[int] = 100,
            offset: Optional[int] = None,
            count_total: bool = False,
    ) -> Dict[str, Any]:
        """
        Query providers from the blockchain with categorization and pagination.

        Args:
            limit: Maximum number of providers to return (default: 100)
            offset: Number of results to skip (default: 0)
            count_total: Include total count in response (default: False)

        Returns:
            Dict with providers list, summary, and categorization
        """
        try:
            logger.info("Querying providers from blockchain")

            providers_result = self.akash_client.provider.get_providers(
                limit=limit, offset=offset, count_total=count_total
            )

            if isinstance(providers_result, dict) and "providers" in providers_result:
                providers = providers_result["providers"]
            else:
                providers = providers_result if providers_result else []

            all_providers = []
            active_providers = []
            inactive_providers = []

            for provider in providers:
                provider_info = {
                    "owner": provider.get("owner", ""),
                    "host_uri": provider.get("host_uri", "")
                                or provider.get("info", {}).get("host_uri", ""),
                    "attributes": provider.get("attributes", []),
                }

                if "info" in provider:
                    provider_info["email"] = provider["info"].get("email", "")
                    provider_info["website"] = provider["info"].get("website", "")

                all_providers.append(provider_info)

                if provider_info.get("host_uri"):
                    active_providers.append(provider_info)
                else:
                    inactive_providers.append(provider_info)

            return {
                "status": "success",
                "total": len(all_providers),
                "summary": {
                    "active": len(active_providers),
                    "inactive": len(inactive_providers),
                },
                "providers": all_providers,
                "active_providers": active_providers,
                "inactive_providers": inactive_providers,
            }

        except Exception as e:
            logger.error(f"Failed to query providers: {e}")
            return {
                "status": "error",
                "error": str(e),
                "providers": [],
                "active_providers": [],
                "inactive_providers": [],
            }

    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about this SDK client and RPC compatibility.

        Attempts to query the RPC node's API version through the "akash" endpoint
        similar to the official client discovery mechanism.

        Returns:
            Dict with client information
        """
        try:
            logger.info("Getting client and RPC information")

            api_version = "v1beta2"

            try:
                if hasattr(self.akash_client, "client") and hasattr(
                        self.akash_client.client, "call"
                ):
                    result = self.akash_client.client.call("akash", {})
                    if result and isinstance(result, dict) and "client_info" in result:
                        api_version = result["client_info"].get(
                            "api_version", api_version
                        )
                        logger.info(f"Detected RPC API version: {api_version}")
                    else:
                        logger.info(
                            "RPC node does not support 'akash' endpoint, using default API version"
                        )
                else:
                    logger.info(
                        "RPC client does not support direct calls, using default API version"
                    )
            except Exception as e:
                logger.debug(f"Could not query RPC API version: {e}")

            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

            return {
                "status": "success",
                "api_version": api_version,
                "sdk_name": "akash-python-sdk",
                "sdk_version": __version__,
                "python_version": python_version,
                "platform": platform.system(),
                "architecture": platform.machine(),
                "supported_endpoints": ["gRPC", "HTTP"],
                "rpc_endpoint": getattr(self.akash_client, "rpc_endpoint", "unknown"),
            }

        except Exception as e:
            logger.error(f"Failed to get client info: {e}")
            return {"status": "error", "error": str(e)}
