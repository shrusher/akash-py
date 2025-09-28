#!/usr/bin/env python3
"""
Validation tests for Cosmos Authz module.

These tests validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Run: python authz_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.proto.cosmos.authz.v1beta1 import authz_pb2 as authz_pb
from akash.proto.cosmos.authz.v1beta1 import tx_pb2 as authz_tx
from akash.proto.cosmos.authz.v1beta1 import query_pb2 as authz_query
from google.protobuf import any_pb2


class TestAuthzMessageStructures:
    """Test authz protobuf message structures and field access."""

    def test_msg_grant_structure(self):
        """Test MsgGrant message structure and field access."""
        msg_grant = authz_tx.MsgGrant()

        required_fields = ['granter', 'grantee', 'grant']
        for field in required_fields:
            assert hasattr(msg_grant, field), f"MsgGrant missing field: {field}"
        msg_grant.granter = "akash1granter"
        msg_grant.grantee = "akash1grantee"

        assert msg_grant.granter == "akash1granter"
        assert msg_grant.grantee == "akash1grantee"

        assert hasattr(msg_grant.grant, 'authorization'), "Grant missing authorization field"
        assert hasattr(msg_grant.grant, 'expiration'), "Grant missing expiration field"

    def test_msg_revoke_structure(self):
        """Test MsgRevoke message structure and field access."""
        msg_revoke = authz_tx.MsgRevoke()

        required_fields = ['granter', 'grantee', 'msg_type_url']
        for field in required_fields:
            assert hasattr(msg_revoke, field), f"MsgRevoke missing field: {field}"
        msg_revoke.granter = "akash1granter"
        msg_revoke.grantee = "akash1grantee"
        msg_revoke.msg_type_url = "/cosmos.bank.v1beta1.MsgSend"

        assert msg_revoke.granter == "akash1granter"
        assert msg_revoke.grantee == "akash1grantee"
        assert msg_revoke.msg_type_url == "/cosmos.bank.v1beta1.MsgSend"

    def test_msg_exec_structure(self):
        """Test MsgExec message structure and field access."""
        msg_exec = authz_tx.MsgExec()

        required_fields = ['grantee', 'msgs']
        for field in required_fields:
            assert hasattr(msg_exec, field), f"MsgExec missing field: {field}"
        msg_exec.grantee = "akash1grantee"

        assert msg_exec.grantee == "akash1grantee"

        any_msg = any_pb2.Any()
        any_msg.type_url = "/cosmos.bank.v1beta1.MsgSend"
        msg_exec.msgs.append(any_msg)

        assert len(msg_exec.msgs) == 1
        assert msg_exec.msgs[0].type_url == "/cosmos.bank.v1beta1.MsgSend"

    def test_grant_structure(self):
        """Test Grant message structure and field access."""
        grant = authz_pb.Grant()

        required_fields = ['authorization', 'expiration']
        for field in required_fields:
            assert hasattr(grant, field), f"Grant missing field: {field}"
        assert hasattr(grant.authorization, 'type_url'), "Authorization missing type_url field"
        assert hasattr(grant.authorization, 'value'), "Authorization missing value field"

        assert hasattr(grant.expiration, 'seconds'), "Expiration missing seconds field"
        assert hasattr(grant.expiration, 'nanos'), "Expiration missing nanos field"

    def test_generic_authorization_structure(self):
        """Test GenericAuthorization message structure."""
        generic_auth = authz_pb.GenericAuthorization()

        required_fields = ['msg']
        for field in required_fields:
            assert hasattr(generic_auth, field), f"GenericAuthorization missing field: {field}"
        generic_auth.msg = "/cosmos.bank.v1beta1.MsgSend"

        assert generic_auth.msg == "/cosmos.bank.v1beta1.MsgSend"


class TestAuthzQueryResponses:
    """Test authz query response structures."""

    def test_query_grants_response_structure(self):
        """Test QueryGrantsResponse structure."""
        response = authz_query.QueryGrantsResponse()

        assert hasattr(response, 'grants'), "QueryGrantsResponse missing grants field"
        assert hasattr(response, 'pagination'), "QueryGrantsResponse missing pagination field"
        grant = authz_pb.Grant()
        grant.authorization.type_url = "/cosmos.authz.v1beta1.GenericAuthorization"
        response.grants.append(grant)

        assert len(response.grants) == 1
        assert response.grants[0].authorization.type_url == "/cosmos.authz.v1beta1.GenericAuthorization"

    def test_query_granter_grants_response_structure(self):
        """Test QueryGranterGrantsResponse structure."""
        response = authz_query.QueryGranterGrantsResponse()

        assert hasattr(response, 'grants'), "QueryGranterGrantsResponse missing grants field"
        assert hasattr(response, 'pagination'), "QueryGranterGrantsResponse missing pagination field"
        grant_auth = authz_pb.GrantAuthorization()
        grant_auth.granter = "akash1granter"
        grant_auth.grantee = "akash1grantee"
        grant_auth.authorization.type_url = "/cosmos.authz.v1beta1.GenericAuthorization"

        response.grants.append(grant_auth)

        assert len(response.grants) == 1
        assert response.grants[0].granter == "akash1granter"
        assert response.grants[0].grantee == "akash1grantee"

    def test_query_grantee_grants_response_structure(self):
        """Test QueryGranteeGrantsResponse structure."""
        response = authz_query.QueryGranteeGrantsResponse()

        assert hasattr(response, 'grants'), "QueryGranteeGrantsResponse missing grants field"
        assert hasattr(response, 'pagination'), "QueryGranteeGrantsResponse missing pagination field"


class TestAuthzMessageConverters:
    """Test authz message converters for transaction compatibility."""

    def test_all_authz_converters_registered(self):
        """Test that all authz message converters are registered."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        required_converters = [
            "/cosmos.authz.v1beta1.MsgGrant",
            "/cosmos.authz.v1beta1.MsgRevoke",
            "/cosmos.authz.v1beta1.MsgExec"
        ]

        for msg_type in required_converters:
            converter = _MESSAGE_CONVERTERS.get(msg_type)
            assert converter is not None, f"Missing converter for {msg_type}"
            assert callable(converter), f"Converter for {msg_type} is not callable"

    def test_msg_grant_protobuf_compatibility(self):
        """Test MsgGrant protobuf field compatibility."""
        pb_msg = authz_tx.MsgGrant()

        required_fields = ['granter', 'grantee', 'grant']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgGrant missing field: {field}"
        pb_msg.granter = "akash1test"
        pb_msg.grantee = "akash1grantee"

        assert pb_msg.granter == "akash1test"
        assert pb_msg.grantee == "akash1grantee"

    def test_msg_revoke_protobuf_compatibility(self):
        """Test MsgRevoke protobuf field compatibility."""
        pb_msg = authz_tx.MsgRevoke()

        required_fields = ['granter', 'grantee', 'msg_type_url']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgRevoke missing field: {field}"

    def test_msg_exec_protobuf_compatibility(self):
        """Test MsgExec protobuf field compatibility."""
        pb_msg = authz_tx.MsgExec()

        required_fields = ['grantee', 'msgs']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgExec missing field: {field}"


