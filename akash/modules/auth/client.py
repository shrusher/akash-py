import logging

from .query import AuthQuery
from .utils import AuthUtils

logger = logging.getLogger(__name__)


class AuthClient(AuthQuery, AuthUtils):
    """
    Client for auth operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the auth client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized AuthClient")
