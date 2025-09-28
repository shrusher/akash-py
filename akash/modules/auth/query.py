import base64
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AuthQuery:
    """
    Mixin for authentication query operations.
    """

    def get_account(self, address: str) -> Optional[Dict]:
        """
        Get account information by address.

        Args:
            address: Bech32 account address

        Returns:
            Optional[Dict]: Account data with keys: 'address', 'pub_key' (base64),
                           'account_number', 'sequence', 'type_url', or None if not found
        """
        try:
            from akash.proto.cosmos.auth.v1beta1.query_pb2 import (
                QueryAccountRequest,
                QueryAccountResponse,
            )
            from akash.proto.cosmos.auth.v1beta1.auth_pb2 import BaseAccount

            request = QueryAccountRequest()
            request.address = address

            path = "/cosmos.auth.v1beta1.Query/Account"
            request_data = request.SerializeToString().hex()

            result = self.akash_client.abci_query(path, request_data)

            if not result or "response" not in result:
                raise Exception(f"ABCI query failed for path {path}: No response")

            if not result["response"].get("value"):
                raise Exception(
                    f"ABCI query failed for path {path}: Empty response value"
                )

            response_data = base64.b64decode(result["response"]["value"])

            if response_data:
                response = QueryAccountResponse()
                response.ParseFromString(response_data)

                if response.account:
                    try:
                        account = BaseAccount()
                        response.account.Unpack(account)

                        return {
                            "address": account.address,
                            "pub_key": (
                                base64.b64encode(account.pub_key.value).decode()
                                if account.pub_key
                                else None
                            ),
                            "account_number": str(account.account_number),
                            "sequence": str(account.sequence),
                            "type_url": response.account.type_url,
                        }
                    except Exception:
                        return {
                            "address": address,
                            "type_url": response.account.type_url,
                            "raw_data": base64.b64encode(
                                response.account.value
                            ).decode(),
                        }

            return None

        except Exception as e:
            logger.error(f"Failed to get account {address}: {e}")
            return None

    def get_accounts(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all accounts with optional pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List[Dict]: List of account data, each with keys: 'address', 'pub_key' (base64),
                       'account_number', 'sequence', 'type_url'
        """
        try:
            from akash.proto.cosmos.auth.v1beta1.query_pb2 import (
                QueryAccountsRequest,
                QueryAccountsResponse,
            )
            from akash.proto.cosmos.auth.v1beta1.auth_pb2 import BaseAccount

            request = QueryAccountsRequest()

            if limit is not None or offset is not None:
                from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import (
                    PageRequest,
                )

                page_request = PageRequest()
                if limit is not None:
                    page_request.limit = limit
                if offset is not None:
                    page_request.offset = offset
                request.pagination.CopyFrom(page_request)

            path = "/cosmos.auth.v1beta1.Query/Accounts"
            request_data = request.SerializeToString().hex()

            result = self.akash_client.abci_query(path, request_data)

            if not result or "response" not in result:
                raise Exception(f"ABCI query failed for path {path}: No response")

            if not result["response"].get("value"):
                raise Exception(
                    f"ABCI query failed for path {path}: Empty response value"
                )

            response_data = base64.b64decode(result["response"]["value"])

            if response_data:
                response = QueryAccountsResponse()
                response.ParseFromString(response_data)

                accounts = []
                for account_any in response.accounts:
                    try:
                        account = BaseAccount()
                        account_any.Unpack(account)

                        account_info = {
                            "address": account.address,
                            "pub_key": (
                                base64.b64encode(account.pub_key.value).decode()
                                if account.pub_key
                                else None
                            ),
                            "account_number": str(account.account_number),
                            "sequence": str(account.sequence),
                            "type_url": account_any.type_url,
                        }
                        accounts.append(account_info)
                    except Exception:
                        account_info = {
                            "type_url": account_any.type_url,
                            "raw_data": base64.b64encode(account_any.value).decode(),
                        }
                        accounts.append(account_info)

                return accounts

            return []

        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return []

    def get_auth_params(self) -> Optional[Dict]:
        """
        Get authentication module parameters.

        Returns:
            Optional[Dict]: Auth module parameters with keys: 'max_memo_characters',
                           'tx_sig_limit', 'tx_size_cost_per_byte', 'sig_verify_cost_ed25519',
                           'sig_verify_cost_secp256k1', or None if not available
        """
        try:
            from akash.proto.cosmos.auth.v1beta1.query_pb2 import (
                QueryParamsRequest,
                QueryParamsResponse,
            )

            request = QueryParamsRequest()

            path = "/cosmos.auth.v1beta1.Query/Params"
            request_data = request.SerializeToString().hex()

            result = self.akash_client.abci_query(path, request_data)

            if not result or "response" not in result:
                raise Exception(f"ABCI query failed for path {path}: No response")

            if not result["response"].get("value"):
                raise Exception(
                    f"ABCI query failed for path {path}: Empty response value"
                )

            response_data = base64.b64decode(result["response"]["value"])

            if response_data:
                response = QueryParamsResponse()
                response.ParseFromString(response_data)

                if response.params:
                    return {
                        "max_memo_characters": str(response.params.max_memo_characters),
                        "tx_sig_limit": str(response.params.tx_sig_limit),
                        "tx_size_cost_per_byte": str(
                            response.params.tx_size_cost_per_byte
                        ),
                        "sig_verify_cost_ed25519": str(
                            response.params.sig_verify_cost_ed25519
                        ),
                        "sig_verify_cost_secp256k1": str(
                            response.params.sig_verify_cost_secp256k1
                        ),
                    }

            return None

        except Exception as e:
            logger.error(f"Failed to get auth params: {e}")
            return None

    def get_module_account_by_name(self, name: str) -> Optional[Dict]:
        """
        Get module account by name.

        Args:
            name: Module account name (e.g., 'distribution', 'bonded_tokens_pool')

        Returns:
            Optional[Dict]: Module account data with keys: 'address', 'pub_key' (base64),
                           'account_number', 'sequence', 'type_url', or None if not found
        """
        try:
            from akash.proto.cosmos.auth.v1beta1.query_pb2 import (
                QueryModuleAccountByNameRequest,
                QueryModuleAccountByNameResponse,
            )

            request = QueryModuleAccountByNameRequest()
            request.name = name

            path = "/cosmos.auth.v1beta1.Query/ModuleAccountByName"
            request_data = request.SerializeToString().hex()

            result = self.akash_client.abci_query(path, request_data)

            if not result or "response" not in result:
                raise Exception(f"ABCI query failed for path {path}: No response")

            if not result["response"].get("value"):
                raise Exception(
                    f"ABCI query failed for path {path}: Empty response value"
                )

            response_data = base64.b64decode(result["response"]["value"])

            if response_data:
                response = QueryModuleAccountByNameResponse()
                response.ParseFromString(response_data)

                if response.account:
                    return {
                        "name": name,
                        "type_url": response.account.type_url,
                        "raw_data": base64.b64encode(response.account.value).decode(),
                    }

            return None

        except Exception as e:
            logger.error(f"Failed to get module account {name}: {e}")
            return None
