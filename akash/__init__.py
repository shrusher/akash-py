"""
Akash Network Python SDK

A Python SDK for interacting with the Akash Network, enabling developers to
perform transactions and queries using RPC endpoints.

Main Components:
- AkashClient: Client for all operations
- AkashWallet: Wallet operations and transaction signing
- AuditClient: Audit operations
- AuthClient: Auth operations
- AuthzClient: Authz operations
- BankClient: Token transfer operations
- CertClient: Certificate operations
- DeploymentClient: Deployment operations
- DiscoveryClient: Discovery operations
- DistributionClient: Distribution operations
- EscrowClient: Escrow operations
- EvidenceClient: Evidence operations
- FeegrantClient: Feegrant operations
- GovernanceClient: Governance operations
- IBCClient: IBC operations
- InflationClient: Inflation operations
- InventoryClient: Inventory operations
- ManifestClient: Manifest operations
- MarketClient: Market operations
- ProviderClient: Provider operations
- Slashing: Slashing operations
- StakingClient: Staking operations

Example:
    ```python
    from akash import AkashClient, AkashWallet

    # Create wallet from mnemonic
    wallet = AkashWallet.from_mnemonic("your mnemonic phrase here")
    client = AkashClient("https://rpc.sandbox-01.aksh.pw:443", "sandbox-01")

    # Send tokens using bank module
    result = client.bank.send(
        wallet=wallet,
        to_address="akash1recipient...",
        amount="1000",
        denom="uakt"
    )
    print(f"Transaction: {result.tx_hash} - Success: {result.success}")
    ```
"""

import os

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

# Version is defined in pyproject.toml
from importlib.metadata import version  # noqa: E402

try:
    __version__ = version("akash")
except Exception:
    # Fallback for development when package isn't installed
    __version__ = "0.2.1-dev"

from .client import AkashClient  # noqa: E402
from .modules.audit import AuditClient  # noqa: E402
from .modules.auth import AuthClient  # noqa: E402
from .modules.authz import AuthzClient  # noqa: E402
from .modules.bank import BankClient  # noqa: E402
from .modules.cert import CertClient  # noqa: E402
from .modules.deployment import DeploymentClient  # noqa: E402
from .modules.discovery import DiscoveryClient  # noqa: E402
from .modules.distribution import DistributionClient  # noqa: E402
from .modules.escrow import EscrowClient  # noqa: E402
from .modules.feegrant import FeegrantClient  # noqa: E402
from .modules.governance import GovernanceClient  # noqa: E402
from .modules.ibc import IBCClient  # noqa: E402
from .modules.inflation import InflationClient  # noqa: E402
from .modules.market import MarketClient  # noqa: E402
from .modules.provider import ProviderClient  # noqa: E402
from .modules.slashing import SlashingClient  # noqa: E402
from .modules.staking import StakingClient  # noqa: E402
from .wallet import AkashWallet  # noqa: E402

__all__ = [
    "AkashClient",
    "AkashWallet",
    "AuditClient",
    "AuthClient",
    "AuthzClient",
    "BankClient",
    "CertClient",
    "DeploymentClient",
    "DiscoveryClient",
    "DistributionClient",
    "EscrowClient",
    "FeegrantClient",
    "GovernanceClient",
    "IBCClient",
    "InflationClient",
    "MarketClient",
    "ProviderClient",
    "SlashingClient",
    "StakingClient",
]
