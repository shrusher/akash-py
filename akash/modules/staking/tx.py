import bech32
import logging
from decimal import Decimal
from typing import Dict, Optional, Any

from ...tx import BroadcastResult, broadcast_transaction_rpc

logger = logging.getLogger(__name__)


class StakingTx:
    """
    Mixin for staking transaction operations.
    """

    def delegate(
        self,
        wallet,
        validator_address: str,
        amount: str,
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Delegate tokens to a validator with enhanced gas simulation.

        Args:
            wallet: AkashWallet instance
            validator_address: Validator address
            amount: Amount to delegate
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Delegating {amount} {denom} to {validator_address}")
            msg_delegate = {
                "@type": "/cosmos.staking.v1beta1.MsgDelegate",
                "delegator_address": wallet.address,
                "validator_address": validator_address,
                "amount": {"denom": denom, "amount": amount},
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_delegate],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to delegate: {e}")
            return BroadcastResult("", 1, f"Delegation failed: {e}", False)

    def undelegate(
        self,
        wallet,
        validator_address: str,
        amount: str,
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Undelegate tokens from a validator.

        Args:
            wallet: AkashWallet instance
            validator_address: Validator address
            amount: Amount to undelegate
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Undelegating {amount} {denom} from {validator_address}")
            msg_undelegate = {
                "@type": "/cosmos.staking.v1beta1.MsgUndelegate",
                "delegator_address": wallet.address,
                "validator_address": validator_address,
                "amount": {"denom": denom, "amount": amount},
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_undelegate],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to undelegate: {e}")
            return BroadcastResult("", 1, f"Undelegation failed: {e}", False)

    def redelegate(
        self,
        wallet,
        src_validator_address: str,
        dst_validator_address: str,
        amount: str,
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Redelegate tokens from one validator to another.

        Args:
            wallet: AkashWallet instance
            src_validator_address: Source validator address
            dst_validator_address: Destination validator address
            amount: Amount to redelegate
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(
                f"Redelegating {amount} {denom} from {src_validator_address} to {dst_validator_address}"
            )
            msg_redelegate = {
                "@type": "/cosmos.staking.v1beta1.MsgBeginRedelegate",
                "delegator_address": wallet.address,
                "validator_src_address": src_validator_address,
                "validator_dst_address": dst_validator_address,
                "amount": {"denom": denom, "amount": amount},
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_redelegate],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit or 300000,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to redelegate: {e}")
            return BroadcastResult("", 1, f"Redelegation failed: {e}", False)

    def withdraw_rewards(
        self,
        wallet,
        validator_address: str,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Withdraw delegation rewards from a validator.

        Args:
            wallet: AkashWallet instance
            validator_address: Validator address
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Withdrawing rewards from {validator_address}")
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
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to withdraw rewards: {e}")
            return BroadcastResult("", 1, f"Reward withdrawal failed: {e}", False)

    def withdraw_all_rewards(
        self, wallet, memo: str = "", fee_amount: str = None, gas_limit: int = None
    ) -> BroadcastResult:
        """
        Withdraw all delegation rewards from all validators.

        Args:
            wallet: AkashWallet instance
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override

        Returns:
            BroadcastResult with transaction details
        """
        try:
            delegations = self.get_delegations(wallet.address)
            if not delegations:
                logger.info("No delegations found")
                return BroadcastResult("", 1, "No delegations found", False)

            logger.info(f"Withdrawing rewards from {len(delegations)} validators")
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

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=messages,
                memo=memo,
                fee_amount=fee_amount or str(5000 + (len(messages) * 2000)),
                gas_limit=gas_limit or (200000 + (len(messages) * 50000)),
                gas_adjustment=1.2,
                use_simulation=False,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to withdraw all rewards: {e}")
            return BroadcastResult("", 1, f"All rewards withdrawal failed: {e}", False)

    def create_validator(
        self,
        wallet,
        validator_info: Dict[str, Any],
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: Optional[int] = None,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Create a new validator.

        Args:
            wallet: AkashWallet instance for the validator
            validator_info: Dictionary with validator information
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit for transaction
            use_simulation: Use gas simulation

        Returns:
            BroadcastResult with transaction result
        """
        try:
            hrp, data = bech32.bech32_decode(wallet.address)
            if not data:
                raise ValueError(f"Invalid wallet address: {wallet.address}")
            validator_address = bech32.bech32_encode("akashvaloper", data)
            if not validator_address:
                raise ValueError(
                    f"Failed to encode validator address from {wallet.address}"
                )

            msg_create_validator = {
                "@type": "/cosmos.staking.v1beta1.MsgCreateValidator",
                "description": validator_info.get("description", {}),
                "commission": validator_info.get("commission", {}),
                "min_self_delegation": str(
                    validator_info.get("min_self_delegation", "1")
                ),
                "delegator_address": wallet.address,
                "validator_address": validator_address,
                "pubkey": validator_info.get("pubkey"),
                "value": validator_info.get(
                    "value", {"denom": "uakt", "amount": "1000000"}
                ),
            }

            logger.info(f"Creating validator {validator_info.get('validator_address')}")

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_create_validator],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Failed to create validator: {e}")
            raise

    def edit_validator(
        self,
        wallet,
        validator_address: str = None,
        description: Dict[str, Any] = None,
        commission_rate: str = None,
        min_self_delegation: str = None,
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: int = 200000,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Edit an existing validator.

        Args:
            wallet: AkashWallet instance for the validator
            validator_address: Validator operator address
            description: Updated description fields
            commission_rate: New commission rate
            min_self_delegation: New minimum self delegation
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit for transaction
            use_simulation: Use gas simulation

        Returns:
            BroadcastResult with transaction result
        """
        try:
            if (
                description is None
                and commission_rate is None
                and min_self_delegation is None
            ):
                raise ValueError(
                    "At least one parameter (description, commission_rate, or min_self_delegation) must be provided"
                )

            if not validator_address:
                hrp, data = bech32.bech32_decode(wallet.address)
                if not data:
                    raise ValueError(f"Invalid wallet address: {wallet.address}")
                validator_address = bech32.bech32_encode("akashvaloper", data)
                if not validator_address:
                    raise ValueError(
                        f"Failed to encode validator address from {wallet.address}"
                    )

            msg_edit_validator = {
                "@type": "/cosmos.staking.v1beta1.MsgEditValidator",
                "validator_address": validator_address,
                "description": description
                or {
                    "moniker": "[do-not-modify]",
                    "identity": "[do-not-modify]",
                    "website": "[do-not-modify]",
                    "security_contact": "[do-not-modify]",
                    "details": "[do-not-modify]",
                },
            }

            if commission_rate is not None:
                rate_decimal = Decimal(str(commission_rate))
                rate_scaled = int(rate_decimal * (10**18))
                msg_edit_validator["commission_rate"] = str(rate_scaled)

            if min_self_delegation is not None:
                msg_edit_validator["min_self_delegation"] = str(min_self_delegation)

            logger.info(f"Editing validator {validator_address}")

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_edit_validator],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Failed to edit validator: {e}")
            raise
