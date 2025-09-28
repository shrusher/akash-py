import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IBCUtils:
    """
    Utility functions for IBC operations.
    """

    @staticmethod
    def _validate_channel_id(channel_id: str) -> bool:
        """
        Validate IBC channel identifier format.

        Args:
            channel_id: Channel ID to validate

        Returns:
            True if valid format
        """

        return (
            channel_id.startswith("channel-")
            and channel_id[8:].isdigit()
            and len(channel_id) > 8
        )

    @staticmethod
    def _validate_address_format(address: str, expected_prefix: Optional[str] = None) -> bool:
        """
        Validate bech32 address format using proper bech32 validation.

        Args:
            address: Address to validate
            expected_prefix: Expected address prefix (optional)

        Returns:
            True if valid format
        """
        try:
            import bech32

            if not address or not isinstance(address, str):
                return False

            hrp, data = bech32.bech32_decode(address)
            if hrp is None or data is None:
                return False

            if expected_prefix and hrp != expected_prefix:
                return False

            return True

        except Exception:
            return False