class TestAuthzQueryParameters:
    """Test authz query parameter compatibility."""

    def test_grants_query_request_structures(self):
        """Test grants query request structures."""
        grants_req = authz_query.QueryGrantsRequest()
        assert hasattr(grants_req, 'granter'), "QueryGrantsRequest missing granter field"
        assert hasattr(grants_req, 'grantee'), "QueryGrantsRequest missing grantee field"
        assert hasattr(grants_req, 'msg_type_url'), "QueryGrantsRequest missing msg_type_url field"
        assert hasattr(grants_req, 'pagination'), "QueryGrantsRequest missing pagination field"

    def test_granter_grants_query_request_structure(self):
        """Test granter grants query request structure."""
        granter_req = authz_query.QueryGranterGrantsRequest()
        assert hasattr(granter_req, 'granter'), "QueryGranterGrantsRequest missing granter field"
        assert hasattr(granter_req, 'pagination'), "QueryGranterGrantsRequest missing pagination field"

    def test_grantee_grants_query_request_structure(self):
        """Test grantee grants query request structure."""
        grantee_req = authz_query.QueryGranteeGrantsRequest()
        assert hasattr(grantee_req, 'grantee'), "QueryGranteeGrantsRequest missing grantee field"
        assert hasattr(grantee_req, 'pagination'), "QueryGranteeGrantsRequest missing pagination field"


