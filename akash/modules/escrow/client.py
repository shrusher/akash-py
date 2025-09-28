import logging

from .query import EscrowQuery

logger = logging.getLogger(__name__)


class EscrowClient(EscrowQuery):
    """
    Client for escrow operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the escrow client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized EscrowClient")
