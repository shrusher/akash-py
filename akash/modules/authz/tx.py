import logging
import time
from typing import Any, Dict, List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from akash.tx import BroadcastResult

logger = logging.getLogger(__name__)


class AuthzTx:
    """
    Mixin for authorization transaction operations.
    """

    def grant_authorization(
        self,
        wallet,
        grantee: str,
        msg_type_url: str = "/cosmos.bank.v1beta1.MsgSend",
        spend_limit: str = "1000000000",
        denom: str = "uakt",
        authorization_type: str = "send",
        expiration_days: int = 30,
        memo: str = "",
        fee_amount: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Grant authorization to another account with gas simulation.

        Args:
            wallet: Wallet to sign the transaction
            grantee: Address of the account receiving the grant
            msg_type_url: Type URL of messages the grantee can execute (default: MsgSend)
            spend_limit: Maximum amount the grantee can spend (default: 1000 AKT)
            denom: Token denomination (default: uakt)
            authorization_type: Type of authorization - "send" or "generic" (default: send)
            expiration_days: Days until grant expires (default: 30)
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit for transaction
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Whether to simulate for gas estimation (default: True)

        Returns:
            BroadcastResult: Transaction result with success status, tx_hash, etc.
        """
        try:
            from ...tx import broadcast_transaction_rpc, BroadcastResult

            # Calculate expiration timestamp (current time + days)
            expiration_seconds = int(time.time()) + (expiration_days * 24 * 60 * 60)

            if authorization_type == "send":
                use_send_auth = True
            elif authorization_type == "generic":
                use_send_auth = False
            else:
                raise ValueError(
                    f"Invalid authorization_type: {authorization_type}. Must be 'send' or 'generic'"
                )

            if use_send_auth:
                msg_grant = {
                    "@type": "/cosmos.authz.v1beta1.MsgGrant",
                    "granter": wallet.address,
                    "grantee": grantee,
                    "grant": {
                        "authorization": {
                            "@type": "/cosmos.bank.v1beta1.SendAuthorization",
                            "spend_limit": [{"denom": denom, "amount": spend_limit}],
                        },
                        "expiration": {"seconds": str(expiration_seconds), "nanos": 0},
                    },
                }
            else:
                msg_grant = {
                    "@type": "/cosmos.authz.v1beta1.MsgGrant",
                    "granter": wallet.address,
                    "grantee": grantee,
                    "grant": {
                        "authorization": {
                            "@type": "/cosmos.authz.v1beta1.GenericAuthorization",
                            "msg": msg_type_url,
                        },
                        "expiration": {"seconds": str(expiration_seconds), "nanos": 0},
                    },
                }

            logger.info(
                f"Granting {msg_type_url} authorization from {wallet.address} to {grantee}, limit: {spend_limit} {denom}"
            )

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_grant],
                memo=memo,
                fee_amount=fee_amount or "7000",
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Grant authorization failed: {e}")
            from ...tx import BroadcastResult

            return BroadcastResult(
                tx_hash=None,
                code=-1,
                raw_log=f"Grant authorization failed: {str(e)}",
                success=False,
            )

    def revoke_authorization(
        self,
        wallet,
        grantee: str,
        msg_type_url: str,
        memo: str = "",
        fee_amount: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Revoke authorization from another account with gas simulation.

        Args:
            wallet: Wallet to sign the transaction
            grantee: Address of the account losing the grant
            msg_type_url: Type URL of messages to revoke
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit for transaction
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Whether to simulate for gas estimation (default: True)

        Returns:
            BroadcastResult: Transaction result with success status, tx_hash, etc.
        """
        try:
            from ...tx import broadcast_transaction_rpc, BroadcastResult

            msg_revoke = {
                "@type": "/cosmos.authz.v1beta1.MsgRevoke",
                "granter": wallet.address,
                "grantee": grantee,
                "msg_type_url": msg_type_url,
            }

            logger.info(f"Revoking {msg_type_url} authorization from {grantee}")

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_revoke],
                memo=memo,
                fee_amount=fee_amount or "5000",
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Revoke authorization failed: {e}")
            from ...tx import BroadcastResult

            return BroadcastResult(
                tx_hash=None,
                code=-1,
                raw_log=f"Revoke authorization failed: {str(e)}",
                success=False,
            )

    def execute_authorized(
        self,
        wallet,
        messages: List[Dict[str, Any]],
        memo: str = "",
        fee_amount: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Execute messages on behalf of another account (if authorized) with gas simulation.

        Args:
            wallet: Wallet of the grantee executing the messages
            messages: List of message dictionaries to execute
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit for transaction
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Whether to simulate for gas estimation (default: True)

        Returns:
            BroadcastResult: Transaction result with success status, tx_hash, etc.
        """
        try:
            from ...tx import broadcast_transaction_rpc, BroadcastResult

            msg_exec = {
                "@type": "/cosmos.authz.v1beta1.MsgExec",
                "grantee": wallet.address,
                "msgs": messages,
            }

            logger.info(
                f"Executing {len(messages)} authorized messages as {wallet.address}"
            )

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_exec],
                memo=memo,
                fee_amount=fee_amount or "10000",
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Execute authorized failed: {e}")
            from ...tx import BroadcastResult

            return BroadcastResult(
                tx_hash=None,
                code=-1,
                raw_log=f"Execute authorized failed: {str(e)}",
                success=False,
            )
