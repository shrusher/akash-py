import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FeegrantUtils:
    """
    Mixin for fee grant utilities.
    """

    def create_basic_allowance(
        self, spend_limit: str, denom: str = "uakt", expiration: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a basic allowance dictionary structure.

        Args:
            spend_limit: Maximum amount that can be spent
            denom: Token denomination
            expiration: Optional expiration time (RFC3339 format)

        Returns:
            dict: Basic allowance structure
        """
        allowance = {
            "@type": "/cosmos.feegrant.v1beta1.BasicAllowance",
            "spend_limit": [{"denom": denom, "amount": spend_limit}],
        }

        if expiration:
            allowance["expiration"] = expiration

        return allowance

    def create_periodic_allowance(
        self,
        total_limit: str,
        period_limit: str,
        period_seconds: int,
        denom: str = "uakt",
    ) -> Dict[str, Any]:
        """
        Create a periodic allowance dictionary structure.

        Args:
            total_limit: Total spend limit
            period_limit: Amount that can be spent per period
            period_seconds: Period duration in seconds
            denom: Token denomination

        Returns:
            dict: Periodic allowance structure
        """
        return {
            "@type": "/cosmos.feegrant.v1beta1.PeriodicAllowance",
            "basic": {"spend_limit": [{"denom": denom, "amount": total_limit}]},
            "period": {"seconds": str(period_seconds), "nanos": 0},
            "period_spend_limit": [{"denom": denom, "amount": period_limit}],
        }
