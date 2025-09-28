import logging
from typing import Dict, Optional

from ...tx import BroadcastResult, broadcast_transaction_rpc

logger = logging.getLogger(__name__)


class IBCTx:
    """IBC transaction operations mixin class."""

    def transfer(
        self,
        wallet,
        source_channel: str,
        token_amount: str,
        token_denom: str,
        receiver: str,
        source_port: str = "transfer",
        timeout_height: Optional[Dict[str, int]] = None,
        timeout_timestamp: Optional[int] = None,
        memo: str = "",
        fee_amount: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Transfer tokens via IBC.

        Args:
            wallet: Wallet instance for signing
            source_channel: Source channel ID
            token_amount: Amount to transfer
            token_denom: Token denomination
            receiver: Recipient address on destination chain
            source_port: Source port (defaults to "transfer")
            timeout_height: Optional timeout height {"revision_number": int, "revision_height": int}
            timeout_timestamp: Optional timeout timestamp (nanoseconds)
            memo: Optional memo
            fee_amount: Optional fee amount (defaults to calculated amount)
            gas_limit: Optional gas limit
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Whether to simulate before broadcasting

        Returns:
            BroadcastResult with transaction details
        """
        try:
            import time

            if timeout_timestamp is None:
                timeout_timestamp = int(time.time() + 600) * 1_000_000_000

            if timeout_height is None:
                try:
                    channel_info = self.get_channel(source_port, source_channel)
                    revision_number = 0

                    if channel_info and "channel" in channel_info:
                        channel = channel_info["channel"]
                        connection_hops = channel.get("connection_hops", [])
                        if connection_hops:
                            connection_id = connection_hops[0]
                            conn_info = self.get_connection(connection_id)
                            if conn_info and "connection" in conn_info:
                                client_id = (
                                    conn_info["connection"]
                                    .get("counterparty", {})
                                    .get("client_id", "")
                                )
                                if client_id:  # Only query if client_id is not empty
                                    try:
                                        client_state = self.get_client_state(client_id)
                                        if (
                                            client_state
                                            and "client_state" in client_state
                                        ):
                                            chain_id = client_state["client_state"].get(
                                                "chain_id", ""
                                            )
                                            if "-" in chain_id:
                                                try:
                                                    revision_number = int(
                                                        chain_id.split("-")[-1]
                                                    )
                                                except ValueError:
                                                    pass
                                    except Exception:
                                        pass

                    timeout_height = {
                        "revision_number": revision_number,
                        "revision_height": 0,
                    }

                except Exception as e:
                    logger.warning(
                        f"Could not determine target chain revision number: {e}"
                    )
                    timeout_height = {"revision_number": 0, "revision_height": 0}

            msg_dict = {
                "@type": "/ibc.applications.transfer.v1.MsgTransfer",
                "source_port": source_port,
                "source_channel": source_channel,
                "token": {"denom": token_denom, "amount": str(token_amount)},
                "sender": wallet.address,
                "receiver": receiver,
                "timeout_height": {
                    "revision_number": str(timeout_height["revision_number"]),
                    "revision_height": str(timeout_height["revision_height"]),
                },
                "timeout_timestamp": str(timeout_timestamp),
                "memo": memo,
            }

            return broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

        except Exception as e:
            logger.error(f"IBC transfer failed: {e}")
            return BroadcastResult("", 1, f"IBC transfer failed: {e}", False)

    def create_client(
        self,
        wallet,
        target_chain_id: str,
        target_rpc_url: str,
        trusting_period_seconds: int = 1209600,  # 14 days default
        unbonding_period_seconds: int = 1814400,  # 21 days default
        max_clock_drift_seconds: int = 600,  # 10 minutes default
        memo: str = "",
        fee_amount: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
    ) -> BroadcastResult:
        """
        Create new IBC client for a target chain automatically.

        This method handles all complexity internally:
        - Fetches latest block from target chain
        - Constructs proper client state
        - Creates initial consensus state
        - Broadcasts the create client transaction

        Users only need to provide the target chain ID and RPC URL.

        Args:
            wallet: Wallet instance for signing
            target_chain_id: Target chain ID (e.g., "cosmoshub-4")
            target_rpc_url: Target chain RPC URL (e.g., "https://cosmos-rpc.polkachu.com:443")
            trusting_period_seconds: Trusting period in seconds (default: 14 days)
            unbonding_period_seconds: Unbonding period in seconds (default: 21 days)
            max_clock_drift_seconds: Max clock drift in seconds (default: 10 minutes)
            memo: Optional memo
            fee_amount: Optional fee amount
            gas_limit: Optional gas limit
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Whether to simulate before broadcasting

        Returns:
            BroadcastResult with transaction details including new client ID
        """
        try:
            from akash.modules.ibc.light_client import TendermintLightClient
            import requests
            import base64

            logger.info(f"Creating IBC client for {target_chain_id}")

            logger.info("Fetching latest block from target chain...")
            light_client = TendermintLightClient(target_chain_id, target_rpc_url)
            light_block = light_client.light_block()

            header = light_block.signed_header["header"]
            chain_id_from_block = header["chain_id"]

            if "-" not in chain_id_from_block:
                revision_number = 0
                logger.info(
                    f"Chain ID {chain_id_from_block} doesn't follow IBC revision format, using revision 0"
                )
            else:
                try:
                    revision_number = int(chain_id_from_block.split("-")[-1])
                    logger.info(
                        f"Extracted revision number {revision_number} from chain ID: {chain_id_from_block}"
                    )
                except ValueError:
                    revision_number = 0
                    logger.info(
                        f"Chain ID {chain_id_from_block} last segment not numeric, using revision 0"
                    )

            logger.info("Fetching consensus parameters from target chain...")
            consensus_params_resp = requests.get(
                f"{target_rpc_url}/consensus_params", timeout=10
            )
            if consensus_params_resp.status_code != 200:
                raise ValueError(
                    f"Failed to fetch consensus params: {consensus_params_resp.text}"
                )

            consensus_params = consensus_params_resp.json()["result"]

            def get_proof_specs_from_consensus_params(consensus_params):
                try:
                    block_params = consensus_params.get("consensus_params", {}).get(
                        "block", {}
                    )
                    max_bytes = int(block_params.get("max_bytes", "22020096"))
                    int(block_params.get("max_gas", "-1"))

                    evidence_params = consensus_params.get("consensus_params", {}).get(
                        "evidence", {}
                    )
                    max_age_num_blocks = int(
                        evidence_params.get("max_age_num_blocks", "100000")
                    )

                    child_size = 33 if max_bytes > 1000000 else 32

                    min_prefix_length = 1 if max_age_num_blocks < 50000 else 4
                    max_prefix_length = min_prefix_length + 8

                    proof_specs = [
                        {
                            "leaf_spec": {
                                "hash": "SHA256",
                                "prehash_key": "NO_HASH",
                                "prehash_value": "SHA256",
                                "length": "VAR_PROTO",
                                "prefix": "AA==",
                            },
                            "inner_spec": {
                                "child_order": [0, 1],
                                "child_size": child_size,
                                "min_prefix_length": min_prefix_length,
                                "max_prefix_length": max_prefix_length,
                                "empty_child": None,
                                "hash": "SHA256",
                            },
                            "max_depth": 0,
                            "min_depth": 0,
                            "prehash_key_before_comparison": False,
                        },
                        {
                            "leaf_spec": {
                                "hash": "SHA256",
                                "prehash_key": "NO_HASH",
                                "prehash_value": "SHA256",
                                "length": "VAR_PROTO",
                                "prefix": "AA==",
                            },
                            "inner_spec": {
                                "child_order": [0, 1],
                                "child_size": 32,
                                "min_prefix_length": 1,
                                "max_prefix_length": 1,
                                "empty_child": None,
                                "hash": "SHA256",
                            },
                            "max_depth": 0,
                            "min_depth": 0,
                            "prehash_key_before_comparison": False,
                        },
                    ]

                    logger.info(
                        f"Generated proof specs from consensus params: child_size={child_size}, prefix_lengths={min_prefix_length}-{max_prefix_length}"
                    )
                    return proof_specs

                except Exception as e:
                    logger.warning(
                        f"Failed to extract proof specs from consensus params: {e}"
                    )
                    return [
                        {
                            "leaf_spec": {
                                "hash": "SHA256",
                                "prehash_key": "NO_HASH",
                                "prehash_value": "SHA256",
                                "length": "VAR_PROTO",
                                "prefix": "AA==",
                            },
                            "inner_spec": {
                                "child_order": [0, 1],
                                "child_size": 33,
                                "min_prefix_length": 4,
                                "max_prefix_length": 12,
                                "empty_child": None,
                                "hash": "SHA256",
                            },
                            "max_depth": 0,
                            "min_depth": 0,
                            "prehash_key_before_comparison": False,
                        }
                    ]

            latest_height = {
                "revision_number": str(revision_number),
                "revision_height": str(light_block.height),
            }

            client_state = {
                "@type": "/ibc.lightclients.tendermint.v1.ClientState",
                "chain_id": target_chain_id,
                "trust_level": {"numerator": "1", "denominator": "3"},
                "trusting_period": f"{trusting_period_seconds}s",
                "unbonding_period": f"{unbonding_period_seconds}s",
                "max_clock_drift": f"{max_clock_drift_seconds}s",
                "frozen_height": {"revision_number": "0", "revision_height": "0"},
                "latest_height": latest_height,
                "proof_specs": get_proof_specs_from_consensus_params(consensus_params),
                "upgrade_path": ["upgrade", "upgradedIBCState"],
                "allow_update_after_expiry": True,
                "allow_update_after_misbehaviour": True,
            }

            header = light_block.signed_header["header"]

            app_hash = header.get("app_hash", "")
            if app_hash:
                root_hash = base64.b64encode(bytes.fromhex(app_hash)).decode("ascii")
            else:
                root_hash = ""

            consensus_state = {
                "@type": "/ibc.lightclients.tendermint.v1.ConsensusState",
                "timestamp": header["time"],
                "root": {"hash": root_hash},
                "next_validators_hash": header.get("next_validators_hash", ""),
            }

            logger.info(
                f"Creating IBC client for {target_chain_id} at height {light_block.height}"
            )

            msg_dict = {
                "@type": "/ibc.core.client.v1.MsgCreateClient",
                "client_state": client_state,
                "consensus_state": consensus_state,
                "signer": wallet.address,
            }

            result = broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

            if result.success:
                client_id = result.get_event_attribute("create_client", "client_id")

                if client_id:
                    logger.info(f"IBC client created successfully: {client_id}")
                    custom_result = BroadcastResult(
                        tx_hash=result.tx_hash,
                        code=result.code,
                        raw_log=f"SUCCESS: Created IBC client {client_id} for {target_chain_id}. TX: {result.tx_hash}",
                        success=True,
                        events=result.events,
                    )
                    custom_result.client_id = client_id
                    return custom_result
                else:
                    logger.warning(
                        "IBC client created but could not extract client ID from events"
                    )
                    return BroadcastResult(
                        tx_hash=result.tx_hash,
                        code=result.code,
                        raw_log=f"SUCCESS: Created IBC client for {target_chain_id}. TX: {result.tx_hash}",
                        success=True,
                        events=result.events,
                    )
            else:
                logger.error(f"IBC client creation failed: {result.raw_log}")
                return result

        except Exception as e:
            error_msg = f"IBC client creation failed: {e}"
            logger.error(error_msg)
            return BroadcastResult("", 1, error_msg, False)

    def _fetch_full_validators(self, target_rpc_url: str, height: int) -> tuple:
        """Fetch complete validator set with pagination."""
        import requests

        validators = []
        page = 1
        total_voting_power = 0

        while True:
            endpoint = (
                f"{target_rpc_url}/validators?height={height}&per_page=1000&page={page}"
            )
            response = requests.get(endpoint, timeout=10)
            if response.status_code != 200:
                raise ValueError(
                    f"Failed to get validators page {page}: {response.text}"
                )

            data = response.json()["result"]
            validators.extend(data["validators"])

            if "total" in data:
                total_voting_power = int(data["total"])

            if len(data["validators"]) < 100:
                break

            page += 1
            if page > 50:
                logger.warning(
                    f"Reached page limit {page} while fetching validators - may be incomplete"
                )
                break

        if total_voting_power == 0:
            total_voting_power = sum(int(v["voting_power"]) for v in validators)

        validators = sorted(
            validators, key=lambda x: (-int(x["voting_power"]), x["address"])
        )

        return validators, total_voting_power

    def update_client(
        self,
        wallet,
        client_id: str,
        target_rpc_url: str,
        memo: str = "",
        fee_amount: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_adjustment: float = 1.2,
        use_simulation: bool = True,
        akash_api: str = "https://akash-api.polkachu.com",
    ) -> BroadcastResult:
        """
        Update existing IBC client with latest block header.

        This method handles all the complexity internally:
        - Queries client state to get chain ID and revision number
        - Uses trusting period validation to find safe height pairs
        - Creates light client to fetch block data
        - Constructs and broadcasts the update transaction

        Users only need to provide the client_id and target chain RPC URL.

        Args:
            wallet: Wallet instance for signing
            client_id: Client identifier to update (e.g., "07-tendermint-53")
            target_rpc_url: Target chain RPC URL (e.g., "https://cosmos-rpc.polkachu.com:443")
            memo: Optional memo
            fee_amount: Optional fee amount
            gas_limit: Optional gas limit
            gas_adjustment: Multiplier for simulated gas
            use_simulation: Whether to simulate before broadcasting
            akash_api: Akash API endpoint for client state queries

        Returns:
            BroadcastResult with transaction details
        """
        try:
            from akash.modules.ibc.light_client import TendermintLightClient
            import requests

            logger.info(f"Starting IBC client update for {client_id}")

            logger.info("Fetching client state information...")
            client_state_response = requests.get(
                f"{akash_api}/ibc/core/client/v1/client_states/{client_id}", timeout=10
            )
            if client_state_response.status_code != 200:
                raise ValueError(
                    f"Failed to query client state: {client_state_response.text}"
                )

            client_state_data = client_state_response.json()["client_state"]
            chain_id = client_state_data["chain_id"]

            latest_height = client_state_data.get("latest_height", {})
            revision_number = int(latest_height.get("revision_number", 0))

            logger.info(
                f"Client targets chain: {chain_id} (revision {revision_number})"
            )

            logger.info("Using dynamic height discovery approach")
            light_client = TendermintLightClient(chain_id, target_rpc_url)

            current_client_height = int(latest_height.get("revision_height", 0))
            trusted_height = current_client_height
            trusted_validators_height = trusted_height + 1

            logger.info(f"Using client state height {trusted_height} as trusted height")
            logger.info(
                f"Checking if consensus state exists at {trusted_validators_height}"
            )

            trusted_val_url = f"{akash_api}/ibc/core/client/v1/consensus_states/{client_id}/revision/{revision_number}/height/{trusted_validators_height}"
            trusted_val_response = requests.get(trusted_val_url, timeout=10)

            if trusted_val_response.status_code != 200:
                logger.info(f"Consensus state at {trusted_validators_height} not found")

                heights_url = f"{akash_api}/ibc/core/client/v1/consensus_states/{client_id}/heights"
                heights_response = requests.get(heights_url, timeout=10)

                if heights_response.status_code == 200:
                    heights_data = heights_response.json()
                    available_heights = []
                    for h in heights_data.get("consensus_state_heights", []):
                        available_heights.append(int(h["revision_height"]))

                    available_heights.sort(reverse=True)
                    logger.info(
                        f"Available consensus states: {available_heights[:5]}..."
                    )

                    if trusted_height >= max(available_heights):
                        logger.info("Current client height is latest consensus state")

                        if len(available_heights) >= 2:
                            trusted_height = available_heights[1]
                            trusted_validators_height = trusted_height
                            header_height = available_heights[0]
                            logger.info(
                                f"Using existing consensus state pair: header={header_height}, trusted={trusted_height}"
                            )
                        else:
                            raise ValueError("Not enough consensus states available")
                    else:
                        valid_heights = [
                            h for h in available_heights if h > trusted_height
                        ]
                        if valid_heights:
                            trusted_validators_height = min(valid_heights)
                            logger.info(
                                f"Using closest available consensus state at {trusted_validators_height}"
                            )
                        else:
                            raise ValueError(
                                f"No consensus state found above trusted height {trusted_height}"
                            )
                else:
                    raise ValueError("Could not query consensus state heights")

            if "header_height" not in locals() or header_height is None:
                latest_block = light_client.light_block()
                header_height = latest_block.height
                logger.info(
                    f"Using latest source chain height {header_height} as header height"
                )

                gap = header_height - trusted_height
                logger.info(f"Height gap: {gap} blocks")

                if gap > 10000:
                    logger.info(
                        f"Gap very large ({gap}), using intermediate header height"
                    )
                    header_height = trusted_height + 1000

            logger.info(
                f"Using heights: header={header_height}, trusted={trusted_height}"
            )

            light_block = light_client.light_block(header_height)
            logger.info(
                f"Getting trusted validators from height {trusted_validators_height}"
            )
            trusted_light_block = light_client.light_block(trusted_validators_height)

            logger.info("Successfully fetched light blocks")

            client_message = {
                "@type": "/ibc.lightclients.tendermint.v1.Header",
                "signed_header": light_block.signed_header,
                "validator_set": light_block.validator_set,
                "trusted_height": {
                    "revision_number": revision_number,
                    "revision_height": trusted_height,
                },
                "trusted_validators": trusted_light_block.validator_set,
            }

            msg_dict = {
                "@type": "/ibc.core.client.v1.MsgUpdateClient",
                "client_id": client_id,
                "header": client_message,
                "signer": wallet.address,
            }

            logger.info("Broadcasting IBC client update transaction...")
            result = broadcast_transaction_rpc(
                client=self.akash_client,
                wallet=wallet,
                messages=[msg_dict],
                memo=memo,
                fee_amount=fee_amount,
                gas_limit=gas_limit,
                gas_adjustment=gas_adjustment,
                use_simulation=use_simulation,
                wait_for_confirmation=True,
                confirmation_timeout=30,
            )

            if result.success:
                logger.info(f"IBC client update successful: {result.tx_hash}")
                return BroadcastResult(
                    tx_hash=result.tx_hash,
                    code=result.code,
                    raw_log=f"SUCCESS: IBC client {client_id} updated to height {header_height}. TX: {result.tx_hash}",
                    success=True,
                )
            else:
                logger.error(f"IBC client update failed: {result.raw_log}")
                return result

        except Exception as e:
            error_msg = f"IBC client update failed: {e}"
            logger.error(error_msg)
            return BroadcastResult("", 1, error_msg, False)
