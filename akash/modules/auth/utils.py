import logging
from typing import Dict, Optional
import bech32

logger = logging.getLogger(__name__)


def validate_address(address: str) -> bool:
    """
    Standalone function to validate if an address is correctly formatted using proper bech32 validation.

    Args:
        address: Bech32 address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not address or not isinstance(address, str):
            return False

        if not address.startswith("akash1"):
            return False

        # Decode bech32
        hrp, data = bech32.bech32_decode(address)
        if hrp != "akash" or data is None:
            return False

        # Check length (should be 20 bytes = 32 5-bit groups)
        if len(data) != 32:
            return False

        return True

    except Exception as e:
        logger.error(f"Address validation failed: {e}")
        return False


class AuthUtils:
    """
    Mixin for authentication utilities.
    """

    def get_account_info(self, address: str) -> Optional[Dict]:
        """
        Get basic account info including sequence and account number.
        This is a convenience method that extracts the most commonly needed info.

        Args:
            address: Bech32 account address

        Returns:
            Optional[Dict]: Account info with keys: 'address', 'sequence', 'account_number',
                           'has_pub_key', or None if account not found
        """
        account_data = self.get_account(address)

        if account_data:
            return {
                "address": account_data["address"],
                "sequence": (
                    int(account_data["sequence"]) if account_data.get("sequence") else 0
                ),
                "account_number": (
                    int(account_data["account_number"])
                    if account_data.get("account_number")
                    else 0
                ),
                "has_pub_key": bool(account_data.get("pub_key")),
            }

        return None

    def validate_address(self, address: str) -> bool:
        """
        Validate if an address is correctly formatted using proper bech32 validation.

        Args:
            address: Bech32 address to validate

        Returns:
            bool: True if valid, False otherwise
        """
        return validate_address(address)

    def validate_address_existence(self, address: str) -> bool:
        """
        Validate if an address exists on the blockchain.

        Args:
            address: Bech32 address to validate

        Returns:
            bool: True if address exists, False otherwise
        """
        try:
            account_info = self.get_account(address)
            return account_info is not None
        except Exception as e:
            logger.error(f"Error validating address {address}: {e}")
            return False

    def get_next_sequence_number(self, address: str) -> int:
        """
        Get the next sequence number for an account.
        This is useful for transaction construction.

        Args:
            address: Bech32 account address

        Returns:
            int: Next sequence number (0 if account doesn't exist)
        """
        account_info = self.get_account_info(address)
        if account_info:
            return account_info["sequence"]
        return 0

    def get_account_number(self, address: str) -> int:
        """
        Get the account number for an address.
        This is useful for transaction construction.

        Args:
            address: Bech32 account address

        Returns:
            int: Account number (0 if account doesn't exist)
        """
        account_info = self.get_account_info(address)
        if account_info:
            return account_info["account_number"]
        return 0
