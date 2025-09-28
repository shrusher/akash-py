import logging
from typing import Dict, List, Any

from ...tx import BroadcastResult, broadcast_transaction_rpc

logger = logging.getLogger(__name__)


class GovernanceTx:
    """
    Mixin for governance transaction operations.
    """

    def submit_text_proposal(
        self,
        wallet,
        title: str,
        description: str,
        deposit: str = "10000000",
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Submit text proposal using unified broadcasting.

        Args:
            wallet: AkashWallet instance
            title: Proposal title
            description: Proposal description
            deposit: Initial deposit in tokens (minimum 10 AKT on testnet)
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Transaction fee amount (default: "10000")
            gas_limit: Gas limit (default: 200000)
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Submitting text proposal: {title}")

            msg_submit_proposal = {
                "@type": "/cosmos.gov.v1beta1.MsgSubmitProposal",
                "content": {
                    "@type": "/cosmos.gov.v1beta1.TextProposal",
                    "title": title,
                    "description": description,
                },
                "initial_deposit": [{"denom": denom, "amount": deposit}],
                "proposer": wallet.address,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_submit_proposal],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to submit text proposal: {e}")
            return BroadcastResult("", 1, f"Text proposal failed: {e}", False)

    def submit_parameter_change_proposal(
        self,
        wallet,
        title: str,
        description: str,
        changes: List[Dict[str, Any]],
        deposit: str = "64000000",
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Submit parameter change proposal using unified broadcasting.

        Args:
            wallet: AkashWallet instance
            title: Proposal title
            description: Proposal description
            changes: List of parameter changes (each with 'subspace', 'key', 'value')
            deposit: Initial deposit in tokens (minimum 64 AKT on mainnet)
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Transaction fee amount (default: "10000")
            gas_limit: Gas limit (default: 250000)
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Submitting parameter change proposal: {title}")

            msg_submit_proposal = {
                "@type": "/cosmos.gov.v1beta1.MsgSubmitProposal",
                "content": {
                    "@type": "/cosmos.params.v1beta1.ParameterChangeProposal",
                    "title": title,
                    "description": description,
                    "changes": [
                        {
                            "subspace": change.get("subspace", ""),
                            "key": change.get("key", ""),
                            "value": change.get("value", ""),
                        }
                        for change in changes
                    ],
                },
                "initial_deposit": [{"denom": denom, "amount": deposit}],
                "proposer": wallet.address,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_submit_proposal],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to submit parameter change proposal: {e}")
            return BroadcastResult(
                "", 1, f"Parameter change proposal failed: {e}", False
            )

    def submit_software_upgrade_proposal(
        self,
        wallet,
        title: str,
        description: str,
        upgrade_name: str,
        upgrade_height: int,
        upgrade_info: str = "",
        deposit: str = "64000000",
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Submit software upgrade proposal using unified broadcasting.

        Args:
            wallet: AkashWallet instance
            title: Proposal title
            description: Proposal description
            upgrade_name: Name of the software upgrade
            upgrade_height: Block height at which to perform upgrade
            upgrade_info: Additional upgrade information (optional)
            deposit: Initial deposit in tokens (minimum 64 AKT on mainnet)
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Transaction fee amount (default: "10000")
            gas_limit: Gas limit (default: 300000)
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Submitting software upgrade proposal: {title}")

            msg_submit_proposal = {
                "@type": "/cosmos.gov.v1beta1.MsgSubmitProposal",
                "content": {
                    "@type": "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal",
                    "title": title,
                    "description": description,
                    "plan": {
                        "name": upgrade_name,
                        "height": str(upgrade_height),
                        "info": upgrade_info,
                    },
                },
                "initial_deposit": [{"denom": denom, "amount": deposit}],
                "proposer": wallet.address,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_submit_proposal],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to submit software upgrade proposal: {e}")
            return BroadcastResult(
                "", 1, f"Software upgrade proposal failed: {e}", False
            )

    def vote(
        self,
        wallet,
        proposal_id: int,
        option: str,
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Vote on governance proposal.

        Args:
            wallet: AkashWallet instance
            proposal_id: Proposal ID to vote on
            option: Vote option (YES, NO, ABSTAIN, NO_WITH_VETO)
            memo: Transaction memo
            fee_amount: Transaction fee amount (default: "5000")
            gas_limit: Gas limit (default: 200000)
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            vote_options = {"YES": 1, "ABSTAIN": 2, "NO": 3, "NO_WITH_VETO": 4}

            if option.upper() not in vote_options:
                raise ValueError(
                    f"Invalid vote option: {option}. Must be one of: {list(vote_options.keys())}"
                )

            vote_option = vote_options[option.upper()]

            logger.info(f"Voting {option} on proposal {proposal_id}")

            msg_vote = {
                "@type": "/cosmos.gov.v1beta1.MsgVote",
                "proposal_id": str(proposal_id),
                "voter": wallet.address,
                "option": vote_option,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_vote],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"Failed to vote: {e}")
            return BroadcastResult("", 1, f"Vote failed: {e}", False)

    def deposit(
        self,
        wallet,
        proposal_id: int,
        amount: str = "10000000",
        denom: str = "uakt",
        memo: str = "",
        fee_amount: str = None,
        gas_limit: int = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> "BroadcastResult":
        """
        Deposit tokens to governance proposal.

        Args:
            wallet: AkashWallet instance
            proposal_id: Proposal ID to deposit to
            amount: Deposit amount in tokens
            denom: Token denomination
            memo: Transaction memo
            fee_amount: Transaction fee amount (default: "5000")
            gas_limit: Gas limit (default: 200000)
            gas_adjustment: Multiplier for gas estimation (default 1.2)
            use_simulation: Enable gas simulation

        Returns:
            BroadcastResult with transaction details
        """
        try:
            logger.info(f"Depositing {amount} {denom} to proposal {proposal_id}")

            msg_deposit = {
                "@type": "/cosmos.gov.v1beta1.MsgDeposit",
                "proposal_id": str(proposal_id),
                "depositor": wallet.address,
                "amount": [{"denom": denom, "amount": amount}],
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_deposit],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=15,
            )

        except Exception as e:
            logger.error(f"Failed to deposit: {e}")
            return BroadcastResult("", 1, f"Deposit failed: {e}", False)
