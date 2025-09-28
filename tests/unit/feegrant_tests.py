#!/usr/bin/env python3
"""
Feegrant module tests - validation and functional tests.

Validation tests: Validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Functional tests: Test feegrant client query operations, transaction broadcasting,
fee allowance management, and utility functions using mocking to isolate functionality
and test error handling scenarios.

Run: python feegrant_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.proto.cosmos.feegrant.v1beta1 import feegrant_pb2 as feegrant_pb
from akash.proto.cosmos.feegrant.v1beta1 import tx_pb2 as feegrant_tx
from akash.proto.cosmos.feegrant.v1beta1 import query_pb2 as feegrant_query
from akash.proto.cosmos.base.v1beta1 import coin_pb2


class TestFeegrantMessageStructures:
    """Test feegrant protobuf message structures and field access."""

    def test_msg_grant_allowance_structure(self):
        """Test MsgGrantAllowance message structure and field access."""
        msg_grant = feegrant_tx.MsgGrantAllowance()

        required_fields = ['granter', 'grantee', 'allowance']
        for field in required_fields:
            assert hasattr(msg_grant, field), f"MsgGrantAllowance missing field: {field}"
        msg_grant.granter = "akash1granter"
        msg_grant.grantee = "akash1grantee"

        assert msg_grant.granter == "akash1granter"
        assert msg_grant.grantee == "akash1grantee"

        assert hasattr(msg_grant.allowance, 'type_url'), "Allowance missing type_url field"
        assert hasattr(msg_grant.allowance, 'value'), "Allowance missing value field"

    def test_msg_revoke_allowance_structure(self):
        """Test MsgRevokeAllowance message structure and field access."""
        msg_revoke = feegrant_tx.MsgRevokeAllowance()

        required_fields = ['granter', 'grantee']
        for field in required_fields:
            assert hasattr(msg_revoke, field), f"MsgRevokeAllowance missing field: {field}"
        msg_revoke.granter = "akash1granter"
        msg_revoke.grantee = "akash1grantee"

        assert msg_revoke.granter == "akash1granter"
        assert msg_revoke.grantee == "akash1grantee"

    def test_basic_allowance_structure(self):
        """Test BasicAllowance message structure and field access."""
        basic_allowance = feegrant_pb.BasicAllowance()

        required_fields = ['spend_limit', 'expiration']
        for field in required_fields:
            assert hasattr(basic_allowance, field), f"BasicAllowance missing field: {field}"
        coin = coin_pb2.Coin()
        coin.denom = "uakt"
        coin.amount = "1000000"
        basic_allowance.spend_limit.append(coin)

        assert len(basic_allowance.spend_limit) == 1
        assert basic_allowance.spend_limit[0].denom == "uakt"
        assert basic_allowance.spend_limit[0].amount == "1000000"

    def test_periodic_allowance_structure(self):
        """Test PeriodicAllowance message structure and field access."""
        periodic_allowance = feegrant_pb.PeriodicAllowance()

        required_fields = ['basic', 'period', 'period_spend_limit', 'period_can_spend', 'period_reset']
        for field in required_fields:
            assert hasattr(periodic_allowance, field), f"PeriodicAllowance missing field: {field}"
        assert hasattr(periodic_allowance.basic, 'spend_limit'), "Basic missing spend_limit field"
        assert hasattr(periodic_allowance.basic, 'expiration'), "Basic missing expiration field"

        assert hasattr(periodic_allowance.period, 'seconds'), "Period missing seconds field"
        assert hasattr(periodic_allowance.period, 'nanos'), "Period missing nanos field"

        coin = coin_pb2.Coin()
        coin.denom = "uakt"
        coin.amount = "500000"
        periodic_allowance.period_spend_limit.append(coin)

        assert len(periodic_allowance.period_spend_limit) == 1

    def test_allowed_msg_allowance_structure(self):
        """Test AllowedMsgAllowance message structure."""
        allowed_msg = feegrant_pb.AllowedMsgAllowance()

        required_fields = ['allowance', 'allowed_messages']
        for field in required_fields:
            assert hasattr(allowed_msg, field), f"AllowedMsgAllowance missing field: {field}"
        allowed_msg.allowed_messages.append("/cosmos.bank.v1beta1.MsgSend")
        allowed_msg.allowed_messages.append("/cosmos.staking.v1beta1.MsgDelegate")

        assert len(allowed_msg.allowed_messages) == 2
        assert allowed_msg.allowed_messages[0] == "/cosmos.bank.v1beta1.MsgSend"

    def test_grant_structure(self):
        """Test Grant message structure."""
        grant = feegrant_pb.Grant()

        required_fields = ['granter', 'grantee', 'allowance']
        for field in required_fields:
            assert hasattr(grant, field), f"Grant missing field: {field}"
        grant.granter = "akash1granter"
        grant.grantee = "akash1grantee"

        assert grant.granter == "akash1granter"
        assert grant.grantee == "akash1grantee"


class TestFeegrantQueryResponses:
    """Test feegrant query response structures."""

    def test_query_allowance_response_structure(self):
        """Test QueryAllowanceResponse structure."""
        response = feegrant_query.QueryAllowanceResponse()

        assert hasattr(response, 'allowance'), "QueryAllowanceResponse missing allowance field"
        grant = feegrant_pb.Grant()
        grant.granter = "akash1granter"
        grant.grantee = "akash1grantee"
        response.allowance.CopyFrom(grant)

        assert response.allowance.granter == "akash1granter"
        assert response.allowance.grantee == "akash1grantee"

    def test_query_allowances_response_structure(self):
        """Test QueryAllowancesResponse structure."""
        response = feegrant_query.QueryAllowancesResponse()

        assert hasattr(response, 'allowances'), "QueryAllowancesResponse missing allowances field"
        assert hasattr(response, 'pagination'), "QueryAllowancesResponse missing pagination field"
        grant = feegrant_pb.Grant()
        grant.granter = "akash1granter"
        grant.grantee = "akash1grantee"
        response.allowances.append(grant)

        assert len(response.allowances) == 1
        assert response.allowances[0].granter == "akash1granter"

    def test_query_allowances_by_granter_response_structure(self):
        """Test QueryAllowancesByGranterResponse structure."""
        response = feegrant_query.QueryAllowancesByGranterResponse()

        assert hasattr(response, 'allowances'), "QueryAllowancesByGranterResponse missing allowances field"
        assert hasattr(response, 'pagination'), "QueryAllowancesByGranterResponse missing pagination field"


class TestFeegrantMessageConverters:
    """Test feegrant message converters for transaction compatibility."""

    def test_all_feegrant_converters_registered(self):
        """Test that all feegrant message converters are registered."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        required_converters = [
            "/cosmos.feegrant.v1beta1.MsgGrantAllowance",
            "/cosmos.feegrant.v1beta1.MsgRevokeAllowance",
            "/cosmos.feegrant.v1beta1.BasicAllowance",
            "/cosmos.feegrant.v1beta1.PeriodicAllowance"
        ]

        for msg_type in required_converters:
            converter = _MESSAGE_CONVERTERS.get(msg_type)
            assert converter is not None, f"Missing converter for {msg_type}"
            assert callable(converter), f"Converter for {msg_type} is not callable"

    def test_msg_grant_allowance_protobuf_compatibility(self):
        """Test MsgGrantAllowance protobuf field compatibility."""
        pb_msg = feegrant_tx.MsgGrantAllowance()

        required_fields = ['granter', 'grantee', 'allowance']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgGrantAllowance missing field: {field}"
        pb_msg.granter = "akash1test"
        pb_msg.grantee = "akash1grantee"

        assert pb_msg.granter == "akash1test"
        assert pb_msg.grantee == "akash1grantee"

    def test_msg_revoke_allowance_protobuf_compatibility(self):
        """Test MsgRevokeAllowance protobuf field compatibility."""
        pb_msg = feegrant_tx.MsgRevokeAllowance()

        required_fields = ['granter', 'grantee']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgRevokeAllowance missing field: {field}"

    def test_basic_allowance_protobuf_compatibility(self):
        """Test BasicAllowance protobuf field compatibility."""
        pb_msg = feegrant_pb.BasicAllowance()

        required_fields = ['spend_limit', 'expiration']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"BasicAllowance missing field: {field}"

    def test_periodic_allowance_protobuf_compatibility(self):
        """Test PeriodicAllowance protobuf field compatibility."""
        pb_msg = feegrant_pb.PeriodicAllowance()

        required_fields = ['basic', 'period', 'period_spend_limit', 'period_can_spend', 'period_reset']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"PeriodicAllowance missing field: {field}"


