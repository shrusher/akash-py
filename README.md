# Akash Python SDK

Python SDK for interacting with the Akash Network blockchain and deploying workloads on the decentralized cloud
marketplace.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-akash--py.cosmosrescue.com-blue.svg)](https://akash-py.cosmosrescue.com/)

## Installation

```bash
pip install akash
```

### Prerequisites

- Python 3.8+

## Quick start

### Setup

```python
from akash import AkashClient, AkashWallet

wallet = AkashWallet.from_mnemonic("your twelve word mnemonic phrase here")
print(f"Wallet address: {wallet.address}")

client = AkashClient("https://akash-rpc.polkachu.com:443")
print(f"Connected: {client.health_check()}")
```

### Send tokens

```python
from akash import AkashClient, AkashWallet

client = AkashClient("https://akash-rpc.polkachu.com:443")
wallet = AkashWallet.from_mnemonic("your mnemonic here")

result = client.bank.send(
    wallet=wallet,
    to_address="akash1recipient_address",
    amount="1000000",
    memo=""
)

if result.success:
    print(f"Transfer successful: {result.tx_hash}")
else:
    print(f"Transfer failed: {result.raw_log}")
```

### Vote on governance proposal

```python
from akash import AkashClient, AkashWallet

client = AkashClient("https://akash-rpc.polkachu.com:443")
wallet = AkashWallet.from_mnemonic("your mnemonic here")

result = client.governance.vote(
    wallet=wallet,
    proposal_id=42,
    option="YES"
)

if result.success:
    print(f"Vote successful: {result.tx_hash}")
else:
    print(f"Vote failed: {result.raw_log}")
```

### Deploy application

```python
from akash import AkashClient, AkashWallet
import time

wallet = AkashWallet.from_mnemonic("your mnemonic here")
client = AkashClient("https://akash-rpc.polkachu.com:443")

print("Step 1: Ensuring certificate for mTLS...")
success, cert_pem, key_pem = client.cert.ensure_certificate(wallet)
if not success:
    print("Certificate setup failed")
    exit()

print("Step 2: Creating deployment from SDL...")
sdl = '''
version: "2.0"
services:
  web:
    image: nginx:latest
    expose:
      - port: 80
        as: 80
        to:
          - global: true
profiles:
  compute:
    web:
      resources:
        cpu:
          units: 0.5
        memory:
          size: 128Mi
        storage:
          size: 1Gi
  placement:
    akash:
      attributes:
        host: akash
      pricing:
        web:
          denom: uakt
          amount: 100
deployment:
  web:
    akash:
      profile: web
      count: 1
'''

deployment = client.deployment.create_deployment(
    sdl_yaml=sdl,
    wallet=wallet,
    deposit="500000"
)

if not deployment.success:
    print(f"Deployment failed: {deployment.raw_log}")
    exit()

dseq = deployment.dseq
print(f"Deployment created: DSEQ {dseq}")

print("Step 3: Waiting for bids...")
time.sleep(30)

bids = client.market.get_bids(owner=wallet.address, dseq=dseq)
if not bids:
    print("No bids received")
    exit()

print("Step 4: Selecting best bid and creating lease...")
provider_addresses = [b['bid_id']['provider'] for b in bids]
valid_providers = client.provider.filter_valid_providers(provider_addresses)
if not valid_providers:
    print("No valid providers found")
    exit()

valid_bids = [b for b in bids if b['bid_id']['provider'] in valid_providers]
best_bid = min(valid_bids, key=lambda b: float(b['price']['amount']))
lease = client.market.create_lease_from_bid(wallet, best_bid)

if not lease['success']:
    print(f"Lease failed: {lease['error']}")
    exit()

print(f"Lease created with provider: {lease['provider_endpoint']}")

print("Step 5: Submitting manifest...")
time.sleep(10)

manifest_result = client.manifest.submit_manifest(
    provider_endpoint=lease['provider_endpoint'],
    lease_id=lease['lease_id'],
    sdl_content=sdl,
    cert_pem=cert_pem,
    key_pem=key_pem
)

if manifest_result.get('status') == 'success':
    print("Manifest submitted successfully")
    print("Your nginx application is now running")
else:
    print(f"Manifest submission failed: {manifest_result.get('error')}")
```

### Provider discovery

```python
from akash import AkashClient

client = AkashClient("https://akash-rpc.polkachu.com:443")

all_providers = client.provider.get_providers()
gpu_providers = client.provider.get_providers_by_capabilities(["gpu"])
high_perf_providers = client.provider.get_providers_by_capabilities(["high-performance"])
us_providers = client.provider.get_providers_by_region("us-west")

if all_providers:
    provider_detail = client.provider.get_provider(all_providers[0]['owner'])
    print(f"Provider: {provider_detail['host_uri']}")

print(f"Total: {len(all_providers)}, GPU: {len(gpu_providers)}")
print(f"High performance: {len(high_perf_providers)}, US West: {len(us_providers)}")
```

### Market operations

```python
from akash import AkashClient, AkashWallet

client = AkashClient("https://akash-rpc.polkachu.com:443")
wallet = AkashWallet.from_mnemonic("provider mnemonic here")

bids = client.market.get_bids(state="open", limit=20)
print(f"Found {len(bids)} open bids")

bid = client.market.create_bid(
    wallet=wallet,
    owner="akash1...",
    dseq=123,
    gseq=1,
    oseq=1,
    price="1000"
)

leases = client.market.get_leases(provider=wallet.address)
print(f"Active leases: {len(leases)}")
```

## Core components

### AkashClient

Main entry point for the SDK. Manages RPC connections and provides access to all functionality.

```python
from akash import AkashClient

client = AkashClient("https://akash-rpc.polkachu.com:443")

with AkashClient("https://akash-rpc.polkachu.com:443") as client:
    deployments = client.deployment.get_deployments()
```

### AkashWallet

Handles wallet operations, key management, and transaction signing.

```python
from akash import AkashWallet

wallet = AkashWallet.generate()
print(f"New wallet: {wallet.address}")
print(f"Mnemonic: {wallet.mnemonic}")

wallet = AkashWallet.from_mnemonic("your mnemonic phrase")

wallet = AkashWallet.from_private_key(private_key_bytes)

signed_tx = wallet.sign_transaction(tx_data)
balance = wallet.get_balance()
```

### Sub-clients

The client provides access to all Akash modules:

- **audit**: Provider audit operations
- **auth**: Auth operations
- **authz**: Authz operations
- **bank**: Token transfers and balance queries
- **cert**: Certificate management
- **deployment**: Deployment lifecycle management
- **discovery**: Discovery operations
- **distribution**: Staking rewards distribution
- **escrow**: Escrow account management
- **evidence**: Evidence of misbehavior submission
- **feegrant**: Fee grant operations
- **governance**: Governance proposals and voting
- **ibc**: Inter-blockchain communication
- **inflation**: Inflation parameter queries
- **inventory**: Inventory management
- **manifest**: Deployment manifest operations
- **market**: Bidding and lease operations
- **provider**: Provider discovery and filtering
- **slashing**: Validator slashing operations
- **staking**: Staking operations

## Network endpoints

**Testnet:**

- RPC: `https://rpc.sandbox-01.aksh.pw:443`
- Chain ID: `sandbox-01`

**Mainnet:**

- RPC: `https://akash-rpc.polkachu.com:443`
- Chain ID: `akashnet-2`

## Links

- [This SDK documentation](https://akash-py.cosmosrescue.com/)
- [Akash documentation](https://docs.akash.network/)
- [SDL specification](https://akash.network/docs/getting-started/stack-definition-language)
