import logging

from .query import IBCQuery
from .tx import IBCTx
from .utils import IBCUtils

logger = logging.getLogger(__name__)


class IBCClient(IBCQuery, IBCTx, IBCUtils):
    """
    Client for IBC operations.

    Enables cross-chain transfers, client management, and connection operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the IBC client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized IBCClient")
