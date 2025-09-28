import logging

from .query import BankQuery
from .tx import BankTx
from .utils import BankUtils

logger = logging.getLogger(__name__)


class BankClient(BankQuery, BankTx, BankUtils):
    """
    Client for banking operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the bank client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized BankClient")
