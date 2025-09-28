import logging

from .query import DiscoveryQuery
from .utils import DiscoveryUtils
from ...grpc_client import ProviderGRPCClient

logger = logging.getLogger(__name__)


class DiscoveryClient(DiscoveryQuery, DiscoveryUtils):
    """
    Client for discovering provider resources and status via gRPC.

    Connects to provider endpoints to gather real-time resource availability,
    status information, and capability assessments.
    """

    def __init__(self, akash_client):
        """
        Initialize the discovery client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        self.grpc_client = ProviderGRPCClient(akash_client)
        logger.info("Initialized DiscoveryClient")