class TestAuthzTransactionMessages:
    """Test authz transaction message structures."""

    def test_all_authz_message_types_exist(self):
        """Test all expected authz message types exist."""
        expected_messages = [
            'MsgGrant', 'MsgRevoke', 'MsgExec'
        ]

        for msg_name in expected_messages:
            assert hasattr(authz_tx, msg_name), f"Missing authz message type: {msg_name}"

            msg_class = getattr(authz_tx, msg_name)
            msg_instance = msg_class()
            assert msg_instance is not None

    def test_authz_message_response_types_exist(self):
        """Test authz message response types exist."""
        expected_responses = [
            'MsgGrantResponse', 'MsgRevokeResponse', 'MsgExecResponse'
        ]

        for response_name in expected_responses:
            assert hasattr(authz_tx, response_name), f"Missing authz response type: {response_name}"

            response_class = getattr(authz_tx, response_name)
            response_instance = response_class()
            assert response_instance is not None

    def test_grant_revoke_consistency(self):
        """Test grant and revoke message consistency."""
        msg_grant = authz_tx.MsgGrant()
        msg_revoke = authz_tx.MsgRevoke()

        common_fields = ['granter', 'grantee']
        for field in common_fields:
            assert hasattr(msg_grant, field), f"MsgGrant missing: {field}"
            assert hasattr(msg_revoke, field), f"MsgRevoke missing: {field}"


class TestAuthzErrorPatterns:
    """Test common authz error patterns and edge cases."""

    def test_empty_grants_response_handling(self):
        """Test handling of empty grants response."""
        response = authz_query.QueryGrantsResponse()

        assert len(response.grants) == 0, "Empty response should have no grants"
        assert hasattr(response, 'pagination'), "Empty response missing pagination"

    def test_empty_msgs_handling(self):
        """Test handling of empty msgs in MsgExec."""
        msg_exec = authz_tx.MsgExec()

        assert len(msg_exec.msgs) == 0, "MsgExec should start with empty msgs list"
        any_msg = any_pb2.Any()
        any_msg.type_url = "/cosmos.bank.v1beta1.MsgSend"
        msg_exec.msgs.append(any_msg)

        assert len(msg_exec.msgs) == 1

    def test_expired_grant_handling(self):
        """Test handling of expired grants."""
        grant = authz_pb.Grant()

        grant.expiration.seconds = 1600000000
        grant.expiration.nanos = 0

        assert grant.expiration.seconds == 1600000000
        assert grant.expiration.nanos == 0

    def test_authorization_any_type_handling(self):
        """Test handling of Any type in authorization."""
        grant = authz_pb.Grant()

        grant.authorization.type_url = "/cosmos.authz.v1beta1.GenericAuthorization"
        grant.authorization.value = b"test_authorization_data"

        assert grant.authorization.type_url == "/cosmos.authz.v1beta1.GenericAuthorization"
        assert grant.authorization.value == b"test_authorization_data"


