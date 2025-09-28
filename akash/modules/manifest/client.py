import logging

from .query import ManifestQuery
from .utils import ManifestUtils

logger = logging.getLogger(__name__)


class ManifestClient(ManifestQuery, ManifestUtils):
    """Client for manifest operations."""

    def __init__(self, akash_client):
        self.akash_client = akash_client
        logger.info("Initialized ManifestClient")
