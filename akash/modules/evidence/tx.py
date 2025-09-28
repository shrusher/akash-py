import logging
from typing import Dict, Any

from ...tx import BroadcastResult, broadcast_transaction_rpc

logger = logging.getLogger(__name__)


class EvidenceTx:
    """
    Mixin for evidence transaction operations.
    """

    def submit_evidence(
        self,
        wallet,
        evidence_data: Dict[str, Any],
        memo: str = "",
        fee_amount: str = "5000",
        gas_limit: int = 200000,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Submit evidence of validator misbehavior.

        Args:
            wallet: Wallet to sign the transaction
            evidence_data: Evidence data including type and details
            memo: Transaction memo
            fee_amount: Fee amount in uakt
            gas_limit: Gas limit override
            gas_adjustment: Multiplier for gas estimation
            use_simulation: Whether to simulate for gas estimation

        Returns:
            BroadcastResult: Transaction result
        """
        try:
            logger.info(f"Submitting evidence from {wallet.address}")

            validation = self.validate_evidence_format(evidence_data)
            if not validation["valid"]:
                logger.error(f"Invalid evidence format: {validation['errors']}")
                return BroadcastResult(
                    "", 1, f"Invalid evidence format: {validation['errors']}", False
                )

            content = evidence_data.get("content", "")

            if isinstance(content, str):
                content = content.encode("utf-8")

            msg_submit = {
                "@type": "/cosmos.evidence.v1beta1.MsgSubmitEvidence",
                "submitter": wallet.address,
                "evidence": {
                    "@type": evidence_data.get(
                        "type_url", "/cosmos.evidence.v1beta1.Equivocation"
                    ),
                    "value": content,
                },
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_submit],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=False,
            )

        except Exception as e:
            logger.error(f"Submit evidence failed: {e}")
            raise