class TestAuthzModuleIntegration:
    """Test authz module integration and consistency."""

    def test_authz_converter_coverage(self):
        """Test all authz messages have converters in tx registry."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        expected_converters = ['MsgGrant', 'MsgRevoke', 'MsgExec']
        for msg_class in expected_converters:
            converter_key = f"/cosmos.authz.v1beta1.{msg_class}"
            assert converter_key in _MESSAGE_CONVERTERS, f"Missing converter for: {msg_class}"

    def test_authz_query_consistency(self):
        """Test authz query response consistency."""
        grants_response = authz_query.QueryGrantsResponse()
        granter_response = authz_query.QueryGranterGrantsResponse()
        grantee_response = authz_query.QueryGranteeGrantsResponse()
        assert hasattr(grants_response, 'grants'), "Grants response missing grants"
        assert hasattr(granter_response, 'grants'), "Granter response missing grants"
        assert hasattr(grantee_response, 'grants'), "Grantee response missing grants"

    def test_address_consistency(self):
        """Test address handling consistency across authz structures."""
        msg_grant = authz_tx.MsgGrant()
        msg_revoke = authz_tx.MsgRevoke()
        msg_exec = authz_tx.MsgExec()
        grant_auth = authz_pb.GrantAuthorization()

        test_granter = "akash1granter123"
        test_grantee = "akash1grantee123"

        msg_grant.granter = test_granter
        msg_grant.grantee = test_grantee

        msg_revoke.granter = test_granter
        msg_revoke.grantee = test_grantee

        msg_exec.grantee = test_grantee

        grant_auth.granter = test_granter
        grant_auth.grantee = test_grantee

        assert msg_grant.granter == test_granter
        assert msg_grant.grantee == test_grantee
        assert msg_revoke.granter == test_granter
        assert msg_revoke.grantee == test_grantee
        assert msg_exec.grantee == test_grantee
        assert grant_auth.granter == test_granter
        assert grant_auth.grantee == test_grantee

    def test_msg_type_url_consistency(self):
        """Test msg_type_url handling consistency."""
        msg_revoke = authz_tx.MsgRevoke()
        generic_auth = authz_pb.GenericAuthorization()

        test_msg_type = "/cosmos.bank.v1beta1.MsgSend"

        msg_revoke.msg_type_url = test_msg_type
        generic_auth.msg = test_msg_type

        assert msg_revoke.msg_type_url == test_msg_type
        assert generic_auth.msg == test_msg_type

    def test_grant_lifecycle_consistency(self):
        """Test grant lifecycle consistency."""
        msg_grant = authz_tx.MsgGrant()
        msg_grant.granter = "akash1granter"
        msg_grant.grantee = "akash1grantee"
        msg_grant.grant.authorization.type_url = "/cosmos.authz.v1beta1.GenericAuthorization"

        msg_exec = authz_tx.MsgExec()
        msg_exec.grantee = "akash1grantee"

        msg_revoke = authz_tx.MsgRevoke()
        msg_revoke.granter = "akash1granter"
        msg_revoke.grantee = "akash1grantee"
        msg_revoke.msg_type_url = "/cosmos.bank.v1beta1.MsgSend"

        assert msg_grant.grantee == msg_exec.grantee
        assert msg_grant.granter == msg_revoke.granter
        assert msg_grant.grantee == msg_revoke.grantee


from unittest.mock import Mock, patch
import base64


class TestAuthzClientInitialization:
    """Test AuthzClient initialization and basic functionality."""

    def setup_method(self):
        self.mock_akash_client = Mock()
        self.mock_akash_client.abci_query = Mock()

    def test_authz_client_creation(self):
        """Test that AuthzClient can be instantiated properly."""
        from akash.modules.authz.client import AuthzClient

        client = AuthzClient(self.mock_akash_client)
        assert client.akash_client == self.mock_akash_client
        assert client.client == self.mock_akash_client

    def test_authz_client_inheritance(self):
        """Test AuthzClient inherits from all required mixins."""
        from akash.modules.authz.client import AuthzClient
        from akash.modules.authz.query import AuthzQuery
        from akash.modules.authz.tx import AuthzTx
        from akash.modules.authz.utils import AuthzUtils

        client = AuthzClient(self.mock_akash_client)

        assert isinstance(client, AuthzQuery)
        assert isinstance(client, AuthzTx)
        assert isinstance(client, AuthzUtils)

        assert hasattr(client, 'get_grants')
        assert hasattr(client, 'grant_authorization')
        assert hasattr(client, 'revoke_authorization')
        assert hasattr(client, 'execute_authorized')

    def test_client_initialization_logging(self):
        """Test client initialization includes proper logging."""
        from akash.modules.authz.client import AuthzClient

        with patch('akash.modules.authz.client.logger.info') as mock_log:
            client = AuthzClient(self.mock_akash_client)
            mock_log.assert_called_once_with("Initialized AuthzClient")


class TestAuthzQueryOperations:
    """Test AuthzQuery operations with mocked responses."""

    def setup_method(self):
        self.mock_akash_client = Mock()
        self.mock_akash_client.abci_query = Mock()

        from akash.modules.authz.client import AuthzClient
        self.client = AuthzClient(self.mock_akash_client)

    def test_get_grants_success(self):
        """Test successful grants query."""
        mock_response = {
            "response": {
                "code": 0,
                "value": base64.b64encode(b"mock_grants_data").decode()
            }
        }
        self.mock_akash_client.abci_query.return_value = mock_response

        with patch('akash.proto.cosmos.authz.v1beta1.query_pb2.QueryGrantsResponse') as MockResponse:
            mock_response_obj = Mock()
            mock_grant = Mock()
            mock_grant.authorization.type_url = "/cosmos.authz.v1beta1.GenericAuthorization"
            mock_grant.expiration.seconds = 1700000000
            mock_grant.expiration.nanos = 0
            mock_response_obj.grants = [mock_grant]
            MockResponse.return_value = mock_response_obj

            with patch('akash.proto.cosmos.authz.v1beta1.authz_pb2.GenericAuthorization') as MockAuth:
                mock_auth = Mock()
                mock_auth.msg = "/cosmos.bank.v1beta1.MsgSend"
                MockAuth.return_value = mock_auth

                result = self.client.get_grants("akash1granter", "akash1grantee")

                assert isinstance(result, list)
                self.mock_akash_client.abci_query.assert_called_once()

    def test_get_grants_no_results(self):
        """Test grants query with no results."""
        mock_response = {
            "response": {
                "code": 0,
                "value": None
            }
        }
        self.mock_akash_client.abci_query.return_value = mock_response

        result = self.client.get_grants("akash1granter")
        assert result == []

    def test_get_grants_failure(self):
        """Test grants query failure handling."""
        self.mock_akash_client.abci_query.side_effect = Exception("Network error")

        with pytest.raises(Exception) as exc_info:
            self.client.get_grants("akash1granter")

        assert "Network error" in str(exc_info.value)

    def test_get_granter_grants_success(self):
        """Test successful granter grants query."""
        mock_response = {
            "response": {
                "code": 0,
                "value": base64.b64encode(b"mock_granter_data").decode()
            }
        }
        self.mock_akash_client.abci_query.return_value = mock_response

        with patch('akash.proto.cosmos.authz.v1beta1.query_pb2.QueryGranterGrantsResponse') as MockResponse:
            with patch('base64.b64decode') as mock_decode:
                mock_decode.return_value = b"mock_data"
                mock_response_obj = Mock()
                mock_grant = Mock()
                mock_grant.granter = "akash1granter"
                mock_grant.grantee = "akash1grantee"
                mock_grant.authorization.type_url = "/cosmos.authz.v1beta1.GenericAuthorization"
                mock_grant.expiration.seconds = 1700000000
                mock_grant.expiration.nanos = 0
                mock_response_obj.grants = [mock_grant]
                MockResponse.return_value = mock_response_obj

                with patch.object(self.client, '_parse_authorization_details') as mock_parse:
                    mock_parse.return_value = {"@type": "/cosmos.authz.v1beta1.GenericAuthorization"}
                    result = self.client.get_granter_grants("akash1granter")
                    assert isinstance(result, list)

    def test_get_grantee_grants_success(self):
        """Test successful grantee grants query."""
        mock_response = {
            "response": {
                "code": 0,
                "value": base64.b64encode(b"mock_grantee_data").decode()
            }
        }
        self.mock_akash_client.abci_query.return_value = mock_response

        with patch('akash.proto.cosmos.authz.v1beta1.query_pb2.QueryGranteeGrantsResponse') as MockResponse:
            mock_response_obj = Mock()
            mock_response_obj.grants = []
            MockResponse.return_value = mock_response_obj

            result = self.client.get_grantee_grants("akash1grantee")
            assert result == []

    def test_query_with_message_type_filter(self):
        """Test grants query with message type filtering."""
        mock_response = {
            "response": {
                "code": 0,
                "value": base64.b64encode(b"filtered_data").decode()
            }
        }
        self.mock_akash_client.abci_query.return_value = mock_response

        with patch('akash.proto.cosmos.authz.v1beta1.query_pb2.QueryGrantsResponse'):
            result = self.client.get_grants(
                "akash1granter",
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend"
            )

            call_args = self.mock_akash_client.abci_query.call_args
            assert "/cosmos.authz.v1beta1.Query/Grants" in call_args[0]


class TestAuthzTransactionOperations:
    """Test AuthzTx operations with mocked broadcast responses."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_akash_client = Mock()
        self.mock_wallet = Mock()
        self.mock_wallet.address = "akash1wallet"

        from akash.modules.authz.client import AuthzClient
        self.client = AuthzClient(self.mock_akash_client)

    def test_grant_authorization_send_auth(self):
        """Test granting SendAuthorization."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_result.tx_hash = "ABC123"
            mock_broadcast.return_value = mock_result

            result = self.client.grant_authorization(
                self.mock_wallet,
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend",
                "5000000",
                "uakt",
                authorization_type="send"
            )

            assert result.success
            assert result.tx_hash == "ABC123"

            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args
            messages = call_args[1]['messages']
            assert len(messages) == 1
            assert messages[0]['@type'] == '/cosmos.authz.v1beta1.MsgGrant'
            assert messages[0]['granter'] == "akash1wallet"
            assert messages[0]['grantee'] == "akash1grantee"

    def test_grant_authorization_generic_auth(self):
        """Test granting GenericAuthorization."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            result = self.client.grant_authorization(
                self.mock_wallet,
                "akash1grantee",
                "/cosmos.distribution.v1beta1.MsgWithdrawDelegatorReward",
                authorization_type="generic"
            )

            assert result.success

            call_args = mock_broadcast.call_args
            messages = call_args[1]['messages']
            grant = messages[0]['grant']
            assert grant['authorization']['@type'] == '/cosmos.authz.v1beta1.GenericAuthorization'
            assert grant['authorization']['msg'] == '/cosmos.distribution.v1beta1.MsgWithdrawDelegatorReward'

    def test_grant_authorization_default_type(self):
        """Test default authorization type (send)."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            self.client.grant_authorization(
                self.mock_wallet,
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend"
            )

            call_args = mock_broadcast.call_args
            messages = call_args[1]['messages']
            auth_type = messages[0]['grant']['authorization']['@type']
            assert auth_type == '/cosmos.bank.v1beta1.SendAuthorization'

    def test_grant_authorization_expiration_calculation(self):
        """Test expiration time calculation."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            with patch('time.time', return_value=1600000000):
                mock_result = Mock()
                mock_result.success = True
                mock_broadcast.return_value = mock_result

                self.client.grant_authorization(
                    self.mock_wallet,
                    "akash1grantee",
                    "/cosmos.bank.v1beta1.MsgSend",
                    expiration_days=30
                )

                call_args = mock_broadcast.call_args
                messages = call_args[1]['messages']
                expiration_seconds = int(messages[0]['grant']['expiration']['seconds'])

                expected = 1600000000 + (30 * 24 * 60 * 60)
                assert expiration_seconds == expected

    def test_revoke_authorization_success(self):
        """Test successful authorization revocation."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_result.tx_hash = "REVOKE123"
            mock_broadcast.return_value = mock_result

            result = self.client.revoke_authorization(
                self.mock_wallet,
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend"
            )

            assert result.success
            assert result.tx_hash == "REVOKE123"

            call_args = mock_broadcast.call_args
            messages = call_args[1]['messages']
            assert len(messages) == 1
            assert messages[0]['@type'] == '/cosmos.authz.v1beta1.MsgRevoke'
            assert messages[0]['granter'] == "akash1wallet"
            assert messages[0]['grantee'] == "akash1grantee"
            assert messages[0]['msg_type_url'] == "/cosmos.bank.v1beta1.MsgSend"

    def test_execute_authorized_messages(self):
        """Test executing authorized messages."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_result.tx_hash = "EXEC123"
            mock_broadcast.return_value = mock_result

            messages_to_execute = [
                {
                    "@type": "/cosmos.bank.v1beta1.MsgSend",
                    "from_address": "akash1granter",
                    "to_address": "akash1recipient",
                    "amount": [{"denom": "uakt", "amount": "1000000"}]
                }
            ]

            result = self.client.execute_authorized(
                self.mock_wallet,
                messages_to_execute
            )

            assert result.success
            assert result.tx_hash == "EXEC123"

            call_args = mock_broadcast.call_args
            messages = call_args[1]['messages']
            assert len(messages) == 1
            assert messages[0]['@type'] == '/cosmos.authz.v1beta1.MsgExec'
            assert messages[0]['grantee'] == "akash1wallet"
            assert messages[0]['msgs'] == messages_to_execute

    def test_transaction_error_handling(self):
        """Test transaction error handling."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_broadcast.side_effect = Exception("Broadcast failed")

            result = self.client.grant_authorization(
                self.mock_wallet,
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend"
            )

            assert not result.success
            assert result.code == -1
            assert "Grant authorization failed" in result.raw_log

    def test_gas_simulation_parameters(self):
        """Test gas simulation and fee parameters."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            self.client.grant_authorization(
                self.mock_wallet,
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend",
                fee_amount="10000",
                gas_limit=200000,
                use_simulation=False
            )

            call_args = mock_broadcast.call_args
            kwargs = call_args[1]
            assert kwargs['fee_amount'] == '10000'
            assert kwargs['gas_limit'] == 200000
            assert kwargs['use_simulation'] is False
            assert kwargs['gas_adjustment'] == 1.2
            assert kwargs['wait_for_confirmation'] is True


