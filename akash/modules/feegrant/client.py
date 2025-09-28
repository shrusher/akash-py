import logging

from .query import FeegrantQuery
from .tx import FeegrantTx
from .utils import FeegrantUtils

logger = logging.getLogger(__name__)


class FeegrantClient(FeegrantQuery, FeegrantTx, FeegrantUtils):
    """
    Client for fee grant operations.

    Handles fee grants and allowance queries with complete protobuf message construction.
    """

    def __init__(self, akash_client):
        """
        Initialize the feegrant client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized FeegrantClient")
