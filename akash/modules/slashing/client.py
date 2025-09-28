import logging

from .query import SlashingQuery
from .tx import SlashingTx

logger = logging.getLogger(__name__)


class SlashingClient(SlashingQuery, SlashingTx):
    """
    Client for slashing operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the slashing client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized SlashingClient")
