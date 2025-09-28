import logging

from .query import DistributionQuery
from .tx import DistributionTx

logger = logging.getLogger(__name__)


class DistributionClient(DistributionQuery, DistributionTx):
    """
    Client for distribution operations.

    Handles reward withdrawals and commission queries with complete protobuf message construction.
    """

    def __init__(self, akash_client):
        """
        Initialize the distribution client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized DistributionClient")
