import logging

from .query import StakingQuery
from .tx import StakingTx

logger = logging.getLogger(__name__)


class StakingClient(StakingQuery, StakingTx):
    """
    Client for staking operations.

    """

    def __init__(self, akash_client):
        """
        Initialize the staking client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized StakingClient")
