import logging

from .query import AuthzQuery
from .tx import AuthzTx
from .utils import AuthzUtils

logger = logging.getLogger(__name__)


class AuthzClient(AuthzQuery, AuthzTx, AuthzUtils):
    """
    Client for Authz operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the authz client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        self.client = akash_client
        logger.info("Initialized AuthzClient")
