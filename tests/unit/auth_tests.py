#!/usr/bin/env python3
"""
Authentication module tests - validation and functional tests.

Validation tests: Validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Functional tests: Test auth client query operations, account management,
authentication parameters, and utility functions using mocking
to isolate functionality and test error handling scenarios.

Run: python auth_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.proto.cosmos.auth.v1beta1 import auth_pb2 as auth_pb
from akash.proto.cosmos.auth.v1beta1 import query_pb2 as auth_query


class TestAuthMessageStructures:
    """Test authentication protobuf message structures and field access."""

    def test_base_account_structure(self):
        """Test BaseAccount message structure and field access."""
        account = auth_pb.BaseAccount()

        required_fields = ['address', 'pub_key', 'account_number', 'sequence']
        for field in required_fields:
            assert hasattr(account, field), f"BaseAccount missing field: {field}"
        account.address = "cosmos1test"
        account.account_number = 123
        account.sequence = 45

        assert account.address == "cosmos1test"
        assert account.account_number == 123
        assert account.sequence == 45

    def test_module_account_structure(self):
        """Test ModuleAccount message structure and field access."""
        module_account = auth_pb.ModuleAccount()

        required_fields = ['base_account', 'name', 'permissions']
        for field in required_fields:
            assert hasattr(module_account, field), f"ModuleAccount missing field: {field}"
        module_account.name = "distribution"
        module_account.permissions.extend(["minter", "burner"])

        assert module_account.name == "distribution"
        assert len(module_account.permissions) == 2
        assert "minter" in module_account.permissions

    def test_params_structure(self):
        """Test Params message structure and field access."""
        params = auth_pb.Params()

        param_fields = [
            'max_memo_characters',
            'tx_sig_limit',
            'tx_size_cost_per_byte',
            'sig_verify_cost_ed25519',
            'sig_verify_cost_secp256k1'
        ]

        for field in param_fields:
            assert hasattr(params, field), f"Params missing field: {field}"
        params.max_memo_characters = 512
        params.tx_sig_limit = 7
        params.tx_size_cost_per_byte = 10

        assert params.max_memo_characters == 512
        assert params.tx_sig_limit == 7
        assert params.tx_size_cost_per_byte == 10


class TestAuthQueryResponses:
    """Test authentication query response structures."""

    def test_query_account_response_structure(self):
        """Test QueryAccountResponse nested structure access."""
        response = auth_query.QueryAccountResponse()

        assert hasattr(response, 'account'), "QueryAccountResponse missing account field"
        if response.account:
            assert hasattr(response.account, 'type_url'), "Account missing type_url"
            assert hasattr(response.account, 'value'), "Account missing value"

    def test_query_accounts_response_structure(self):
        """Test QueryAccountsResponse structure with pagination."""
        response = auth_query.QueryAccountsResponse()

        assert hasattr(response, 'accounts'), "QueryAccountsResponse missing accounts field"
        assert hasattr(response, 'pagination'), "QueryAccountsResponse missing pagination field"
        assert hasattr(response.accounts, 'append'), "accounts field should be list-like"

    def test_query_params_response_structure(self):
        """Test QueryParamsResponse structure."""
        response = auth_query.QueryParamsResponse()

        assert hasattr(response, 'params'), "QueryParamsResponse missing params field"


class TestAuthModuleIntegration:
    """Test auth module integration and consistency."""

    def test_account_type_consistency(self):
        """Test account types are consistent between messages."""
        base_account = auth_pb.BaseAccount()
        module_account = auth_pb.ModuleAccount()

        assert hasattr(base_account, 'address'), "BaseAccount missing address"
        assert hasattr(module_account.base_account, 'address'), "ModuleAccount.base_account missing address"
        module_account.base_account.address = "cosmos1module"
        assert module_account.base_account.address == "cosmos1module"

    def test_auth_params_validation(self):
        """Test auth parameter validation and constraints."""
        params = auth_pb.Params()

        params.max_memo_characters = 256
        params.tx_sig_limit = 7
        params.tx_size_cost_per_byte = 10
        params.sig_verify_cost_ed25519 = 590
        params.sig_verify_cost_secp256k1 = 1000
        assert params.max_memo_characters > 0
        assert params.tx_sig_limit > 0
        assert params.sig_verify_cost_ed25519 < params.sig_verify_cost_secp256k1


from unittest.mock import Mock, patch
import base64


class TestAuthClientInitialization:
    """Test auth client initialization and setup."""

    def test_auth_client_initialization(self):
        """Test AuthClient can be initialized properly."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        assert auth_client.akash_client == mock_akash_client
        assert hasattr(auth_client, 'get_account')
        assert hasattr(auth_client, 'get_accounts')
        assert hasattr(auth_client, 'get_auth_params')
        assert hasattr(auth_client, 'get_module_account_by_name')
        assert hasattr(auth_client, 'get_account_info')
        assert hasattr(auth_client, 'validate_address')
        assert hasattr(auth_client, 'get_next_sequence_number')
        assert hasattr(auth_client, 'get_account_number')

    def test_auth_client_inherits_mixins(self):
        """Test AuthClient properly inherits from all mixins."""
        from akash.modules.auth.client import AuthClient
        from akash.modules.auth.query import AuthQuery
        from akash.modules.auth.utils import AuthUtils

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        assert isinstance(auth_client, AuthQuery)
        assert isinstance(auth_client, AuthUtils)

    def test_auth_client_logging_setup(self):
        """Test logging is properly configured for AuthClient."""
        from akash.modules.auth.client import AuthClient

        with patch('akash.modules.auth.client.logger') as mock_logger:
            mock_akash_client = Mock()
            auth_client = AuthClient(mock_akash_client)

            mock_logger.info.assert_called_once_with("Initialized AuthClient")


