import base64
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BankQuery:
    """
    Mixin for bank query operations.
    """

    def get_balance(self, address: str, denom: str = "uakt") -> str:
        """
        Query balance for specific denomination.

        Args:
            address: Account address
            denom: Token denomination

        Returns:
            str: Balance amount
        """
        try:
            from akash.proto.cosmos.bank.v1beta1 import query_pb2

            request = query_pb2.QueryBalanceRequest()
            request.address = address
            request.denom = denom

            data = request.SerializeToString().hex()

            result = self.akash_client.abci_query(
                "/cosmos.bank.v1beta1.Query/Balance", data
            )

            if "response" in result and "value" in result["response"]:
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryBalanceResponse()
                response.ParseFromString(response_data)

                if response.balance:
                    return response.balance.amount

            return "0"

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return "0"

    def get_all_balances(self, address: str) -> Dict[str, str]:
        """
        Query all balances for an address via RPC.

        Args:
            address: Account address

        Returns:
            Dict[str, str]: Balances by denomination
        """
        try:
            from akash.proto.cosmos.bank.v1beta1 import query_pb2

            request = query_pb2.QueryAllBalancesRequest()
            request.address = address

            data = request.SerializeToString().hex()

            result = self.akash_client.abci_query(
                "/cosmos.bank.v1beta1.Query/AllBalances", data
            )

            if "response" in result and "value" in result["response"]:
                response_data = base64.b64decode(result["response"]["value"])
                response = query_pb2.QueryAllBalancesResponse()
                response.ParseFromString(response_data)

                balances = {}
                for balance in response.balances:
                    balances[balance.denom] = balance.amount

                return balances

            return {}

        except Exception as e:
            logger.error(f"Failed to query all balances: {e}")
            raise

    def get_account_info(self, address: str) -> Dict[str, Any]:
        """
        Get account information including sequence and account number.

        Args:
            address: Account address

        Returns:
            Account information dictionary
        """
        try:
            return self.akash_client.get_account_info(address)
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    def get_supply(self, denom: str = "uakt") -> Dict[str, Any]:
        """
        Get token supply information using proper ABCI query.

        Args:
            denom: Token denomination

        Returns:
            Supply information
        """
        try:
            from akash.proto.cosmos.bank.v1beta1.query_pb2 import QuerySupplyOfRequest

            logger.info(f"Querying supply for {denom}")

            request = QuerySupplyOfRequest()
            request.denom = denom

            data = request.SerializeToString().hex()

            result = self.akash_client.abci_query(
                "/cosmos.bank.v1beta1.Query/SupplyOf", data
            )

            if "response" in result and "value" in result["response"]:
                import base64
                from akash.proto.cosmos.bank.v1beta1.query_pb2 import (
                    QuerySupplyOfResponse,
                )

                response_data = base64.b64decode(result["response"]["value"])
                response = QuerySupplyOfResponse()
                response.ParseFromString(response_data)

                if response.amount:
                    supply_amount = response.amount.amount
                    supply_akt = (
                        int(supply_amount) / 1_000_000 if supply_amount != "0" else 0.0
                    )
                    return {
                        "denom": denom,
                        "amount": supply_amount,
                        "amount_akt": f"{supply_akt:.6f}",
                    }

            return {"denom": denom, "amount": "0", "amount_akt": "0.0"}

        except Exception as e:
            logger.error(f"Failed to get supply: {e}")
            raise
