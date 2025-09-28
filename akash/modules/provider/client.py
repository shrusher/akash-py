import logging

from .query import ProviderQuery
from .tx import ProviderTx
from .utils import ProviderUtils

logger = logging.getLogger(__name__)


class ProviderClient(ProviderUtils, ProviderQuery, ProviderTx):
    """
    Client for provider operations.

    Manages provider lifecycle including registration, updates,
    and query operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the provider client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized ProviderClient")