class TestAuthQueryOperations:
    """Test auth query operations with mocked responses."""

    def test_get_account_success(self):
        """Test successful account query."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_account_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryAccountResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_account_any = Mock()
            mock_account_any.type_url = "/cosmos.auth.v1beta1.BaseAccount"

            mock_base_account = Mock()
            mock_base_account.address = "akash1test"
            mock_base_account.account_number = 123
            mock_base_account.sequence = 5
            mock_base_account.pub_key = None

            mock_account_any.Unpack.return_value = None
            mock_response_instance.account = mock_account_any
            mock_response_class.return_value = mock_response_instance

            with patch('akash.proto.cosmos.auth.v1beta1.auth_pb2.BaseAccount', return_value=mock_base_account):
                account = auth_client.get_account("akash1test")

                assert account is not None
                mock_akash_client.abci_query.assert_called_once()

    def test_get_account_not_found(self):
        """Test account query with account not found."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': None
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        account = auth_client.get_account("akash1nonexistent")
        assert account is None

    def test_get_account_abci_error(self):
        """Test account query with ABCI error."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = {}

        auth_client = AuthClient(mock_akash_client)

        account = auth_client.get_account("akash1test")
        assert account is None

    def test_get_accounts_success(self):
        """Test successful accounts list query."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_accounts_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryAccountsResponse') as mock_response_class:
            mock_response_instance = Mock()

            mock_account1 = Mock()
            mock_account1.type_url = "/cosmos.auth.v1beta1.BaseAccount"
            mock_account2 = Mock()
            mock_account2.type_url = "/cosmos.auth.v1beta1.BaseAccount"

            mock_response_instance.accounts = [mock_account1, mock_account2]
            mock_response_class.return_value = mock_response_instance

            with patch('akash.proto.cosmos.auth.v1beta1.auth_pb2.BaseAccount') as mock_base_account_class:
                mock_base_account1 = Mock()
                mock_base_account1.address = "akash1test1"
                mock_base_account1.account_number = 1
                mock_base_account1.sequence = 0
                mock_base_account1.pub_key = None

                mock_base_account2 = Mock()
                mock_base_account2.address = "akash1test2"
                mock_base_account2.account_number = 2
                mock_base_account2.sequence = 3
                mock_base_account2.pub_key = None

                mock_base_account_class.side_effect = [mock_base_account1, mock_base_account2]

                accounts = auth_client.get_accounts()

                assert len(accounts) == 2
                mock_akash_client.abci_query.assert_called_once()

    def test_get_accounts_with_pagination(self):
        """Test accounts query with pagination parameters."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_accounts_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryAccountsResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_response_instance.accounts = []
            mock_response_class.return_value = mock_response_instance

            accounts = auth_client.get_accounts(limit=10, offset=5)

            assert accounts == []
            mock_akash_client.abci_query.assert_called_once()

    def test_get_auth_params_success(self):
        """Test successful auth parameters query."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_params_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryParamsResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_params = Mock()
            mock_params.max_memo_characters = 256
            mock_params.tx_sig_limit = 7
            mock_params.tx_size_cost_per_byte = 10
            mock_params.sig_verify_cost_ed25519 = 590
            mock_params.sig_verify_cost_secp256k1 = 1000
            mock_response_instance.params = mock_params
            mock_response_class.return_value = mock_response_instance

            params = auth_client.get_auth_params()

            assert params is not None
            assert params['max_memo_characters'] == '256'
            assert params['tx_sig_limit'] == '7'
            assert params['sig_verify_cost_ed25519'] == '590'
            mock_akash_client.abci_query.assert_called_once()

    def test_get_auth_params_no_params(self):
        """Test auth parameters query with no params in response."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_params_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryParamsResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_response_instance.params = None
            mock_response_class.return_value = mock_response_instance

            params = auth_client.get_auth_params()

            assert params is None

    def test_get_module_account_by_name_success(self):
        """Test successful module account query by name."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_module_account_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryModuleAccountByNameResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_account = Mock()
            mock_account.type_url = "/cosmos.auth.v1beta1.ModuleAccount"
            mock_account.value = b'module_account_data'
            mock_response_instance.account = mock_account
            mock_response_class.return_value = mock_response_instance

            module_account = auth_client.get_module_account_by_name("distribution")

            assert module_account is not None
            assert module_account['name'] == "distribution"
            assert module_account['type_url'] == "/cosmos.auth.v1beta1.ModuleAccount"
            mock_akash_client.abci_query.assert_called_once()

    def test_get_module_account_by_name_not_found(self):
        """Test module account query with account not found."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_empty_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryModuleAccountByNameResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_response_instance.account = None
            mock_response_class.return_value = mock_response_instance

            module_account = auth_client.get_module_account_by_name("nonexistent")

            assert module_account is None


class TestAuthUtilityFunctions:
    """Test auth utility functions."""

    def test_get_account_info_success(self):
        """Test successful account info extraction."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        mock_account_data = {
            'address': 'akash1test',
            'sequence': '5',
            'account_number': '123',
            'pub_key': 'pubkey_data'
        }

        with patch.object(auth_client, 'get_account', return_value=mock_account_data):
            account_info = auth_client.get_account_info("akash1test")

            assert account_info is not None
            assert account_info['address'] == 'akash1test'
            assert account_info['sequence'] == 5
            assert account_info['account_number'] == 123
            assert account_info['has_pub_key'] == True

    def test_get_account_info_no_account(self):
        """Test account info extraction when account doesn't exist."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        with patch.object(auth_client, 'get_account', return_value=None):
            account_info = auth_client.get_account_info("akash1nonexistent")

            assert account_info is None

    def test_validate_address_exists(self):
        """Test address validation for existing address."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        mock_account_data = {'address': 'akash1test'}

        with patch.object(auth_client, 'get_account', return_value=mock_account_data):
            is_valid = auth_client.validate_address_existence("akash1test")

            assert is_valid == True

    def test_validate_address_not_exists(self):
        """Test address validation for non-existing address."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        with patch.object(auth_client, 'get_account', return_value=None):
            is_valid = auth_client.validate_address_existence("akash1nonexistent")

            assert is_valid == False

    def test_validate_address_exception(self):
        """Test address validation with exception."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        with patch.object(auth_client, 'get_account', side_effect=Exception("Network error")):
            with patch('akash.modules.auth.utils.logger') as mock_logger:
                is_valid = auth_client.validate_address_existence("akash1test")

                assert is_valid == False
                mock_logger.error.assert_called_once()

    def test_get_next_sequence_number_success(self):
        """Test getting next sequence number for existing account."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        mock_account_info = {'sequence': 5}

        with patch.object(auth_client, 'get_account_info', return_value=mock_account_info):
            sequence = auth_client.get_next_sequence_number("akash1test")

            assert sequence == 5

    def test_get_next_sequence_number_no_account(self):
        """Test getting sequence number for non-existing account."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        with patch.object(auth_client, 'get_account_info', return_value=None):
            sequence = auth_client.get_next_sequence_number("akash1nonexistent")

            assert sequence == 0

    def test_get_account_number_success(self):
        """Test getting account number for existing account."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        mock_account_info = {'account_number': 123}

        with patch.object(auth_client, 'get_account_info', return_value=mock_account_info):
            account_number = auth_client.get_account_number("akash1test")

            assert account_number == 123

    def test_get_account_number_no_account(self):
        """Test getting account number for non-existing account."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        with patch.object(auth_client, 'get_account_info', return_value=None):
            account_number = auth_client.get_account_number("akash1nonexistent")

            assert account_number == 0


