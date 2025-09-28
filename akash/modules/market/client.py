import logging

from .query import MarketQuery
from .tx import MarketTx
from .utils import MarketUtils

logger = logging.getLogger(__name__)


class MarketClient(MarketQuery, MarketTx, MarketUtils):
    """Client for market operations."""

    def __init__(self, akash_client):
        self.akash_client = akash_client
