import logging

from ...tx import broadcast_transaction_rpc, BroadcastResult

logger = logging.getLogger(__name__)


class SlashingTx:
    """
    Mixin for slashing transaction operations.
    """

    def unjail(
        self,
        wallet,
        validator_address: str = None,
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Unjail a validator that has been jailed for downtime.

        Args:
            wallet: Validator's operator wallet
            validator_address: Validator address to unjail
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            if not validator_address:
                import bech32

                hrp, data = bech32.bech32_decode(wallet.address)
                if hrp == "akash" and data:
                    validator_address = bech32.bech32_encode("akashvaloper", data)
                else:
                    raise ValueError(f"Invalid wallet address format: {wallet.address}")
                
                if not validator_address:
                    raise ValueError("Failed to convert wallet address to validator address")

            msg_dict = {
                "@type": "/cosmos.slashing.v1beta1.MsgUnjail",
                "validator_addr": validator_address,
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
            logger.error(f"Unjail validator failed: {e}")
            return BroadcastResult("", 1, f"Unjail validator failed: {e}", False)
