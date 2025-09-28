import logging
import time
from typing import Dict, List, Any

from ...tx import BroadcastResult, broadcast_transaction_rpc

logger = logging.getLogger(__name__)


class DeploymentTx:
    """
    Mixin for deployment transaction operations.
    """

    def create_deployment(
        self,
        wallet,
        groups: List[Dict[str, Any]],
        deposit: str = "5000000",
        deposit_denom: str = "uakt",
        version: str = None,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Create deployment with complete resource specifications.

        Args:
            wallet: AkashWallet instance
            groups: List of group specifications with resources
            deposit: Deposit amount (default: "5000000")
            deposit_denom: Deposit token denomination (default: "uakt")
            version: Deployment version (defaults to timestamp)
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Enable/disable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            import hashlib
            import json
            logger.info(f"Creating deployment with {len(groups)} groups")

            dseq = int(time.time())
            if version is None:
                version_data = {
                    "groups": groups,
                    "timestamp": dseq
                }
                version_json = json.dumps(version_data, sort_keys=True, separators=(',', ':'))
                version = hashlib.sha256(version_json.encode()).hexdigest()

            msg_dict = {
                "@type": "/akash.deployment.v1beta3.MsgCreateDeployment",
                "id": {"owner": wallet.address, "dseq": str(dseq)},
                "version": version,
                "groups": [
                    self._group_spec_to_dict(group_data) for group_data in groups
                ],
                "depositor": wallet.address,
                "deposit": {"denom": deposit_denom, "amount": deposit},
            }

            result = broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
            )

            if result.success:
                result.dseq = dseq
                logger.info(f"Deployment created successfully with DSEQ: {dseq}")

            return result

        except Exception as e:
            logger.error(f"Failed to create deployment: {e}")
            return BroadcastResult("", 1, f"Deployment creation failed: {e}", False)

    def update_deployment(
        self,
        wallet,
        sdl: Dict[str, Any],
        owner: str = None,
        dseq: int = None,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Update deployment with SDL content.

        Args:
            wallet: AkashWallet instance
            sdl: SDL configuration dictionary
            owner: Deployment owner address (defaults to wallet address)
            dseq: Deployment sequence number (required)
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Enable/disable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            if owner is None:
                owner = wallet.address

            if dseq is None:
                raise ValueError("dseq (deployment sequence number) is required")

            version_bytes = self.generate_sdl_version(sdl)
            logger.info(
                f"Updating deployment {dseq} with SDL (version hash: {version_bytes.hex()[:16]}...)"
            )

            msg_dict = self._update_deployment_msg(owner, dseq, version_bytes)

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Failed to update deployment: {e}")
            return BroadcastResult("", 1, f"Deployment update failed: {e}", False)

    def close_deployment(
        self,
        wallet,
        owner: str,
        dseq: int,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Close deployment.

        Args:
            wallet: AkashWallet instance
            owner: Deployment owner address
            dseq: Deployment sequence number
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Enable/disable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Closing deployment {dseq}")

            msg_dict = self._close_deployment_msg(owner, dseq)

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Failed to close deployment: {e}")
            return BroadcastResult("", 1, f"Deployment closure failed: {e}", False)

    def deposit_deployment(
        self,
        wallet,
        owner: str,
        dseq: int,
        amount: str,
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Add funds to deployment deposit account.

        Args:
            wallet: Wallet for signing transactions
            owner: Deployment owner address
            dseq: Deployment sequence number
            amount: Amount to deposit
            denom: Token denomination (default: "uakt")
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Enable/disable gas simulation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            logger.info(f"Depositing {amount} {denom} to deployment {dseq}")

            msg_dict = self._deposit_deployment_msg(
                owner, dseq, amount, denom, wallet.address
            )

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Error depositing to deployment: {e}")
            return BroadcastResult("", 1, f"Deployment deposit failed: {e}", False)

    def close_group(
        self,
        wallet,
        owner: str,
        dseq: int,
        gseq: int,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Close a specific group within a deployment.

        Args:
            wallet: Wallet for signing transactions
            owner: Deployment owner address
            dseq: Deployment sequence number
            gseq: Group sequence number
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Enable/disable gas simulation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            logger.info(f"Closing group {gseq} in deployment {dseq}")

            msg_dict = self._close_group_msg(owner, dseq, gseq)

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Error closing group: {e}")
            return BroadcastResult("", 1, f"Group closure failed: {e}", False)

    def pause_group(
        self,
        wallet,
        owner: str,
        dseq: int,
        gseq: int,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Pause a specific group within a deployment.

        Args:
            wallet: Wallet for signing transactions
            owner: Deployment owner address
            dseq: Deployment sequence number
            gseq: Group sequence number
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Enable/disable gas simulation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            logger.info(f"Pausing group {gseq} in deployment {dseq}")

            msg_dict = self._pause_group_msg(owner, dseq, gseq)

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Error pausing group: {e}")
            return BroadcastResult("", 1, f"Group pause failed: {e}", False)

    def start_group(
        self,
        wallet,
        owner: str,
        dseq: int,
        gseq: int,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Start a specific group within a deployment.

        Args:
            wallet: Wallet for signing transactions
            owner: Deployment owner address
            dseq: Deployment sequence number
            gseq: Group sequence number
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Enable/disable gas simulation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            logger.info(f"Starting group {gseq} in deployment {dseq}")

            msg_dict = self._start_group_msg(owner, dseq, gseq)

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
            )

        except Exception as e:
            logger.error(f"Error starting group: {e}")
            return BroadcastResult("", 1, f"Group start failed: {e}", False)
