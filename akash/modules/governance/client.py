import logging

from .query import GovernanceQuery
from .tx import GovernanceTx
from .utils import GovernanceUtils

logger = logging.getLogger(__name__)


class GovernanceClient(GovernanceQuery, GovernanceTx, GovernanceUtils):
    """
    Client for governance operations.

    Enables democratic participation in network governance through proposals, voting, and deposits.
    """

    def __init__(self, akash_client):
        """
        Initialize the governance client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized GovernanceClient")
