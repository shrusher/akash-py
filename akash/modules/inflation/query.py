import base64
import logging
from typing import Dict, Optional, Any

from akash.proto.cosmos.mint.v1beta1 import query_pb2 as mint_query_pb2

logger = logging.getLogger(__name__)


class InflationQuery:
    """
    Mixin for inflation query operations.
    """

    def get_params(self) -> Optional[Dict[str, Any]]:
        """
        Query mint module parameters.

        Returns:
            Optional[Dict[str, Any]]: Mint parameters including inflation settings
        """
        try:
            logger.info("Querying mint parameters")

            request = mint_query_pb2.QueryParamsRequest()

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.rpc_query(
                "abci_query",
                ["/cosmos.mint.v1beta1.Query/Params", request_hex, "0", False],
            )

            if result and "response" in result:
                response = result["response"]
                code = response.get("code", -1)

                if code == 0 and response.get("value"):
                    response_data = base64.b64decode(response["value"])

                    query_response = mint_query_pb2.QueryParamsResponse()
                    query_response.ParseFromString(response_data)

                    if query_response.params:
                        params = query_response.params
                        return {
                            "mint_denom": params.mint_denom,
                            "inflation_rate_change": params.inflation_rate_change,
                            "inflation_max": params.inflation_max,
                            "inflation_min": params.inflation_min,
                            "goal_bonded": params.goal_bonded,
                            "blocks_per_year": str(params.blocks_per_year),
                        }
                else:
                    logger.error(f"Mint params query failed with code {code}")

            return None

        except Exception as e:
            logger.error(f"Failed to query mint params: {e}")
            return None

    def get_inflation(self) -> Optional[str]:
        """
        Query current inflation rate.

        Returns:
            Optional[str]: Current inflation rate as string
        """
        try:
            logger.info("Querying current inflation rate")

            request = mint_query_pb2.QueryInflationRequest()

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.rpc_query(
                "abci_query",
                ["/cosmos.mint.v1beta1.Query/Inflation", request_hex, "0", False],
            )

            if result and "response" in result:
                response = result["response"]
                code = response.get("code", -1)

                if code == 0 and response.get("value"):
                    response_data = base64.b64decode(response["value"])

                    query_response = mint_query_pb2.QueryInflationResponse()
                    query_response.ParseFromString(response_data)

                    if query_response.inflation:
                        return query_response.inflation.decode("utf-8")
                else:
                    logger.error(f"Inflation query failed with code {code}")

            return None

        except Exception as e:
            logger.error(f"Failed to query inflation: {e}")
            return None

    def get_annual_provisions(self) -> Optional[str]:
        """
        Query current annual provisions.

        Returns:
            Optional[str]: Current annual provisions as string
        """
        try:
            logger.info("Querying annual provisions")

            request = mint_query_pb2.QueryAnnualProvisionsRequest()

            request_bytes = request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.rpc_query(
                "abci_query",
                [
                    "/cosmos.mint.v1beta1.Query/AnnualProvisions",
                    request_hex,
                    "0",
                    False,
                ],
            )

            if result and "response" in result:
                response = result["response"]
                code = response.get("code", -1)

                if code == 0 and response.get("value"):
                    response_data = base64.b64decode(response["value"])

                    query_response = mint_query_pb2.QueryAnnualProvisionsResponse()
                    query_response.ParseFromString(response_data)

                    if query_response.annual_provisions:
                        return query_response.annual_provisions.decode("utf-8")
                else:
                    logger.error(f"Annual provisions query failed with code {code}")

            return None

        except Exception as e:
            logger.error(f"Failed to query annual provisions: {e}")
            return None

    def get_all_mint_info(self) -> Dict[str, Any]:
        """
        Get all mint module information in one call.

        Returns:
            Dict[str, Any]: Complete mint information including params, inflation, and annual provisions
        """
        try:
            logger.info("Querying all mint information")

            params = self.get_params()
            inflation = self.get_inflation()
            annual_provisions = self.get_annual_provisions()

            return {
                "params": params,
                "current_inflation": inflation,
                "annual_provisions": annual_provisions,
                "status": "success" if params else "partial",
            }

        except Exception as e:
            logger.error(f"Failed to get all mint info: {e}")
            return {
                "params": None,
                "current_inflation": None,
                "annual_provisions": None,
                "status": "error",
                "error": str(e),
            }