class TestFeegrantQueryParameters:
    """Test feegrant query parameter compatibility."""

    def test_allowance_query_request_structures(self):
        """Test allowance query request structures."""
        allowance_req = feegrant_query.QueryAllowanceRequest()
        assert hasattr(allowance_req, 'granter'), "QueryAllowanceRequest missing granter field"
        assert hasattr(allowance_req, 'grantee'), "QueryAllowanceRequest missing grantee field"

        allowances_req = feegrant_query.QueryAllowancesRequest()
        assert hasattr(allowances_req, 'grantee'), "QueryAllowancesRequest missing grantee field"
        assert hasattr(allowances_req, 'pagination'), "QueryAllowancesRequest missing pagination field"

    def test_allowances_by_granter_query_request_structure(self):
        """Test allowances by granter query request structure."""
        granter_req = feegrant_query.QueryAllowancesByGranterRequest()
        assert hasattr(granter_req, 'granter'), "QueryAllowancesByGranterRequest missing granter field"
        assert hasattr(granter_req, 'pagination'), "QueryAllowancesByGranterRequest missing pagination field"


class TestFeegrantTransactionMessages:
    """Test feegrant transaction message structures."""

    def test_all_feegrant_message_types_exist(self):
        """Test all expected feegrant message types exist."""
        expected_messages = [
            'MsgGrantAllowance', 'MsgRevokeAllowance'
        ]

        for msg_name in expected_messages:
            assert hasattr(feegrant_tx, msg_name), f"Missing feegrant message type: {msg_name}"

            msg_class = getattr(feegrant_tx, msg_name)
            msg_instance = msg_class()
            assert msg_instance is not None

    def test_feegrant_message_response_types_exist(self):
        """Test feegrant message response types exist."""
        expected_responses = [
            'MsgGrantAllowanceResponse', 'MsgRevokeAllowanceResponse'
        ]

        for response_name in expected_responses:
            assert hasattr(feegrant_tx, response_name), f"Missing feegrant response type: {response_name}"

            response_class = getattr(feegrant_tx, response_name)
            response_instance = response_class()
            assert response_instance is not None

    def test_allowance_types_exist(self):
        """Test allowance types exist."""
        expected_allowances = [
            'BasicAllowance', 'PeriodicAllowance', 'AllowedMsgAllowance'
        ]

        for allowance_name in expected_allowances:
            assert hasattr(feegrant_pb, allowance_name), f"Missing allowance type: {allowance_name}"

            allowance_class = getattr(feegrant_pb, allowance_name)
            allowance_instance = allowance_class()
            assert allowance_instance is not None


