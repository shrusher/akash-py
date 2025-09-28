import base64
import logging
import requests
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AkashClient:
    """
    Akash client.

    Client for interacting with Akash Network using RPC endpoints.

    Attributes:
        bank: Client for banking operations
        staking: Client for staking operations
        governance: Client for governance operations
        market: Client for market operations
        deployment: Client for deployment operations
        provider: Client for provider operations
        audit: Client for audit operations
        auth: Client for authentication operations
        authz: Client for authorization operations
        cert: Client for certificate operations
        distribution: Client for distribution (rewards and commission) operations
        escrow: Client for escrow operations
        evidence: Client for evidence operations
        feegrant: Client for fee grant operations
        inflation: Client for inflation operations
        mint: Client for mint operations
        slashing: Client for slashing operations
        discovery: Client for discovery operations
        inventory: Client for inventory management operations
        manifest: Client for manifest management operations
        ibc: Client for IBC (Inter-Blockchain Communication) operations
    """

    def __init__(
        self,
        rpc_endpoint: str = "https://akash-rpc.polkachu.com:443",
        chain_id: str = "akashnet-2",
    ):
        """
        Initialize the Akash client.

        Args:
            rpc_endpoint (str): RPC endpoint URL (default: akashnet-2 mainnet)
            chain_id (str): Chain ID for transactions (default: "akashnet-2")

        Example:
            ```python
            # Mainnet client (default)
            client = AkashClient("https://akash-rpc.polkachu.com:443")

            # Testnet client for development
            client = AkashClient(
                rpc_endpoint="https://rpc.sandbox-01.aksh.pw:443",
                chain_id="sandbox-01"
            )
            ```
        """
        self.rpc_endpoint = rpc_endpoint.rstrip("/")
        self.chain_id = chain_id

        # Initialize sub-clients
        from .modules.audit import AuditClient
        from .modules.auth import AuthClient
        from .modules.authz import AuthzClient
        from .modules.bank import BankClient
        from .modules.cert.client import CertClient
        from .modules.deployment import DeploymentClient
        from .modules.discovery.client import DiscoveryClient
        from .modules.distribution import DistributionClient
        from .modules.escrow import EscrowClient
        from .modules.evidence import EvidenceClient
        from .modules.feegrant import FeegrantClient
        from .modules.governance import GovernanceClient
        from .modules.ibc import IBCClient
        from .modules.inflation import InflationClient
        from .modules.inventory.client import InventoryClient
        from .modules.manifest.client import ManifestClient
        from .modules.market import MarketClient
        from .modules.provider import ProviderClient
        from .modules.slashing import SlashingClient
        from .modules.staking import StakingClient
        from .grpc_client import ProviderGRPCClient

        self.audit = AuditClient(self)
        self.auth = AuthClient(self)
        self.authz = AuthzClient(self)
        self.bank = BankClient(self)
        self.cert = CertClient(self)
        self.deployment = DeploymentClient(self)
        self.discovery = DiscoveryClient(self)
        self.distribution = DistributionClient(self)
        self.escrow = EscrowClient(self)
        self.evidence = EvidenceClient(self)
        self.feegrant = FeegrantClient(self)
        self.governance = GovernanceClient(self)
        self.ibc = IBCClient(self)
        self.inflation = InflationClient(self)
        self.inventory = InventoryClient(self)
        self.manifest = ManifestClient(self)
        self.market = MarketClient(self)
        self.provider = ProviderClient(self)
        self.slashing = SlashingClient(self)
        self.staking = StakingClient(self)
        self.grpc_client = ProviderGRPCClient(self)

        logger.info(f"Initialized AkashClient for {rpc_endpoint} (chain: {chain_id})")

    def rpc_query(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        Perform an RPC query.

        Args:
            method (str): RPC method name
            params (List[Any]): RPC parameters

        Returns:
            Dict[str, Any]: RPC response
        """
        if params is None:
            params = []

        rpc_request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}

        try:
            response = requests.post(
                self.rpc_endpoint,
                json=rpc_request,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            if "error" in result:
                raise Exception(f"RPC error: {result['error']}")

            return result.get("result", {})

        except Exception as e:
            logger.error(f"RPC query failed: {e}")
            raise

    def abci_query(
        self, path: str, data: str = "", prove: bool = False
    ) -> Dict[str, Any]:
        """
        Perform an ABCI query via RPC.

        Args:
            path (str): Query path
            data (str): Query data (hex encoded)
            prove (bool): Include proof in response

        Returns:
            Dict[str, Any]: ABCI query response
        """
        return self.rpc_query("abci_query", [path, data, "0", prove])

    def broadcast_tx_async(self, tx_bytes: bytes) -> Dict[str, Any]:
        """
        Broadcast transaction using broadcast_tx_async.

        Args:
            tx_bytes (bytes): Serialized transaction bytes

        Returns:
            Dict[str, Any]: Broadcast result
        """
        tx_b64 = base64.b64encode(tx_bytes).decode()

        try:
            result = self.rpc_query("broadcast_tx_async", [tx_b64])
            return result

        except Exception as e:
            logger.error(f"Transaction broadcast failed: {e}")
            raise

    def broadcast_tx_sync(self, tx_bytes: bytes) -> Dict[str, Any]:
        """
        Broadcast transaction using broadcast_tx_sync.

        Args:
            tx_bytes (bytes): Serialized transaction bytes

        Returns:
            Dict[str, Any]: Broadcast result
        """
        tx_b64 = base64.b64encode(tx_bytes).decode()

        try:
            result = self.rpc_query("broadcast_tx_sync", [tx_b64])
            return result

        except Exception as e:
            logger.error(f"Transaction broadcast failed: {e}")
            raise

    def health_check(self, timeout: float = 10.0) -> bool:
        """
        Check if the RPC endpoint is healthy.

        Args:
            timeout (float): Timeout in seconds

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.rpc_endpoint}/health", timeout=timeout)
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def get_network_status(self) -> Dict[str, Any]:
        """
        Get network status information.

        Returns:
            Dict[str, Any]: Network status
        """
        try:
            result = self.rpc_query("status")
            node_info = result.get("node_info", {})
            sync_info = result.get("sync_info", {})

            return {
                "network": node_info.get("network", ""),
                "chain_id": sync_info.get("chain_id", ""),
                "latest_block_height": sync_info.get("latest_block_height", "0"),
                "node_version": node_info.get("version", ""),
                "catching_up": sync_info.get("catching_up", True),
            }

        except Exception as e:
            logger.error(f"Failed to get network status: {e}")
            raise

    def get_balance(self, address: str, denom: str = "uakt") -> str:
        """Get account balance - delegates to BankClient."""
        return self.bank.get_balance(address, denom)

    def get_balances(self, address: str) -> Dict[str, str]:
        """Get all balances for an address - delegates to BankClient."""
        return self.bank.get_all_balances(address)

    def get_validators(self) -> List[Dict[str, Any]]:
        """Get validators list."""
        return self.staking.get_validators()

    def get_proposals(self) -> List[Dict[str, Any]]:
        """Get governance proposals."""
        return self.governance.get_proposals()

    def get_staking_params(self) -> Dict[str, Any]:
        """Get staking module parameters."""
        return self.staking.get_staking_params()

    def get_governance_params(self) -> Dict[str, Any]:
        """Get governance module parameters."""
        return self.governance.get_governance_params()

    def get_account_info(self, address: str) -> Dict[str, Any]:
        """Get account information - delegates to AuthClient."""
        account_info = self.auth.get_account_info(address)
        if account_info:
            return account_info
        else:
            return {"address": address, "account_number": 0, "sequence": 0}

    def get_delegations(self, delegator_address: str) -> List[Dict[str, Any]]:
        """Get delegations for an address."""
        return self.staking.get_delegations(delegator_address)

    def get_provider_endpoint(self, provider_address: str) -> str:
        """
        Fetch provider's gRPC endpoint from on-chain data.

        Args:
            provider_address: Provider's Akash address.

        Returns:
            str: Provider's gRPC endpoint (e.g., 'provider.example.com:8443').
        """
        try:

            def format_host_uri(host_uri: str) -> str:
                if not host_uri:
                    raise ValueError(f"No host_uri for provider {provider_address}")

                if host_uri.startswith("http://") or host_uri.startswith("https://"):
                    from urllib.parse import urlparse

                    parsed = urlparse(host_uri)
                    host = parsed.hostname
                    port = parsed.port or 8443
                    return f"{host}:{port}"
                else:
                    if ":" not in host_uri:
                        return f"{host_uri}:8443"
                    return host_uri

            try:
                provider = self.provider.get_provider(provider_address)
                if provider and provider.get("host_uri"):
                    return format_host_uri(provider.get("host_uri"))
            except Exception as e:
                logger.debug(f"Direct provider query failed, will search: {e}")

            offset = 0
            limit = 200

            while True:
                providers = self.provider.get_providers(limit=limit, offset=offset)
                if not providers:
                    break

                for provider in providers:
                    if provider.get("owner") == provider_address:
                        return format_host_uri(provider.get("host_uri"))

                if len(providers) < limit:
                    break  # Last page
                offset += limit

            raise ValueError(f"Provider {provider_address} not found")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get provider endpoint: {e}")
            raise ValueError(f"Failed to get provider endpoint: {e}")

    def close(self):
        """Close the client and clean up resources."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
