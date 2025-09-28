import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class GovernanceUtils:
    """
    Mixin for governance utilities.
    """

    def get_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """
        Alias for get_proposal_info() for E2E test compatibility.

        Args:
            proposal_id: Proposal ID

        Returns:
            Proposal information
        """
        return self.get_proposal_info(proposal_id)

    def get_proposal_votes(self, proposal_id: int) -> List[Dict[str, Any]]:
        """
        Alias for get_votes() for E2E test compatibility.

        Args:
            proposal_id: Proposal ID

        Returns:
            List of votes
        """
        return self.get_votes(proposal_id)

    def get_proposal_deposits(self, proposal_id: int) -> List[Dict[str, Any]]:
        """
        Alias for get_deposits() for E2E test compatibility.

        Args:
            proposal_id: Proposal ID

        Returns:
            List of deposits
        """
        return self.get_deposits(proposal_id)
