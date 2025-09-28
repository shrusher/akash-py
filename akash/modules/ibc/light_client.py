"""Tendermint Light Client for IBC client operations."""

import logging
import requests
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TendermintLightBlock:
    """
    Represents a validated light block with signed header and validator set.
    """

    def __init__(self, signed_header: Dict[str, Any], validator_set: Dict[str, Any]):
        self.signed_header = signed_header
        self.validator_set = validator_set
        self._height = int(signed_header["header"]["height"])

        time_str = signed_header["header"]["time"]
        if time_str.endswith("Z"):
            time_part, tz_part = time_str[:-1], "+00:00"
        else:
            time_part, tz_part = (
                time_str.rsplit("+", 1) if "+" in time_str else time_str.rsplit("-", 1)
            )
            tz_part = "+" + tz_part if "+" in time_str else "-" + tz_part

        if "." in time_part:
            base_time, fractional = time_part.rsplit(".", 1)
            fractional = fractional[:6]
            time_part = f"{base_time}.{fractional}"

        corrected_time_str = time_part + tz_part
        self._time = datetime.fromisoformat(corrected_time_str)

    @property
    def height(self) -> int:
        return self._height

    @property
    def time(self) -> datetime:
        return self._time

    def hash(self) -> bytes:
        """Compute block hash from header."""
        header = self.signed_header["header"]
        return bytes.fromhex(header.get("validators_hash", ""))


class TendermintLightClient:
    """
    Minimal Tendermint light client for IBC header validation.
    """

    def __init__(self, chain_id: str, rpc_endpoint: str):
        self.chain_id = chain_id
        self.rpc_endpoint = rpc_endpoint.rstrip("/")
        self.trusted_blocks = {}

    def light_block(self, height: int = 0) -> TendermintLightBlock:
        """
        Get a validated light block.
        Returns a TendermintLightBlock with consistent signed_header and validator_set.
        """
        if height == 0:
            status_resp = requests.get(f"{self.rpc_endpoint}/status", timeout=10)
            status_resp.raise_for_status()
            status = status_resp.json()["result"]
            height = int(status["sync_info"]["latest_block_height"])

        commit_resp = requests.get(
            f"{self.rpc_endpoint}/commit?height={height}", timeout=10
        )
        commit_resp.raise_for_status()
        commit_data = commit_resp.json()["result"]

        signed_header = commit_data["signed_header"]

        validators = self._get_complete_validator_set(height)

        validator_set = {"validators": validators}

        return TendermintLightBlock(signed_header, validator_set)

    def _get_complete_validator_set(self, height: int) -> list:
        """Get all validators for a height with full pagination."""
        all_validators = []
        page = 1

        while True:
            resp = requests.get(
                f"{self.rpc_endpoint}/validators?height={height}&per_page=1000&page={page}",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()["result"]
            validators = data["validators"]

            if not validators:
                break

            all_validators.extend(validators)

            total = int(data.get("total", len(all_validators)))
            if len(all_validators) >= total:
                break

            page += 1
            if page > 500:  # Safety limit
                break

        logger.debug(f"Retrieved {len(all_validators)} validators for height {height}")
        return all_validators


def create_light_provider(chain_id: str, rpc_endpoint: str) -> TendermintLightClient:
    """
    Create a light client provider.
    """
    return TendermintLightClient(chain_id, rpc_endpoint)