class TestAuthzUtilityFunctions:
    """Test AuthzUtils utility functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_akash_client = Mock()

        from akash.modules.authz.client import AuthzClient
        self.client = AuthzClient(self.mock_akash_client)

    def test_utils_mixin_included(self):
        """Test that utils mixin is properly included."""
        from akash.modules.authz.utils import AuthzUtils

        assert isinstance(self.client, AuthzUtils)


    def test_authorization_type_validation(self):
        """Test authorization type validation logic."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            test_cases = [
                ("send", "/any.message.type", "/cosmos.bank.v1beta1.SendAuthorization"),
                ("generic", "/cosmos.bank.v1beta1.MsgSend", "/cosmos.authz.v1beta1.GenericAuthorization")
            ]

            for auth_type, msg_type, expected_auth in test_cases:
                mock_broadcast.reset_mock()

                self.client.grant_authorization(
                    Mock(address="akash1test"),
                    "akash1grantee",
                    msg_type,
                    authorization_type=auth_type
                )

                call_args = mock_broadcast.call_args
                messages = call_args[1]['messages']
                actual_auth = messages[0]['grant']['authorization']['@type']
                assert actual_auth == expected_auth, f"Failed for {auth_type} with {msg_type}"

    def test_invalid_authorization_type_error(self):
        """Test that invalid authorization types raise appropriate errors."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"

        result = self.client.grant_authorization(
            mock_wallet,
            "akash1grantee",
            "/cosmos.bank.v1beta1.MsgSend",
            authorization_type="invalid"
        )

        assert not result.success
        assert result.code == -1
        assert "Invalid authorization_type: invalid" in result.raw_log
        assert "Must be 'send' or 'generic'" in result.raw_log


class TestAuthzErrorHandlingScenarios:
    """Test AuthzClient error handling in various scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_akash_client = Mock()

        from akash.modules.authz.client import AuthzClient
        self.client = AuthzClient(self.mock_akash_client)

    def test_query_network_failure(self):
        """Test handling of network failures during queries."""
        self.mock_akash_client.abci_query.side_effect = Exception("Connection timeout")

        with pytest.raises(Exception) as exc_info:
            self.client.get_grants("akash1granter")

        assert "Connection timeout" in str(exc_info.value) or "Failed to query grants" in str(exc_info.value)

    def test_query_invalid_response(self):
        """Test handling of invalid query responses."""
        self.mock_akash_client.abci_query.return_value = None
        result = self.client.get_grants("akash1granter")
        assert result == []

        self.mock_akash_client.abci_query.return_value = {"invalid": "response"}
        result = self.client.get_grants("akash1granter")
        assert result == []

    def test_protobuf_parsing_failure(self):
        """Test handling of protobuf parsing failures."""
        mock_response = {
            "response": {
                "code": 0,
                "value": base64.b64encode(b"invalid_protobuf_data").decode()
            }
        }
        self.mock_akash_client.abci_query.return_value = mock_response

        with pytest.raises(Exception):
            self.client.get_grants("akash1granter")

    def test_transaction_broadcast_failure(self):
        """Test handling of transaction broadcast failures."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_broadcast.side_effect = Exception("Insufficient funds")

            result = self.client.grant_authorization(
                Mock(address="akash1test"),
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend"
            )

            assert not result.success
            assert result.code == -1
            assert "Insufficient funds" in result.raw_log

    def test_invalid_addresses(self):
        """Test handling of invalid addresses."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = False
            mock_result.raw_log = "invalid address format"
            mock_broadcast.return_value = mock_result

            result = self.client.grant_authorization(
                Mock(address="invalid_address"),
                "also_invalid",
                "/cosmos.bank.v1beta1.MsgSend"
            )

            assert not result.success
            assert "invalid address format" in result.raw_log

    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"

        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            result = self.client.grant_authorization(
                mock_wallet,
                "akash1grantee",
                "/cosmos.bank.v1beta1.MsgSend"
            )

            assert result.success

            call_args = mock_broadcast.call_args
            kwargs = call_args[1]
            assert kwargs['fee_amount'] == '7000'
            assert kwargs['memo'] == ''

    def test_authorization_parsing_edge_cases(self):
        """Test edge cases in authorization parsing."""
        mock_response = {
            "response": {
                "code": 0,
                "value": base64.b64encode(b"mock_data").decode()
            }
        }
        self.mock_akash_client.abci_query.return_value = mock_response

        with patch('akash.proto.cosmos.authz.v1beta1.query_pb2.QueryGrantsResponse') as MockResponse:
            mock_response_obj = Mock()
            mock_grant = Mock()
            mock_grant.authorization.type_url = "/unknown.authorization.Type"
            mock_grant.expiration.seconds = 1700000000
            mock_grant.expiration.nanos = 0
            mock_response_obj.grants = [mock_grant]
            MockResponse.return_value = mock_response_obj

            result = self.client.get_grants("akash1granter")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]['authorization']['@type'] == '/unknown.authorization.Type'

    def test_concurrent_operation_safety(self):
        """Test safety of concurrent operations."""
        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            mock_wallet = Mock(address="akash1test")

            results = []
            for i in range(3):
                result = self.client.grant_authorization(
                    mock_wallet,
                    f"akash1grantee{i}",
                    "/cosmos.bank.v1beta1.MsgSend"
                )
                results.append(result)

            assert all(r.success for r in results)
            assert mock_broadcast.call_count == 3


if __name__ == '__main__':
    print("Running authz module validation tests")
    print("=" * 70)
    print()
    print("Testing protobuf structures, message converters, query responses,")
    print("parameter compatibility, and authorization grant/revoke patterns.")
    print()
    print("These tests catch breaking changes without blockchain interactions.")
    print()

    pytest.main([__file__, '-v'])
