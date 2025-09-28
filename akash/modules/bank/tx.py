import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from akash.tx import BroadcastResult

logger = logging.getLogger(__name__)


class BankTx:
    """
    Mixin for bank transaction operations.
    """

    def send(
        self,
        wallet,
        to_address: str,
        amount: str,
        denom: str = "uakt",
        memo: str = "",
        fee_amount: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_adjustment: float = 1.2,
    ) -> "BroadcastResult":
        """
        Send tokens with enhanced gas simulation.

        Args:
            wallet: AkashWallet instance
            to_address: Recipient address
            amount: Amount in base units (uakt)
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Fee amount in uakt (auto-scales with gas if not provided)
            gas_limit: Gas limit override (disables simulation if provided)
            gas_adjustment: Multiplier for simulated gas (default 1.2)

        Returns:
            BroadcastResult with transaction details
        """
        try:
            from ...tx import broadcast_transaction_rpc, BroadcastResult

            logger.info(f"Sending {amount} {denom} to {to_address}")

            msg_send = {
                "@type": "/cosmos.bank.v1beta1.MsgSend",
                "from_address": wallet.address,
                "to_address": to_address,
                "amount": [{"denom": denom, "amount": amount}],
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_send],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=(gas_limit is None),
                wait_for_confirmation=True,
            )

        except Exception as e:
            logger.error(f"Failed to send tokens: {e}")
            return BroadcastResult("", 1, f"Send failed: {e}", False)
