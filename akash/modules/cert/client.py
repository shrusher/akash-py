import logging

from .query import CertQuery
from .tx import CertTx
from .utils import CertUtils

logger = logging.getLogger(__name__)


class CertClient(CertQuery, CertTx, CertUtils):
    """
    Client for certificate operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the certificate client.

        Args:
            akash_client: Parent AkashClient instance
        """
        super().__init__()
        self.akash_client = akash_client
        logger.info("Initialized CertClient")
