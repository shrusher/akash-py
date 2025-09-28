import logging
import socket
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ProviderUtils:
    """
    Mixin for provider utilities.
    """

    def get_provider_attributes(self, owner_address: str) -> List[Dict[str, str]]:
        """
        Get provider attributes.

        Args:
            owner_address: Provider owner address

        Returns:
            List of attribute dictionaries with 'key' and 'value'
        """
        try:
            provider_info = self.get_provider(owner_address)
            return provider_info.get("attributes", [])
        except Exception as e:
            logger.error(f"Failed to get provider attributes: {e}")
            raise

    def query_providers_by_attributes(
        self, required_attributes: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Query providers that have specific attributes.

        Args:
            required_attributes: List of required attribute dictionaries

        Returns:
            List of matching provider information
        """
        try:
            logger.info(
                f"Querying providers by attributes: {len(required_attributes)} filters"
            )

            all_providers = self.get_providers()
            matching_providers = []

            for provider in all_providers:
                provider_attrs = provider.get("attributes", [])
                matches_all = True

                for required_attr in required_attributes:
                    attr_match = False
                    for provider_attr in provider_attrs:
                        if provider_attr.get("key") == required_attr.get(
                            "key"
                        ) and provider_attr.get("value") == required_attr.get("value"):
                            attr_match = True
                            break

                    if not attr_match:
                        matches_all = False
                        break

                if matches_all:
                    matching_providers.append(provider)

            logger.info(
                f"Found {len(matching_providers)} providers matching attributes"
            )
            return matching_providers

        except Exception as e:
            logger.error(f"Failed to query providers by attributes: {e}")
            raise

    def validate_provider_config(self, provider_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate provider configuration before registration.

        Args:
            provider_info: Provider configuration to validate

        Returns:
            Validation result with errors and warnings
        """
        try:
            errors = []
            warnings = []

            if not provider_info.get("host_uri"):
                errors.append("host_uri is required")

            email = provider_info.get("email", "")
            if email and "@" not in email:
                errors.append("Invalid email format")

            host_uri = provider_info.get("host_uri", "")
            if host_uri and not (
                host_uri.startswith("http://") or host_uri.startswith("https://")
            ):
                warnings.append("host_uri should use http:// or https://")

            attributes = provider_info.get("attributes", [])
            for attr in attributes:
                if not attr.get("key"):
                    errors.append("Attribute key cannot be empty")
                if not attr.get("value"):
                    warnings.append(f"Attribute '{attr.get('key')}' has empty value")

            return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {e}"],
                "warnings": [],
            }

    def get_provider_info_basic(self, owner_address: str) -> Dict[str, Any]:
        """
        Get basic provider information from blockchain.

        Args:
            owner_address: Provider owner address

        Returns:
            Basic provider status information
        """
        try:
            logger.info(f"Querying provider status: {owner_address}")

            provider = self.get_provider(owner_address)
            if not provider:
                return {"status": "not_found", "available": False}

            host_uri = provider.get("host_uri", "")
            if host_uri:
                return {
                    "status": "active",
                    "available": True,
                    "host_uri": host_uri,
                    "attributes": provider.get("attributes", []),
                }
            else:
                return {
                    "status": "inactive",
                    "available": False,
                    "attributes": provider.get("attributes", []),
                }

        except Exception as e:
            logger.error(f"Failed to get provider status: {e}")
            raise

    def validate_provider_endpoint(self, provider_address: str) -> bool:
        """
        Validate provider endpoint connectivity and DNS resolution.

        Args:
            provider_address: Provider address to validate

        Returns:
            bool: True if provider endpoint is accessible, False otherwise
        """
        try:
            if hasattr(self, 'akash_client'):
                provider_info = self.akash_client.provider.get_provider(provider_address)
            else:
                provider_info = self.get_provider(provider_address)

            if not provider_info or not provider_info.get('host_uri'):
                logger.debug(f"Provider {provider_address} has no host_uri")
                return False

            host_uri = provider_info.get('host_uri')
            parsed = urlparse(host_uri)
            hostname = parsed.hostname or parsed.netloc.split(':')[0]

            socket.gethostbyname(hostname)
            logger.debug(f"Provider {provider_address} endpoint {host_uri} is accessible")
            return True

        except Exception as e:
            logger.debug(f"Provider {provider_address} endpoint validation failed: {e}")
            return False

    def filter_valid_providers(self, provider_addresses: List[str]) -> List[str]:
        """
        Filter provider addresses to only include those with valid endpoints.

        Args:
            provider_addresses: List of provider addresses

        Returns:
            List of provider addresses with valid endpoints
        """
        valid_providers = []

        for provider_addr in provider_addresses:
            if self.validate_provider_endpoint(provider_addr):
                valid_providers.append(provider_addr)
            else:
                logger.debug(f"Filtered out provider {provider_addr} due to invalid endpoint")

        return valid_providers
