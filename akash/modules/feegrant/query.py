import base64
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class FeegrantQuery:
    """
    Mixin for fee grant query operations.
    """

    def get_allowance(self, granter: str, grantee: str) -> Dict[str, Any]:
        """
        Query fee allowance between two accounts.

        Args:
            granter: Address of the account that granted the allowance
            grantee: Address of the account that received the allowance

        Returns:
            dict: Fee allowance info or empty dict if not found
        """
        try:
            from akash.proto.cosmos.feegrant.v1beta1.query_pb2 import (
                QueryAllowanceRequest,
                QueryAllowanceResponse,
            )

            request = QueryAllowanceRequest()
            request.granter = granter
            request.grantee = grantee

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.abci_query(
                path="/cosmos.feegrant.v1beta1.Query/Allowance", data=request_hex
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code", 0) == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = QueryAllowanceResponse()
                    query_response.ParseFromString(response_data)

                    if query_response.allowance:
                        allowance_info = {
                            "granter": query_response.allowance.granter,
                            "grantee": query_response.allowance.grantee,
                            "allowance": {
                                "type_url": query_response.allowance.allowance.type_url,
                            },
                        }
                        return allowance_info

            return {}

        except ImportError as e:
            logger.error(f"Feegrant protobuf imports failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Get allowance failed: {e}")
            raise

    def get_allowances(
        self, grantee: str, limit: int = 100, offset: int = 0, count_total: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query all fee allowances for a grantee.

        Args:
            grantee: Address of the account that received allowances
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            list: List of fee allowances
        """
        try:
            from akash.proto.cosmos.feegrant.v1beta1.query_pb2 import (
                QueryAllowancesRequest,
                QueryAllowancesResponse,
            )
            from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import PageRequest

            request = QueryAllowancesRequest()
            request.grantee = grantee

            page_request = PageRequest()
            page_request.limit = limit
            page_request.offset = offset
            page_request.count_total = count_total
            request.pagination.CopyFrom(page_request)

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.abci_query(
                path="/cosmos.feegrant.v1beta1.Query/Allowances", data=request_hex
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code", 0) == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = QueryAllowancesResponse()
                    query_response.ParseFromString(response_data)

                    allowances = []
                    for allowance in query_response.allowances:
                        allowance_info = {
                            "granter": allowance.granter,
                            "grantee": allowance.grantee,
                            "allowance": {"type_url": allowance.allowance.type_url},
                        }
                        allowances.append(allowance_info)

                    return allowances

            return []

        except ImportError as e:
            logger.error(f"Feegrant protobuf imports failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Get allowances failed: {e}")
            raise

    def get_allowances_by_granter(
        self, granter: str, limit: int = 100, offset: int = 0, count_total: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query all fee allowances granted by an account.

        Args:
            granter: Address of the account that granted allowances
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            list: List of fee allowances granted
        """
        try:
            from akash.proto.cosmos.feegrant.v1beta1.query_pb2 import (
                QueryAllowancesByGranterRequest,
                QueryAllowancesByGranterResponse,
            )
            from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import PageRequest

            request = QueryAllowancesByGranterRequest()
            request.granter = granter

            page_request = PageRequest()
            page_request.limit = limit
            page_request.offset = offset
            page_request.count_total = count_total
            request.pagination.CopyFrom(page_request)

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.abci_query(
                path="/cosmos.feegrant.v1beta1.Query/AllowancesByGranter",
                data=request_hex,
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code", 0) == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = QueryAllowancesByGranterResponse()
                    query_response.ParseFromString(response_data)

                    allowances = []
                    for allowance in query_response.allowances:
                        allowance_info = {
                            "granter": allowance.granter,
                            "grantee": allowance.grantee,
                            "allowance": {"type_url": allowance.allowance.type_url},
                        }
                        allowances.append(allowance_info)

                    return allowances

            return []

        except ImportError as e:
            logger.error(f"Feegrant protobuf imports failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Get allowances by granter failed: {e}")
            raise
