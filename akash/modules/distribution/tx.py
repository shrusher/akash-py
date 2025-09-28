import logging

from ...tx import BroadcastResult, broadcast_transaction_rpc

logger = logging.getLogger(__name__)


class DistributionTx:
    """
    Mixin for distribution transaction operations.
    """

    def withdraw_delegator_reward(
        self,
        wallet,
        validator_address: str,
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: int = 200000,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Withdraw rewards from a specific validator.

        Args:
            wallet: Wallet to sign the transaction
            validator_address: Validator address to withdraw rewards from
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit
            gas_adjustment: Multiplier for gas estimation
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult: Transaction result with success status
        """
        try:
            msg_withdraw = {
                "@type": "/cosmos.distribution.v1beta1.MsgWithdrawDelegatorReward",
                "delegator_address": wallet.address,
                "validator_address": validator_address,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_withdraw],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=False,
            )

        except Exception as e:
            logger.error(f"Withdraw delegator reward failed: {e}")
            raise

    def withdraw_validator_commission(
        self,
        wallet,
        validator_address: str,
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: int = 200000,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Withdraw validator commission.

        Args:
            wallet: Wallet to sign the transaction
            validator_address: Validator address to withdraw commission from
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult: Transaction result with success status
        """
        try:
            msg_withdraw_commission = {
                "@type": "/cosmos.distribution.v1beta1.MsgWithdrawValidatorCommission",
                "validator_address": validator_address,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_withdraw_commission],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=False,
            )

        except Exception as e:
            logger.error(f"Withdraw validator commission failed: {e}")
            raise

    def set_withdraw_address(
        self,
        wallet,
        withdraw_address: str,
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: int = 200000,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Set the withdrawal address for rewards.

        Args:
            wallet: Wallet to sign the transaction
            withdraw_address: Address to receive rewards
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult: Transaction result with success status
        """
        try:
            msg_set_withdraw = {
                "@type": "/cosmos.distribution.v1beta1.MsgSetWithdrawAddress",
                "delegator_address": wallet.address,
                "withdraw_address": withdraw_address,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_set_withdraw],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=False,
            )

        except Exception as e:
            logger.error(f"Set withdraw address failed: {e}")
            raise

    def fund_community_pool(
        self,
        wallet,
        amount: str,
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: int = 200000,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Fund the community pool with specified amount.

        Args:
            wallet: Wallet to sign the transaction
            amount: Amount to fund
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult: Transaction result with success status
        """
        try:
            msg_fund_pool = {
                "@type": "/cosmos.distribution.v1beta1.MsgFundCommunityPool",
                "depositor": wallet.address,
                "amount": [{"denom": denom, "amount": amount}],
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_fund_pool],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=False,
            )

        except Exception as e:
            logger.error(f"Fund community pool failed: {e}")
            raise

    def withdraw_all_rewards(
        self,
        wallet,
        memo: str = "",
        fee_amount: str = "8000",
        gas_limit: int = 300000,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Withdraw all delegation rewards for a delegator.

        Args:
            wallet: Wallet to sign the transaction
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult: Transaction result with success status
        """
        try:
            from ..staking.query import StakingQuery

            delegations = StakingQuery.get_delegations(self, wallet.address)
            if not delegations:
                logger.info("No delegations found")
                return BroadcastResult("", 1, "No delegations found", False)

            messages = [
                {
                    "@type": "/cosmos.distribution.v1beta1.MsgWithdrawDelegatorReward",
                    "delegator_address": wallet.address,
                    "validator_address": delegation.get("delegation", {}).get(
                        "validator_address", ""
                    ),
                }
                for delegation in delegations
                if delegation.get("delegation", {}).get("validator_address")
            ]

            if not messages:
                logger.info("No valid delegations found")
                return BroadcastResult("", 1, "No valid delegations found", False)

            logger.info(f"Withdrawing rewards from {len(messages)} validators")
            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=messages,
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=False,
            )

        except Exception as e:
            logger.error(f"Withdraw all rewards failed: {e}")
            raise
