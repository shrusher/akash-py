import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AuditUtils:
    """
    Mixin for audit utilities.
    """

    def validate_provider_attributes(self, provider_data: Dict) -> bool:
        """
        Validate provider attribute structure.

        Args:
            provider_data: Provider attribute data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            required_fields = ["owner", "auditor", "attributes"]

            for field in required_fields:
                if field not in provider_data:
                    logger.error(f"Missing required field: {field}")
                    return False

            if not isinstance(provider_data["attributes"], list):
                logger.error("Attributes must be a list")
                return False

            for attr in provider_data["attributes"]:
                if not isinstance(attr, dict):
                    logger.error("Each attribute must be a dictionary")
                    return False
                if "key" not in attr or "value" not in attr:
                    logger.error("Each attribute must have 'key' and 'value'")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating provider attributes: {e}")
            return False
