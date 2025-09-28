import logging

from .query import EvidenceQuery
from .tx import EvidenceTx
from .utils import EvidenceUtils

logger = logging.getLogger(__name__)


class EvidenceClient(EvidenceQuery, EvidenceTx, EvidenceUtils):
    """
    Client for evidence operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the evidence client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized EvidenceClient")
