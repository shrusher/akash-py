import logging

from .query import DeploymentQuery
from .tx import DeploymentTx
from .utils import DeploymentUtils

logger = logging.getLogger(__name__)


class DeploymentClient(DeploymentQuery, DeploymentTx, DeploymentUtils):
    """
    Client for deployment operations.
    """

    def __init__(self, akash_client):
        """
        Initialize the deployment client.

        Args:
            akash_client: Parent AkashClient instance
        """
        self.akash_client = akash_client
        logger.info("Initialized DeploymentClient")
