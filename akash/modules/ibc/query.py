import base64
import logging
import requests
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IBCQuery:
    """
    Mixin for IBC query operations.
    """

    def get_client_state(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Query IBC client state.

        Args:
            client_id: IBC client identifier

        Returns:
            Dict containing client state information or None if not found
        """
        try:
            if not client_id or not isinstance(client_id, str):
                logger.error(f"Invalid client_id: {client_id}")
                return None

            from akash.proto.ibc.core.client.v1 import query_pb2

            request = query_pb2.QueryClientStateRequest()
            request.client_id = client_id

            data = request.SerializeToString().hex()
            result = self.akash_client.abci_query(
                "/ibc.core.client.v1.Query/ClientState", data
            )

            if (
                "response" in result
                and "value" in result["response"]
                and result["response"]["value"]
            ):
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryClientStateResponse()
                response.ParseFromString(response_data)

                client_state_data = {"type_url": response.client_state.type_url}
                if (
                    "/ibc.lightclients.tendermint.v1.ClientState"
                    in response.client_state.type_url
                ):
                    from akash.proto.ibc.lightclients.tendermint.v1 import (
                        tendermint_pb2,
                    )

                    tendermint_state = tendermint_pb2.ClientState()
                    tendermint_state.ParseFromString(response.client_state.value)

                    client_state_data.update(
                        {
                            "chain_id": tendermint_state.chain_id,
                            "trust_level": {
                                "numerator": str(
                                    tendermint_state.trust_level.numerator
                                ),
                                "denominator": str(
                                    tendermint_state.trust_level.denominator
                                ),
                            },
                            "latest_height": {
                                "revision_number": tendermint_state.latest_height.revision_number,
                                "revision_height": tendermint_state.latest_height.revision_height,
                            },
                            "frozen_height": {
                                "revision_number": tendermint_state.frozen_height.revision_number,
                                "revision_height": tendermint_state.frozen_height.revision_height,
                            },
                            "trusting_period": str(
                                tendermint_state.trusting_period.seconds
                            )
                            + "s",
                            "unbonding_period": str(
                                tendermint_state.unbonding_period.seconds
                            )
                            + "s",
                            "max_clock_drift": str(
                                tendermint_state.max_clock_drift.seconds
                            )
                            + "s",
                            "allow_update_after_expiry": tendermint_state.allow_update_after_expiry,
                            "allow_update_after_misbehaviour": tendermint_state.allow_update_after_misbehaviour,
                            "upgrade_path": list(tendermint_state.upgrade_path),
                        }
                    )
                else:
                    client_state_data = response.client_state

                return {
                    "client_state": client_state_data,
                    "proof": response.proof.hex() if response.proof else "",
                    "proof_height": (
                        {
                            "revision_number": response.proof_height.revision_number,
                            "revision_height": response.proof_height.revision_height,
                        }
                        if response.proof_height
                        else {}
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to query client state: {e}")

        return None

    def get_client_status(self, client_id: str) -> str:
        """
        Query IBC client status (Active, Expired, or Frozen).

        Args:
            client_id: The client identifier to check status for

        Returns:
            String status: "Active", "Expired", "Frozen", or "Unknown"
        """
        try:
            from akash.proto.ibc.core.client.v1 import query_pb2

            request = query_pb2.QueryClientStatusRequest()
            request.client_id = client_id

            query_data = request.SerializeToString()
            result = self.akash_client.rpc_query(
                "abci_query",
                [
                    "/ibc.core.client.v1.Query/ClientStatus",
                    query_data.hex().upper(),
                    "0",
                    False,
                ],
            )

            if (
                result
                and "response" in result
                and result["response"].get("code", 0) == 0
            ):
                from akash.proto.ibc.core.client.v1 import query_pb2
                import base64

                response = query_pb2.QueryClientStatusResponse()
                response.ParseFromString(base64.b64decode(result["response"]["value"]))

                return response.status
            else:
                logger.warning(f"Failed to get status for client {client_id}: {result}")
                return "Unknown"

        except Exception as e:
            logger.error(f"Failed to query client status for {client_id}: {e}")
            return "Unknown"

    def get_client_states(
        self,
        limit: Optional[int] = None,
        next_key: Optional[str] = None,
        timeout_minutes: int = 3,
        rest_endpoint: str = "https://rest.cosmos.directory/akash",
    ) -> Dict[str, Any]:
        """
        Query IBC client states using REST API (RPC pagination is mental).

        If next_key is None, iterates through ALL pages until completion.
        If next_key is provided, returns single page results.

        Args:
            limit: Maximum number of client states to return per page (default: 5000)
            next_key: Pagination key from previous request (None = get all clients)
            timeout_minutes: Maximum time to wait for completion (default: 3 minutes)
            rest_endpoint: REST API endpoint (default: cosmos.directory)

        Returns:
            Dict with client_states, next_key, and pagination info
        """
        if next_key is not None:
            return self._query_client_states_rest(
                limit=limit, next_key=next_key, rest_endpoint=rest_endpoint
            )

        if limit is not None:
            return self._query_client_states_rest(
                limit=limit, next_key=None, rest_endpoint=rest_endpoint
            )

        import time

        logger.warning("query_client_states: Querying ALL clients may take 2-3 minutes")
        start_time = time.time()

        all_client_states = []
        current_next_key = None
        page = 0
        max_pages = 200  # Safety limit

        while page < max_pages:
            try:
                result = self._query_client_states_rest(
                    limit=limit, next_key=current_next_key, rest_endpoint=rest_endpoint
                )
                page_states = result.get("client_states", [])
                current_next_key = result.get("next_key", None)

                if page_states:
                    all_client_states.extend(page_states)

                elapsed = time.time() - start_time
                logger.info(
                    f"Page {page + 1}: Got {len(page_states)} clients, total: {len(all_client_states)} (elapsed: {elapsed:.1f}s)"
                )

                if elapsed > (timeout_minutes * 60):
                    logger.warning(
                        f"Query timeout after {timeout_minutes} minutes, returning {len(all_client_states)} clients"
                    )
                    break

                if not current_next_key:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Completed pagination - found {len(all_client_states)} total clients in {elapsed:.1f}s"
                    )
                    break

                page += 1
                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.error(f"Failed to query client states page {page + 1}: {e}")
                break

        return {
            "client_states": all_client_states,
            "next_key": None,
            "total": len(all_client_states),
        }

    def _query_client_states_rest(
        self,
        limit: Optional[int] = None,
        next_key: Optional[str] = None,
        rest_endpoint: str = "https://rest.cosmos.directory/akash",
    ) -> Dict[str, Any]:
        """
        Query IBC client states using REST API.

        Args:
            limit: Maximum number of client states to return (default: 5000)
            next_key: Pagination key from previous request
            rest_endpoint: REST API endpoint (default: cosmos.directory)

        Returns:
            Dict with client_states, next_key, and pagination info
        """
        try:
            actual_limit = limit if limit is not None else 5000

            url = f"{rest_endpoint}/ibc/core/client/v1/client_states?pagination.limit={actual_limit}"

            if next_key:
                import urllib.parse

                encoded_key = urllib.parse.quote(next_key, safe="")
                url += f"&pagination.key={encoded_key}"

            logger.debug(f"REST API query: {url}")

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()

            client_states = []
            if "client_states" in data:
                for cs in data["client_states"]:
                    client_states.append(
                        {
                            "client_id": cs.get("client_id", ""),
                            "client_state": cs.get("client_state", {}),
                        }
                    )

            pagination = data.get("pagination", {})
            next_key = pagination.get("next_key", None)
            total = pagination.get("total", None)

            logger.info(
                f"REST API returned {len(client_states)} client states, next_key: {'Yes' if next_key else 'No'}"
            )

            return {
                "client_states": client_states,
                "next_key": next_key,
                "total": total,
            }

        except Exception as e:
            logger.error(f"REST API query failed: {e}")
            return {"client_states": [], "next_key": None, "total": None}

    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Query IBC connection.

        Args:
            connection_id: IBC connection identifier

        Returns:
            Dict containing connection information or None if not found
        """
        try:
            from akash.proto.ibc.core.connection.v1 import query_pb2

            request = query_pb2.QueryConnectionRequest()
            request.connection_id = connection_id

            data = request.SerializeToString().hex()
            result = self.akash_client.abci_query(
                "/ibc.core.connection.v1.Query/Connection", data
            )

            if "response" in result and "value" in result["response"]:
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryConnectionResponse()
                response.ParseFromString(response_data)

                return {
                    "connection": {
                        "client_id": response.connection.client_id,
                        "state": response.connection.state,
                        "counterparty": (
                            {
                                "client_id": response.connection.counterparty.client_id,
                                "connection_id": response.connection.counterparty.connection_id,
                                "prefix": response.connection.counterparty.prefix,
                            }
                            if response.connection.counterparty
                            else {}
                        ),
                        "delay_period": response.connection.delay_period,
                    },
                    "proof": response.proof.hex() if response.proof else "",
                    "proof_height": (
                        {
                            "revision_number": response.proof_height.revision_number,
                            "revision_height": response.proof_height.revision_height,
                        }
                        if response.proof_height
                        else {}
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to query connection: {e}")

        return None

    def get_connections(
        self,
        limit: Optional[int] = None,
        next_key: Optional[str] = None,
        timeout_minutes: int = 3,
        rest_endpoint: str = "https://rest.cosmos.directory/akash",
    ) -> Dict[str, Any]:
        """
        Query IBC connections using REST API (RPC pagination is mental).

        If next_key is None, iterates through ALL pages until completion.
        If next_key is provided, returns single page results.

        Args:
            limit: Maximum number of connections to return per page (default: 5000)
            next_key: Pagination key from previous request (None = get all connections)
            timeout_minutes: Maximum time to wait for completion (default: 3 minutes)
            rest_endpoint: REST API endpoint (default: cosmos.directory)

        Returns:
            Dict with connections, next_key, and pagination info
        """
        if next_key is not None:
            return self._query_connections_rest(
                limit=limit, next_key=next_key, rest_endpoint=rest_endpoint
            )

        if limit is not None:
            return self._query_connections_rest(
                limit=limit, next_key=None, rest_endpoint=rest_endpoint
            )

        import time

        logger.warning(
            "query_connections: Querying ALL connections may take 2-3 minutes"
        )
        start_time = time.time()

        all_connections = []
        current_next_key = None
        page = 0
        max_pages = 200  # Safety limit

        while page < max_pages:
            try:
                result = self._query_connections_rest(
                    limit=limit, next_key=current_next_key, rest_endpoint=rest_endpoint
                )
                page_connections = result.get("connections", [])
                current_next_key = result.get("next_key", None)

                if page_connections:
                    all_connections.extend(page_connections)

                elapsed = time.time() - start_time
                logger.info(
                    f"Page {page + 1}: Got {len(page_connections)} connections, total: {len(all_connections)} (elapsed: {elapsed:.1f}s)"
                )

                if elapsed > (timeout_minutes * 60):
                    logger.warning(
                        f"Query timeout after {timeout_minutes} minutes, returning {len(all_connections)} connections"
                    )
                    break

                if not current_next_key:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Completed pagination - found {len(all_connections)} total connections in {elapsed:.1f}s"
                    )
                    break

                page += 1
                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.error(f"Failed to query connections page {page + 1}: {e}")
                break

        return {
            "connections": all_connections,
            "next_key": None,
            "total": len(all_connections),
        }

    def _query_connections_rest(
        self,
        limit: Optional[int] = None,
        next_key: Optional[str] = None,
        rest_endpoint: str = "https://rest.cosmos.directory/akash",
    ) -> Dict[str, Any]:
        """
        Query IBC connections using REST API.

        Args:
            limit: Maximum number of connections to return (default: 5000)
            next_key: Pagination key from previous request
            rest_endpoint: REST API endpoint (default: cosmos.directory)

        Returns:
            Dict with connections, next_key, and pagination info
        """
        try:
            actual_limit = limit if limit is not None else 5000

            url = f"{rest_endpoint}/ibc/core/connection/v1/connections?pagination.limit={actual_limit}"

            if next_key:
                import urllib.parse

                encoded_key = urllib.parse.quote(next_key, safe="")
                url += f"&pagination.key={encoded_key}"

            logger.debug(f"REST API query: {url}")

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()

            connections = []
            if "connections" in data:
                for conn in data["connections"]:
                    connections.append(
                        {
                            "id": conn.get("id", ""),
                            "client_id": conn.get("client_id", ""),
                            "state": conn.get("state", ""),
                            "counterparty": conn.get("counterparty", {}),
                            "delay_period": conn.get("delay_period", "0"),
                            "versions": conn.get("versions", []),
                        }
                    )

            pagination = data.get("pagination", {})
            next_key = pagination.get("next_key", None)
            total = pagination.get("total", None)

            logger.info(
                f"REST API returned {len(connections)} connections, next_key: {'Yes' if next_key else 'No'}"
            )

            return {"connections": connections, "next_key": next_key, "total": total}

        except Exception as e:
            logger.error(f"REST API query failed: {e}")
            return {"connections": [], "next_key": None, "total": None}

    def get_channel(self, port_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Query IBC channel.

        Args:
            port_id: Port identifier
            channel_id: Channel identifier

        Returns:
            Dict containing channel information or None if not found
        """
        try:
            from akash.proto.ibc.core.channel.v1 import query_pb2

            request = query_pb2.QueryChannelRequest()
            request.port_id = port_id
            request.channel_id = channel_id

            data = request.SerializeToString().hex()
            result = self.akash_client.abci_query(
                "/ibc.core.channel.v1.Query/Channel", data
            )

            if "response" in result and "value" in result["response"]:
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryChannelResponse()
                response.ParseFromString(response_data)

                return {
                    "channel": {
                        "state": response.channel.state,
                        "ordering": response.channel.ordering,
                        "counterparty": (
                            {
                                "port_id": response.channel.counterparty.port_id,
                                "channel_id": response.channel.counterparty.channel_id,
                            }
                            if response.channel.counterparty
                            else {}
                        ),
                        "connection_hops": list(response.channel.connection_hops),
                        "version": response.channel.version,
                    },
                    "proof": response.proof.hex() if response.proof else "",
                    "proof_height": (
                        {
                            "revision_number": response.proof_height.revision_number,
                            "revision_height": response.proof_height.revision_height,
                        }
                        if response.proof_height
                        else {}
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to query channel: {e}")

        return None

    def get_denom_trace(self, hash: str) -> Optional[Dict[str, Any]]:
        """
        Query IBC transfer denomination trace.

        Args:
            hash: Denomination hash

        Returns:
            Dict containing denomination trace or None if not found
        """
        try:
            from akash.proto.ibc.applications.transfer.v1 import query_pb2

            request = query_pb2.QueryDenomTraceRequest()
            request.hash = hash

            data = request.SerializeToString().hex()
            result = self.akash_client.abci_query(
                "/ibc.applications.transfer.v1.Query/DenomTrace", data
            )

            if "response" in result and "value" in result["response"]:
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryDenomTraceResponse()
                response.ParseFromString(response_data)

                return {
                    "denom_trace": (
                        {
                            "path": response.denom_trace.path,
                            "base_denom": response.denom_trace.base_denom,
                        }
                        if response.denom_trace
                        else {}
                    )
                }

        except Exception as e:
            logger.error(f"Failed to query denom trace: {e}")

        return None

    def get_channels(
        self,
        limit: Optional[int] = None,
        next_key: Optional[str] = None,
        timeout_minutes: int = 3,
        rest_endpoint: str = "https://rest.cosmos.directory/akash",
    ) -> Dict[str, Any]:
        """
        Query IBC channels using REST API.

        If next_key is None, iterates through ALL pages until completion.
        If next_key is provided, returns single page results.

        Args:
            limit: Maximum number of channels to return per page (default: 5000)
            next_key: Pagination key from previous request (None = get all channels)
            timeout_minutes: Maximum time to wait for completion (default: 3 minutes)
            rest_endpoint: REST API endpoint (default: cosmos.directory)

        Returns:
            Dict with channels, next_key, and pagination info
        """
        if next_key is not None:
            return self._query_channels_rest(
                limit=limit, next_key=next_key, rest_endpoint=rest_endpoint
            )

        if limit is not None:
            return self._query_channels_rest(
                limit=limit, next_key=None, rest_endpoint=rest_endpoint
            )

        import time

        logger.warning("query_channels: Querying ALL channels may take 2-3 minutes")
        start_time = time.time()

        all_channels = []
        current_next_key = None
        page = 0
        max_pages = 200  # Safety limit

        while page < max_pages:
            try:
                result = self._query_channels_rest(
                    limit=limit, next_key=current_next_key, rest_endpoint=rest_endpoint
                )
                page_channels = result.get("channels", [])
                current_next_key = result.get("next_key", None)

                if page_channels:
                    all_channels.extend(page_channels)

                elapsed = time.time() - start_time
                logger.info(
                    f"Page {page + 1}: Got {len(page_channels)} channels, total: {len(all_channels)} (elapsed: {elapsed:.1f}s)"
                )

                if elapsed > (timeout_minutes * 60):
                    logger.warning(
                        f"Query timeout after {timeout_minutes} minutes, returning {len(all_channels)} channels"
                    )
                    break

                if not current_next_key:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Completed pagination - found {len(all_channels)} total channels in {elapsed:.1f}s"
                    )
                    break

                page += 1
                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.error(f"Failed to query channels page {page + 1}: {e}")
                break

        return {"channels": all_channels, "next_key": None, "total": len(all_channels)}

    def _query_channels_rest(
        self,
        limit: Optional[int] = None,
        next_key: Optional[str] = None,
        rest_endpoint: str = "https://rest.cosmos.directory/akash",
    ) -> Dict[str, Any]:
        """
        Query IBC channels using REST API.

        Args:
            limit: Maximum number of channels to return (default: 5000)
            next_key: Pagination key from previous request
            rest_endpoint: REST API endpoint (default: cosmos.directory)

        Returns:
            Dict with channels, next_key, and pagination info
        """
        try:
            actual_limit = limit if limit is not None else 5000

            url = f"{rest_endpoint}/ibc/core/channel/v1/channels?pagination.limit={actual_limit}"

            if next_key:
                import urllib.parse

                encoded_key = urllib.parse.quote(next_key, safe="")
                url += f"&pagination.key={encoded_key}"

            logger.debug(f"REST API query: {url}")

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()

            channels = []
            if "channels" in data:
                for ch in data["channels"]:
                    channels.append(
                        {
                            "state": ch.get("state", ""),
                            "ordering": ch.get("ordering", ""),
                            "counterparty": ch.get("counterparty", {}),
                            "connection_hops": ch.get("connection_hops", []),
                            "version": ch.get("version", ""),
                            "port_id": ch.get("port_id", ""),
                            "channel_id": ch.get("channel_id", ""),
                        }
                    )

            pagination = data.get("pagination", {})
            next_key = pagination.get("next_key", None)
            total = pagination.get("total", None)

            logger.info(
                f"REST API returned {len(channels)} channels, next_key: {'Yes' if next_key else 'No'}"
            )

            return {"channels": channels, "next_key": next_key, "total": total}

        except Exception as e:
            logger.error(f"REST API query failed: {e}")
            return {"channels": [], "next_key": None, "total": None}

    def find_active_clients_for_chain(
        self, chain_id: str, max_results: int = 10
    ) -> List[str]:
        """
        Find active IBC clients for a specific chain.

        Args:
            chain_id: Target chain ID (e.g., 'cosmoshub-4')
            max_results: Maximum number of active clients to return

        Returns:
            List of active client IDs for the chain
        """
        try:
            logger.info(f"Finding active clients for chain: {chain_id}")
            active_clients = []
            matching_clients = []

            current_next_key = None

            while True:
                result = self._query_client_states_rest(
                    limit=1000, next_key=current_next_key
                )
                client_states = result.get("client_states", [])

                for client_info in client_states:
                    client_id = client_info.get("client_id", "")
                    client_state = client_info.get("client_state", {})

                    if (
                        isinstance(client_state, dict)
                        and client_state.get("chain_id") == chain_id
                    ):
                        matching_clients.append(client_id)
                        logger.debug(f"Found client {client_id} for chain {chain_id}")

                current_next_key = result.get("next_key")

                if not current_next_key:
                    break

            logger.info(
                f"Found {len(matching_clients)} clients for {chain_id}, checking status..."
            )

            for client_id in matching_clients:
                if len(active_clients) >= max_results:
                    break

                try:
                    status = self.get_client_status(client_id)
                    if status == "Active":
                        active_clients.append(client_id)
                        logger.info(f"Found active client: {client_id}")
                except Exception as e:
                    logger.debug(f"Error checking status for {client_id}: {e}")
                    continue

            logger.info(f"Found {len(active_clients)} active clients for {chain_id}")
            return active_clients

        except Exception as e:
            logger.error(f"Error finding active clients for {chain_id}: {e}")
            return []

    def find_active_channels_for_chain(
        self, chain_id: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find active IBC channels for a specific chain.

        Args:
            chain_id: Target chain ID (e.g., 'cosmoshub-4')
            max_results: Maximum number of active channels to return

        Returns:
            List of active channel info dicts for the chain
        """
        try:
            logger.info(f"Finding active channels for chain: {chain_id}")
            active_channels = []

            active_clients = self.find_active_clients_for_chain(
                chain_id, max_results=20
            )
            if not active_clients:
                logger.warning(f"No active clients found for {chain_id}")
                return []

            logger.info(f"Found {len(active_clients)} active clients: {active_clients}")

            all_connections = []
            current_next_key = None

            while True:
                connections_result = self._query_connections_rest(
                    limit=1000, next_key=current_next_key
                )
                page_connections = connections_result.get("connections", [])
                all_connections.extend(page_connections)

                current_next_key = connections_result.get("next_key")
                if not current_next_key:
                    break

            active_connections = []
            for conn in all_connections:
                if (
                    conn.get("client_id") in active_clients
                    and conn.get("state") == "STATE_OPEN"
                ):
                    active_connections.append(conn.get("id", ""))

            logger.info(
                f"Found {len(active_connections)} active connections from {len(all_connections)} total"
            )

            if not active_connections:
                return []

            all_channels = []
            current_next_key = None

            while True:
                channels_result = self._query_channels_rest(
                    limit=1000, next_key=current_next_key
                )
                page_channels = channels_result.get("channels", [])
                all_channels.extend(page_channels)

                current_next_key = channels_result.get("next_key")
                if not current_next_key:
                    break

            for channel in all_channels:
                if (
                    channel.get("state") == "STATE_OPEN"
                    and channel.get("port_id") == "transfer"
                    and any(
                        conn_id in active_connections
                        for conn_id in channel.get("connection_hops", [])
                    )
                ):

                    connection_id = None
                    for conn_hop in channel.get("connection_hops", []):
                        if conn_hop in active_connections:
                            connection_id = conn_hop
                            break

                    active_channels.append(
                        {
                            "channel_id": channel.get("channel_id", ""),
                            "port_id": channel.get("port_id", ""),
                            "connection_id": connection_id,
                            "state": channel.get("state", ""),
                            "counterparty": channel.get("counterparty", {}),
                        }
                    )

                    if len(active_channels) >= max_results:
                        break

            logger.info(
                f"Found {len(active_channels)} active channels for {chain_id} from {len(all_channels)} total"
            )
            return active_channels

        except Exception as e:
            logger.error(f"Error finding active channels for {chain_id}: {e}")
            return []

    def _query_all_connections(self) -> List[Dict[str, Any]]:
        """
        Query all IBC connections (internal helper).

        Returns:
            List of connection information
        """
        try:
            from akash.proto.ibc.core.connection.v1 import query_pb2

            request = query_pb2.QueryConnectionsRequest()
            data = request.SerializeToString().hex()
            result = self.akash_client.abci_query(
                "/ibc.core.connection.v1.Query/Connections", data
            )

            if "response" in result and "value" in result["response"]:
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryConnectionsResponse()
                response.ParseFromString(response_data)

                connections = []
                for identified_connection in response.connections:
                    connections.append(
                        {
                            "connection_id": identified_connection.id,
                            "client_id": identified_connection.connection.client_id,
                            "state": identified_connection.connection.state,
                            "counterparty": (
                                {
                                    "client_id": identified_connection.connection.counterparty.client_id,
                                    "connection_id": identified_connection.connection.counterparty.connection_id,
                                }
                                if identified_connection.connection.counterparty
                                else {}
                            ),
                            "delay_period": identified_connection.connection.delay_period,
                        }
                    )

                return connections

        except Exception as e:
            logger.error(f"Failed to query all connections: {e}")

        return []

    def get_transfer_params(self) -> Dict[str, Any]:
        """
        Query IBC transfer module parameters.

        Returns:
            Transfer parameters with send_enabled and receive_enabled flags
        """
        try:
            from akash.proto.ibc.applications.transfer.v1 import query_pb2

            request = query_pb2.QueryParamsRequest()
            data = request.SerializeToString().hex()
            result = self.akash_client.abci_query(
                "/ibc.applications.transfer.v1.Query/Params", data
            )

            if "response" in result and "value" in result["response"]:
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryParamsResponse()
                response.ParseFromString(response_data)

                return {
                    "send_enabled": response.params.send_enabled,
                    "receive_enabled": response.params.receive_enabled,
                }

        except Exception as e:
            logger.error(f"Failed to query transfer params: {e}")

        return {}

    def trace_ibc_token(self, ibc_denom: str) -> Optional[Dict[str, Any]]:
        """
        Trace an IBC token to its origin.

        Args:
            ibc_denom: IBC denomination to trace

        Returns:
            Token trace information or None
        """
        if not ibc_denom.startswith("ibc/"):
            return {"is_ibc": False, "base_denom": ibc_denom}

        hash_part = ibc_denom[4:]
        if not hash_part:
            return {"is_ibc": False, "base_denom": ibc_denom}

        trace = self.get_denom_trace(hash_part)
        if trace and trace["denom_trace"]:
            return {
                "is_ibc": True,
                "path": trace["denom_trace"]["path"],
                "base_denom": trace["denom_trace"]["base_denom"],
                "hash": hash_part,
            }

        return None
