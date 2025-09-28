import base64
import logging
from typing import Dict, List, Any, Optional

from akash.proto.cosmos.slashing.v1beta1 import query_pb2 as slashing_query_pb2

logger = logging.getLogger(__name__)


class SlashingQuery:
    """
    Mixin for slashing query operations.
    """

    def get_params(self) -> Dict[str, Any]:
        """
        Query slashing parameters.

        Returns:
            dict: Slashing parameters including signed blocks window,
                 min signed per window, downtime jail duration, and
                 slash fractions for double sign and downtime.
        """
        try:
            request = slashing_query_pb2.QueryParamsRequest()

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.rpc_query(
                "abci_query",
                ["/cosmos.slashing.v1beta1.Query/Params", request_hex, "0", False],
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code", 0) == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = slashing_query_pb2.QueryParamsResponse()
                    query_response.ParseFromString(response_data)

                    params = query_response.params

                    return {
                        "signed_blocks_window": str(params.signed_blocks_window),
                        "min_signed_per_window": (
                            params.min_signed_per_window.hex()
                            if params.min_signed_per_window
                            else ""
                        ),
                        "downtime_jail_duration": str(
                            params.downtime_jail_duration.seconds
                        )
                        + "s",
                        "slash_fraction_double_sign": (
                            params.slash_fraction_double_sign.hex()
                            if params.slash_fraction_double_sign
                            else ""
                        ),
                        "slash_fraction_downtime": (
                            params.slash_fraction_downtime.hex()
                            if params.slash_fraction_downtime
                            else ""
                        ),
                    }

            return {}

        except ImportError as e:
            logger.error(f"Slashing protobuf imports failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Get slashing params failed: {e}")
            raise

    def get_signing_info(self, cons_address: str) -> Dict[str, Any]:
        """
        Query signing info of a specific validator by consensus address.

        Args:
            cons_address: Consensus address of the validator

        Returns:
            dict: Validator signing info including address, start height,
                 index offset, jailed until, tombstoned status, and
                 missed blocks counter.
        """
        try:
            request = slashing_query_pb2.QuerySigningInfoRequest()
            request.cons_address = cons_address

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.rpc_query(
                "abci_query",
                ["/cosmos.slashing.v1beta1.Query/SigningInfo", request_hex, "0", False],
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code", 0) == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = slashing_query_pb2.QuerySigningInfoResponse()
                    query_response.ParseFromString(response_data)

                    signing_info = query_response.val_signing_info

                    return {
                        "address": signing_info.address,
                        "start_height": str(signing_info.start_height),
                        "index_offset": str(signing_info.index_offset),
                        "jailed_until": f"{signing_info.jailed_until.seconds}.{signing_info.jailed_until.nanos:09d}Z",
                        "tombstoned": signing_info.tombstoned,
                        "missed_blocks_counter": str(
                            signing_info.missed_blocks_counter
                        ),
                    }

            return {}

        except ImportError as e:
            logger.error(f"Slashing protobuf imports failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Get signing info failed: {e}")
            raise

    def get_signing_infos(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query signing info of all validators.

        Args:
            limit: Maximum number of validators to return
            offset: Number of validators to skip

        Returns:
            list: List of validator signing infos, each containing address,
                 start height, index offset, jailed until, tombstoned status,
                 and missed blocks counter.
        """
        try:
            request = slashing_query_pb2.QuerySigningInfosRequest()

            if limit is not None or offset is not None:
                try:
                    from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import (
                        PageRequest,
                    )

                    pagination = PageRequest()
                    if limit is not None:
                        pagination.limit = limit
                    if offset is not None:
                        pagination.offset = offset
                    request.pagination.CopyFrom(pagination)
                except ImportError:
                    pass

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.rpc_query(
                "abci_query",
                [
                    "/cosmos.slashing.v1beta1.Query/SigningInfos",
                    request_hex,
                    "0",
                    False,
                ],
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code", 0) == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = slashing_query_pb2.QuerySigningInfosResponse()
                    query_response.ParseFromString(response_data)

                    signing_infos = []
                    for info in query_response.info:
                        signing_infos.append(
                            {
                                "address": info.address,
                                "start_height": str(info.start_height),
                                "index_offset": str(info.index_offset),
                                "jailed_until": f"{info.jailed_until.seconds}.{info.jailed_until.nanos:09d}Z",
                                "tombstoned": info.tombstoned,
                                "missed_blocks_counter": str(
                                    info.missed_blocks_counter
                                ),
                            }
                        )

                    return signing_infos

            return []

        except ImportError as e:
            logger.error(f"Slashing protobuf imports failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Get signing infos failed: {e}")
            raise
