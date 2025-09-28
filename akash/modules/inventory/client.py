import logging

from .query import InventoryQuery
from .utils import InventoryUtils

logger = logging.getLogger(__name__)


class InventoryClient(InventoryQuery, InventoryUtils):
    """
    Inventory client for resource management and monitoring.
    """

    def __init__(self, client):
        """
        Initialize inventory client with main Akash client.

        Args:
            client: Parent AkashClient instance
        """
        self.client = client
        logger.info("Initialized InventoryClient")
