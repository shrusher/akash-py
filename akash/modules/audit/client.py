import logging

from .query import AuditQuery
from .tx import AuditTx
from .utils import AuditUtils

logger = logging.getLogger(__name__)


class AuditClient(AuditQuery, AuditTx, AuditUtils):
    """
    Client for audit operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the audit client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized AuditClient")