class TestFeegrantErrorPatterns:
    """Test common feegrant error patterns and edge cases."""

    def test_empty_allowances_response_handling(self):
        """Test handling of empty allowances response."""
        response = feegrant_query.QueryAllowancesResponse()

        assert len(response.allowances) == 0, "Empty response should have no allowances"
        assert hasattr(response, 'pagination'), "Empty response missing pagination"

    def test_empty_spend_limit_handling(self):
        """Test handling of empty spend limit."""
        basic_allowance = feegrant_pb.BasicAllowance()

        assert len(basic_allowance.spend_limit) == 0, "BasicAllowance should start with empty spend_limit"
        coin = coin_pb2.Coin()
        coin.denom = "uakt"
        coin.amount = "1000000"
        basic_allowance.spend_limit.append(coin)

        assert len(basic_allowance.spend_limit) == 1

    def test_expired_allowance_handling(self):
        """Test handling of expired allowances."""
        basic_allowance = feegrant_pb.BasicAllowance()

        basic_allowance.expiration.seconds = 1600000000
        basic_allowance.expiration.nanos = 0

        assert basic_allowance.expiration.seconds == 1600000000
        assert basic_allowance.expiration.nanos == 0

    def test_zero_period_handling(self):
        """Test handling of zero period duration."""
        periodic_allowance = feegrant_pb.PeriodicAllowance()

        periodic_allowance.period.seconds = 0
        periodic_allowance.period.nanos = 0

        assert periodic_allowance.period.seconds == 0
        assert periodic_allowance.period.nanos == 0


