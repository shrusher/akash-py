import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from akash.tx import BroadcastResult

logger = logging.getLogger(__name__)


class FeegrantTx:
    """
    Mixin for fee grant transaction operations.
    """

    def grant_allowance(
        self,
        wallet,
        grantee: str,
        allowance_type: str = "basic",
        spend_limit: str = "1000000",
        denom: str = "uakt",
        expiration: Optional[str] = None,
        period_seconds: int = 86400,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Grant fee allowance to another account.

        Args:
            wallet: Wallet to sign the transaction (granter)
            grantee: Address of the account receiving the allowance
            allowance_type: Type of allowance ("basic" or "periodic")
            spend_limit: Maximum amount that can be spent (in uakt)
            denom: Token denomination
            expiration: Optional expiration time (RFC3339 format)
            period_seconds: Period duration in seconds for periodic allowance (default: 86400 = 24 hours)
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            from ...tx import broadcast_transaction_rpc, BroadcastResult

            if allowance_type == "basic":
                allowance_dict = {
                    "@type": "/cosmos.feegrant.v1beta1.BasicAllowance",
                    "spend_limit": [{"denom": denom, "amount": spend_limit}],
                }

                if expiration:
                    allowance_dict["expiration"] = expiration

            elif allowance_type == "periodic":
                period_limit = str(int(spend_limit) // 10)

                allowance_dict = {
                    "@type": "/cosmos.feegrant.v1beta1.PeriodicAllowance",
                    "basic": {"spend_limit": [{"denom": denom, "amount": spend_limit}]},
                    "period": {"seconds": period_seconds, "nanos": 0},
                    "period_spend_limit": [{"denom": denom, "amount": period_limit}],
                }
            else:
                return BroadcastResult(
                    "", 1, f"Unknown allowance type: {allowance_type}", False
                )

            msg_dict = {
                "@type": "/cosmos.feegrant.v1beta1.MsgGrantAllowance",
                "granter": wallet.address,
                "grantee": grantee,
                "allowance": allowance_dict,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Grant allowance failed: {e}")
            from ...tx import BroadcastResult

            return BroadcastResult("", 1, f"Grant allowance failed: {e}", False)

    def revoke_allowance(
        self,
        wallet,
        grantee: str,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Revoke fee allowance from another account.

        Args:
            wallet: Wallet to sign the transaction (granter)
            grantee: Address of the account losing the allowance
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            from ...tx import broadcast_transaction_rpc, BroadcastResult

            msg_dict = {
                "@type": "/cosmos.feegrant.v1beta1.MsgRevokeAllowance",
                "granter": wallet.address,
                "grantee": grantee,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Revoke allowance failed: {e}")
            from ...tx import BroadcastResult

            return BroadcastResult("", 1, f"Revoke allowance failed: {e}", False)
