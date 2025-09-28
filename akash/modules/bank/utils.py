import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BankUtils:
    """
    Mixin for bank utilities.
    """

    def estimate_fee(
        self, message_count: int = 1, gas_per_message: int = 200000
    ) -> Dict[str, Any]:
        """
        Estimate transaction fees based on message count and gas requirements.

        Args:
            message_count: Number of messages in transaction
            gas_per_message: Gas per message (default varies by message type)

        Returns:
            Dict with fee estimation details
        """
        try:
            total_gas = message_count * gas_per_message

            base_fee_rate = 0.025
            estimated_fee = int(total_gas * base_fee_rate)

            return {
                "gas_limit": total_gas,
                "estimated_fee": estimated_fee,
                "fee_denom": "uakt",
                "fee_akt": estimated_fee / 1_000_000,
                "message_count": message_count,
                "gas_per_message": gas_per_message,
            }

        except Exception as e:
            logger.error(f"Fee estimation failed: {e}")
            return {
                "gas_limit": 200000,
                "estimated_fee": 5000,
                "fee_denom": "uakt",
                "fee_akt": 0.005,
                "message_count": 1,
                "gas_per_message": 200000,
            }

    def validate_address(self, address: str) -> bool:
        """
        Validate if an address is correctly formatted using proper bech32 validation.
        Delegates to auth module's validate_address for the actual validation.

        Args:
            address: Address to validate

        Returns:
            bool: True if valid, False otherwise
        """
        return self.akash_client.auth.validate_address(address)

    def calculate_akt_amount(self, uakt_amount: str) -> float:
        """
        Convert uAKT (micro-AKT) to AKT.

        Args:
            uakt_amount: Amount in uAKT as string

        Returns:
            Amount in AKT as float
        """
        try:
            return int(uakt_amount) / 1_000_000
        except (ValueError, TypeError):
            return 0.0

    def calculate_uakt_amount(self, akt_amount: float) -> str:
        """
        Convert AKT to uAKT (micro-AKT).

        Args:
            akt_amount: Amount in AKT as float

        Returns:
            Amount in uAKT as string
        """
        try:
            return str(int(akt_amount * 1_000_000))
        except (ValueError, TypeError):
            return "0"