class TestFeegrantModuleIntegration:
    """Test feegrant module integration and consistency."""

    def test_feegrant_converter_coverage(self):
        """Test all feegrant messages have converters in tx registry."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        expected_converters = ['MsgGrantAllowance', 'MsgRevokeAllowance', 'BasicAllowance', 'PeriodicAllowance']
        for msg_class in expected_converters:
            converter_key = f"/cosmos.feegrant.v1beta1.{msg_class}"
            assert converter_key in _MESSAGE_CONVERTERS, f"Missing converter for: {msg_class}"

    def test_feegrant_query_consistency(self):
        """Test feegrant query response consistency."""
        allowance_response = feegrant_query.QueryAllowanceResponse()
        allowances_response = feegrant_query.QueryAllowancesResponse()
        granter_response = feegrant_query.QueryAllowancesByGranterResponse()

        assert hasattr(allowance_response, 'allowance'), "Single allowance response missing allowance"
        assert hasattr(allowances_response, 'allowances'), "Multiple allowances response missing allowances"
        assert hasattr(granter_response, 'allowances'), "Granter allowances response missing allowances"

    def test_address_consistency(self):
        """Test address handling consistency across feegrant structures."""
        msg_grant = feegrant_tx.MsgGrantAllowance()
        msg_revoke = feegrant_tx.MsgRevokeAllowance()
        grant = feegrant_pb.Grant()

        test_granter = "akash1granter123"
        test_grantee = "akash1grantee123"

        msg_grant.granter = test_granter
        msg_grant.grantee = test_grantee

        msg_revoke.granter = test_granter
        msg_revoke.grantee = test_grantee

        grant.granter = test_granter
        grant.grantee = test_grantee

        assert msg_grant.granter == test_granter
        assert msg_grant.grantee == test_grantee
        assert msg_revoke.granter == test_granter
        assert msg_revoke.grantee == test_grantee
        assert grant.granter == test_granter
        assert grant.grantee == test_grantee

    def test_allowance_type_consistency(self):
        """Test allowance type consistency across messages."""
        msg_grant = feegrant_tx.MsgGrantAllowance()
        grant = feegrant_pb.Grant()

        assert hasattr(msg_grant.allowance, 'type_url'), "MsgGrantAllowance allowance missing type_url"
        assert hasattr(msg_grant.allowance, 'value'), "MsgGrantAllowance allowance missing value"
        assert hasattr(grant.allowance, 'type_url'), "Grant allowance missing type_url"
        assert hasattr(grant.allowance, 'value'), "Grant allowance missing value"

    def test_spend_limit_consistency(self):
        """Test spend limit consistency across allowance types."""
        basic_allowance = feegrant_pb.BasicAllowance()
        periodic_allowance = feegrant_pb.PeriodicAllowance()

        test_denom = "uakt"
        test_amount = "1000000"

        coin1 = coin_pb2.Coin()
        coin1.denom = test_denom
        coin1.amount = test_amount
        basic_allowance.spend_limit.append(coin1)

        coin2 = coin_pb2.Coin()
        coin2.denom = test_denom
        coin2.amount = test_amount
        periodic_allowance.period_spend_limit.append(coin2)

        assert len(basic_allowance.spend_limit) == 1
        assert len(periodic_allowance.period_spend_limit) == 1
        assert basic_allowance.spend_limit[0].denom == test_denom
        assert periodic_allowance.period_spend_limit[0].denom == test_denom


class TestFeegrantClientFunctionality:
    """Test feegrant client functional behavior with mocked responses."""

    def test_feegrant_client_creation(self):
        """Test feegrant client initialization."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        client = FeegrantClient(mock_client)

        assert hasattr(client, 'akash_client')
        assert client.akash_client == mock_client
        assert hasattr(client, 'get_allowance')
        assert hasattr(client, 'get_allowances')
        assert hasattr(client, 'grant_allowance')

    def test_get_allowance_method_structure(self):
        """Test get_allowance method accepts correct parameters."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        mock_client.abci_query.return_value = {'response': {'code': 0, 'value': None}}

        client = FeegrantClient(mock_client)

        result = client.get_allowance(
            granter="akash1granter",
            grantee="akash1grantee"
        )

        assert isinstance(result, dict)
        mock_client.abci_query.assert_called_once()

    def test_get_allowances_method_structure(self):
        """Test get_allowances method accepts correct parameters."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        mock_client.abci_query.return_value = {'response': {'code': 0, 'value': None}}

        client = FeegrantClient(mock_client)

        result = client.get_allowances(
            grantee="akash1grantee",
            limit=50
        )

        assert isinstance(result, list)
        mock_client.abci_query.assert_called_once()

    def test_get_allowances_by_granter_method(self):
        """Test get_allowances_by_granter method."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        mock_client.abci_query.return_value = {'response': {'code': 0, 'value': None}}

        client = FeegrantClient(mock_client)

        result = client.get_allowances_by_granter(
            granter="akash1granter",
            limit=100
        )

        assert isinstance(result, list)
        assert len(result) == 0
        mock_client.abci_query.assert_called_once()

    def test_transaction_methods_exist(self):
        """Test feegrant transaction methods exist and are callable."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        client = FeegrantClient(mock_client)

        assert hasattr(client, 'grant_allowance')
        assert hasattr(client, 'revoke_allowance')

        assert callable(client.grant_allowance)
        assert callable(client.revoke_allowance)

    def test_utility_methods_exist(self):
        """Test feegrant utility methods exist and are callable."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        client = FeegrantClient(mock_client)

        assert hasattr(client, 'create_basic_allowance')
        assert hasattr(client, 'create_periodic_allowance')

        assert callable(client.create_basic_allowance)
        assert callable(client.create_periodic_allowance)

    def test_create_basic_allowance_method(self):
        """Test create_basic_allowance utility method."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        client = FeegrantClient(mock_client)

        allowance = client.create_basic_allowance(
            spend_limit="1000000",
            denom="uakt"
        )

        assert isinstance(allowance, dict)
        assert allowance['@type'] == '/cosmos.feegrant.v1beta1.BasicAllowance'
        assert 'spend_limit' in allowance
        assert len(allowance['spend_limit']) == 1
        assert allowance['spend_limit'][0]['denom'] == 'uakt'
        assert allowance['spend_limit'][0]['amount'] == '1000000'

    def test_create_periodic_allowance_method(self):
        """Test create_periodic_allowance utility method."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        client = FeegrantClient(mock_client)

        allowance = client.create_periodic_allowance(
            total_limit="1000000",
            period_limit="100000",
            period_seconds=3600,
            denom="uakt"
        )

        assert isinstance(allowance, dict)
        assert allowance['@type'] == '/cosmos.feegrant.v1beta1.PeriodicAllowance'
        assert 'basic' in allowance
        assert 'period' in allowance
        assert 'period_spend_limit' in allowance


    def test_error_handling_patterns(self):
        """Test error handling in feegrant methods."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()

        mock_client.abci_query.side_effect = Exception("Network error")

        client = FeegrantClient(mock_client)

        with pytest.raises(Exception):
            client.get_allowance("akash1granter", "akash1grantee")

        with pytest.raises(Exception):
            client.get_allowances("akash1grantee")

        with pytest.raises(Exception):
            client.get_allowances_by_granter("akash1granter")

    def test_abci_query_path_usage(self):
        """Test that methods use correct ABCI query paths."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        mock_client.abci_query.return_value = {'response': {'code': 0, 'value': None}}

        client = FeegrantClient(mock_client)

        client.get_allowance("akash1granter", "akash1grantee")
        args, kwargs = mock_client.abci_query.call_args
        assert kwargs['path'] == '/cosmos.feegrant.v1beta1.Query/Allowance'

        mock_client.abci_query.reset_mock()

        client.get_allowances("akash1grantee")
        args, kwargs = mock_client.abci_query.call_args
        assert kwargs['path'] == '/cosmos.feegrant.v1beta1.Query/Allowances'

        mock_client.abci_query.reset_mock()

        client.get_allowances_by_granter("akash1granter")
        args, kwargs = mock_client.abci_query.call_args
        assert kwargs['path'] == '/cosmos.feegrant.v1beta1.Query/AllowancesByGranter'


class TestFeegrantTransactionFunctionality:
    """Test feegrant transaction functionality."""

    def test_grant_allowance_transaction_structure(self):
        """Test grant_allowance transaction method structure."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock, patch

        mock_client = Mock()
        client = FeegrantClient(mock_client)

        mock_wallet = Mock()
        mock_wallet.address = "akash1granter"

        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.tx_hash = "test_hash"
            mock_result.code = 0
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            result = client.grant_allowance(
                wallet=mock_wallet,
                grantee="akash1grantee",
                allowance_type="basic",
                spend_limit="1000000",
                denom="uakt",
                memo="Test grant"
            )

            mock_broadcast.assert_called_once()
            assert result.success

    def test_revoke_allowance_transaction_structure(self):
        """Test revoke_allowance transaction method structure."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock, patch

        mock_client = Mock()
        client = FeegrantClient(mock_client)

        mock_wallet = Mock()
        mock_wallet.address = "akash1granter"

        with patch('akash.tx.broadcast_transaction_rpc') as mock_broadcast:
            mock_result = Mock()
            mock_result.tx_hash = "test_hash"
            mock_result.code = 0
            mock_result.success = True
            mock_broadcast.return_value = mock_result

            result = client.revoke_allowance(
                wallet=mock_wallet,
                grantee="akash1grantee",
                memo="Test revoke"
            )

            mock_broadcast.assert_called_once()
            assert result.success


class TestFeegrantErrorScenarios:
    """Test feegrant error handling and edge cases."""

    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        mock_client.abci_query.return_value = None

        client = FeegrantClient(mock_client)

        result = client.get_allowance("akash1granter", "akash1grantee")
        assert result == {}

        result = client.get_allowances("akash1grantee")
        assert result == []

    def test_invalid_response_handling(self):
        """Test handling of invalid API responses."""
        from akash.modules.feegrant.client import FeegrantClient
        from unittest.mock import Mock

        mock_client = Mock()
        mock_client.abci_query.return_value = {'invalid': 'response'}

        client = FeegrantClient(mock_client)

        result = client.get_allowances_by_granter("akash1granter")
        assert result == []



if __name__ == '__main__':
    print("✅ Running feegrant module validation tests")
    print("=" * 70)
    print()
    print("Testing protobuf structures, message converters, query responses,")
    print("parameter compatibility, fee allowance grant/revoke patterns,")
    print("and functional client behavior.")
    print()
    print("These tests catch breaking changes without blockchain interactions.")
    print()

    pytest.main([__file__, '-v'])