class TestAuthErrorHandlingScenarios:
    """Test auth error handling and edge cases."""

    def test_get_account_network_failure(self):
        """Test account query with network failure."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        mock_akash_client.abci_query.side_effect = Exception("Connection timeout")

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.modules.auth.query.logger') as mock_logger:
            account = auth_client.get_account("akash1test")

            assert account is None
            mock_logger.error.assert_called_once()

    def test_get_accounts_malformed_response(self):
        """Test accounts query with malformed response."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': 'invalid_base64_data'
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.modules.auth.query.logger') as mock_logger:
            accounts = auth_client.get_accounts()

            assert accounts == []
            mock_logger.error.assert_called_once()

    def test_get_auth_params_network_error(self):
        """Test auth params query with network error."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        mock_akash_client.abci_query.side_effect = Exception("Network error")

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.modules.auth.query.logger') as mock_logger:
            params = auth_client.get_auth_params()

            assert params is None
            mock_logger.error.assert_called_once()

    def test_get_module_account_by_name_empty_response(self):
        """Test module account query with empty response."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': None
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        module_account = auth_client.get_module_account_by_name("distribution")

        assert module_account is None

    def test_get_accounts_protobuf_parse_error(self):
        """Test accounts query with protobuf parsing error."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'invalid_protobuf_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryAccountsResponse') as mock_response_class:
            mock_response_class.side_effect = Exception("Parse error")

            with patch('akash.modules.auth.query.logger') as mock_logger:
                accounts = auth_client.get_accounts()

                assert accounts == []
                mock_logger.error.assert_called_once()

    def test_get_account_unpacking_fallback(self):
        """Test account query with unpacking fallback to raw data."""
        from akash.modules.auth.client import AuthClient

        mock_response = {
            'response': {
                'value': base64.b64encode(b'mock_account_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = mock_response

        auth_client = AuthClient(mock_akash_client)

        with patch('akash.proto.cosmos.auth.v1beta1.query_pb2.QueryAccountResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_account_any = Mock()
            mock_account_any.type_url = "/cosmos.auth.v1beta1.BaseAccount"
            mock_account_any.value = b'raw_account_data'
            mock_account_any.Unpack.side_effect = Exception("Unpack failed")
            mock_response_instance.account = mock_account_any
            mock_response_class.return_value = mock_response_instance

            account = auth_client.get_account("akash1test")

            assert account is not None
            assert account['type_url'] == "/cosmos.auth.v1beta1.BaseAccount"
            assert 'raw_data' in account

    def test_get_account_info_missing_fields(self):
        """Test account info extraction with missing fields."""
        from akash.modules.auth.client import AuthClient

        mock_akash_client = Mock()
        auth_client = AuthClient(mock_akash_client)

        mock_account_data = {
            'address': 'akash1test',
            'sequence': None,
            'account_number': '123',
            'pub_key': None
        }

        with patch.object(auth_client, 'get_account', return_value=mock_account_data):
            account_info = auth_client.get_account_info("akash1test")

            assert account_info is not None
            assert account_info['address'] == 'akash1test'
            assert account_info['sequence'] == 0
            assert account_info['account_number'] == 123
            assert account_info['has_pub_key'] == False


if __name__ == '__main__':
    print("Running authentication module tests (validation + functional)")
    print("=" * 70)
    print()
    print("Validation tests: testing protobuf structures, message converters,")
    print("query responses, account management, and parameter handling patterns.")
    print()
    print("Functional tests: testing client operations, query methods, account")
    print("validation, authentication parameters, and error handling scenarios.")
    print()
    print("These tests cover functionality without blockchain interactions.")
    print()

    pytest.main([__file__, '-v'])
