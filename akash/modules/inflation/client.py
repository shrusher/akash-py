import logging

from .query import InflationQuery

logger = logging.getLogger(__name__)


class InflationClient(InflationQuery):
    """
    Client for mint/inflation operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the inflation client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized InflationClient")
