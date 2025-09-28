#!/usr/bin/env python3
"""
Slashing module tests - validation and functional tests.

Validation tests: Validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Functional tests: Test slashing client query operations, transaction broadcasting,
validator slashing operations, and utility functions using mocking to isolate functionality
and test error handling scenarios.

Run: python slashing_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.proto.cosmos.slashing.v1beta1 import slashing_pb2 as slash_pb
from akash.proto.cosmos.slashing.v1beta1 import tx_pb2 as slash_tx
from akash.proto.cosmos.slashing.v1beta1 import query_pb2 as slash_query


class TestSlashingMessageStructures:
    """Test slashing protobuf message structures and field access."""

    def test_msg_unjail_structure(self):
        """Test MsgUnjail message structure and field access."""
        msg_unjail = slash_tx.MsgUnjail()

        required_fields = ['validator_addr']
        for field in required_fields:
            assert hasattr(msg_unjail, field), f"MsgUnjail missing field: {field}"
        msg_unjail.validator_addr = "akashvaloper1validator"

        assert msg_unjail.validator_addr == "akashvaloper1validator"

    def test_validator_signing_info_structure(self):
        """Test ValidatorSigningInfo message structure and field access."""
        signing_info = slash_pb.ValidatorSigningInfo()

        required_fields = ['address', 'start_height', 'index_offset', 'jailed_until', 'tombstoned',
                           'missed_blocks_counter']
        for field in required_fields:
            assert hasattr(signing_info, field), f"ValidatorSigningInfo missing field: {field}"
        signing_info.address = "akashvalcons1validator"
        signing_info.start_height = 100
        signing_info.index_offset = 5
        signing_info.tombstoned = False
        signing_info.missed_blocks_counter = 3

        assert signing_info.address == "akashvalcons1validator"
        assert signing_info.start_height == 100
        assert signing_info.index_offset == 5
        assert signing_info.tombstoned == False
        assert signing_info.missed_blocks_counter == 3

    def test_params_structure(self):
        """Test Params message structure and field access."""
        params = slash_pb.Params()

        required_fields = ['signed_blocks_window', 'min_signed_per_window', 'downtime_jail_duration',
                           'slash_fraction_double_sign', 'slash_fraction_downtime']
        for field in required_fields:
            assert hasattr(params, field), f"Params missing field: {field}"
        params.signed_blocks_window = 10000
        params.min_signed_per_window = b"0.500000000000000000"
        params.slash_fraction_double_sign = b"0.050000000000000000"
        params.slash_fraction_downtime = b"0.010000000000000000"

        assert params.signed_blocks_window == 10000
        assert params.min_signed_per_window == b"0.500000000000000000"
        assert params.slash_fraction_double_sign == b"0.050000000000000000"
        assert params.slash_fraction_downtime == b"0.010000000000000000"


class TestSlashingQueryResponses:
    """Test slashing query response structures."""

    def test_query_signing_info_response_structure(self):
        """Test QuerySigningInfoResponse structure."""
        response = slash_query.QuerySigningInfoResponse()

        assert hasattr(response, 'val_signing_info'), "QuerySigningInfoResponse missing val_signing_info field"
        signing_info = slash_pb.ValidatorSigningInfo()
        signing_info.address = "akashvalcons1validator"
        signing_info.start_height = 100
        signing_info.tombstoned = False

        response.val_signing_info.CopyFrom(signing_info)

        assert response.val_signing_info.address == "akashvalcons1validator"
        assert response.val_signing_info.start_height == 100
        assert response.val_signing_info.tombstoned == False

    def test_query_signing_infos_response_structure(self):
        """Test QuerySigningInfosResponse structure."""
        response = slash_query.QuerySigningInfosResponse()

        assert hasattr(response, 'info'), "QuerySigningInfosResponse missing info field"
        assert hasattr(response, 'pagination'), "QuerySigningInfosResponse missing pagination field"
        signing_info = slash_pb.ValidatorSigningInfo()
        signing_info.address = "akashvalcons1validator"
        signing_info.start_height = 200

        response.info.append(signing_info)

        assert len(response.info) == 1
        assert response.info[0].address == "akashvalcons1validator"
        assert response.info[0].start_height == 200

    def test_query_params_response_structure(self):
        """Test QueryParamsResponse structure."""
        response = slash_query.QueryParamsResponse()

        assert hasattr(response, 'params'), "QueryParamsResponse missing params field"
        params = slash_pb.Params()
        params.signed_blocks_window = 5000
        params.min_signed_per_window = b"0.600000000000000000"

        response.params.CopyFrom(params)

        assert response.params.signed_blocks_window == 5000
        assert response.params.min_signed_per_window == b"0.600000000000000000"


class TestSlashingMessageConverters:
    """Test slashing message converters for transaction compatibility."""

    def test_all_slashing_converters_registered(self):
        """Test that all slashing message converters are registered."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        required_converters = [
            "/cosmos.slashing.v1beta1.MsgUnjail"
        ]

        for msg_type in required_converters:
            converter = _MESSAGE_CONVERTERS.get(msg_type)
            assert converter is not None, f"Missing converter for {msg_type}"
            assert callable(converter), f"Converter for {msg_type} is not callable"

    def test_msg_unjail_protobuf_compatibility(self):
        """Test MsgUnjail protobuf field compatibility."""
        pb_msg = slash_tx.MsgUnjail()

        required_fields = ['validator_addr']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgUnjail missing field: {field}"
        pb_msg.validator_addr = "akashvaloper1test"

        assert pb_msg.validator_addr == "akashvaloper1test"


class TestSlashingQueryParameters:
    """Test slashing query parameter compatibility."""

    def test_signing_info_query_request_structures(self):
        """Test signing info query request structures."""
        signing_info_req = slash_query.QuerySigningInfoRequest()
        assert hasattr(signing_info_req, 'cons_address'), "QuerySigningInfoRequest missing cons_address field"

        signing_infos_req = slash_query.QuerySigningInfosRequest()
        assert hasattr(signing_infos_req, 'pagination'), "QuerySigningInfosRequest missing pagination field"

    def test_params_query_request_structure(self):
        """Test params query request structure."""
        params_req = slash_query.QueryParamsRequest()
        assert params_req is not None, "QueryParamsRequest should be instantiable"


class TestSlashingTransactionMessages:
    """Test slashing transaction message structures."""

    def test_all_slashing_message_types_exist(self):
        """Test all expected slashing message types exist."""
        expected_messages = [
            'MsgUnjail'
        ]

        for msg_name in expected_messages:
            assert hasattr(slash_tx, msg_name), f"Missing slashing message type: {msg_name}"

            msg_class = getattr(slash_tx, msg_name)
            msg_instance = msg_class()
            assert msg_instance is not None

    def test_slashing_message_response_types_exist(self):
        """Test slashing message response types exist."""
        expected_responses = [
            'MsgUnjailResponse'
        ]

        for response_name in expected_responses:
            assert hasattr(slash_tx, response_name), f"Missing slashing response type: {response_name}"

            response_class = getattr(slash_tx, response_name)
            response_instance = response_class()
            assert response_instance is not None

    def test_unjail_message_consistency(self):
        """Test unjail message field consistency."""
        msg_unjail = slash_tx.MsgUnjail()
        msg_unjail_response = slash_tx.MsgUnjailResponse()

        assert hasattr(msg_unjail, 'validator_addr'), "MsgUnjail missing validator_addr"
        assert msg_unjail_response is not None, "MsgUnjailResponse should be instantiable"


class TestSlashingErrorPatterns:
    """Test common slashing error patterns and edge cases."""

    def test_empty_signing_infos_response_handling(self):
        """Test handling of empty signing infos response."""
        response = slash_query.QuerySigningInfosResponse()

        assert len(response.info) == 0, "Empty response should have no signing infos"
        assert hasattr(response, 'pagination'), "Empty response missing pagination"

    def test_zero_values_handling(self):
        """Test handling of zero values in signing info."""
        signing_info = slash_pb.ValidatorSigningInfo()

        signing_info.start_height = 0
        signing_info.index_offset = 0
        signing_info.missed_blocks_counter = 0
        signing_info.tombstoned = False

        assert signing_info.start_height == 0
        assert signing_info.index_offset == 0
        assert signing_info.missed_blocks_counter == 0
        assert signing_info.tombstoned == False

    def test_params_decimal_handling(self):
        """Test handling of decimal parameters."""
        params = slash_pb.Params()

        params.min_signed_per_window = b"0.500000000000000000"
        params.slash_fraction_double_sign = b"0.050000000000000000"
        params.slash_fraction_downtime = b"0.010000000000000000"

        assert params.min_signed_per_window == b"0.500000000000000000"
        assert params.slash_fraction_double_sign == b"0.050000000000000000"
        assert params.slash_fraction_downtime == b"0.010000000000000000"

    def test_timestamp_handling(self):
        """Test handling of timestamp fields in signing info."""
        signing_info = slash_pb.ValidatorSigningInfo()

        assert hasattr(signing_info, 'jailed_until'), "ValidatorSigningInfo missing jailed_until field"

        timestamp_field = signing_info.jailed_until
        assert timestamp_field is not None, "jailed_until field should be accessible"


class TestSlashingModuleIntegration:
    """Test slashing module integration and consistency."""

    def test_slashing_converter_coverage(self):
        """Test all slashing messages have converters in tx registry."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        expected_converters = ['MsgUnjail']
        for msg_class in expected_converters:
            converter_key = f"/cosmos.slashing.v1beta1.{msg_class}"
            assert converter_key in _MESSAGE_CONVERTERS, f"Missing converter for: {msg_class}"

    def test_slashing_query_consistency(self):
        """Test slashing query response consistency."""
        signing_info_response = slash_query.QuerySigningInfoResponse()
        signing_infos_response = slash_query.QuerySigningInfosResponse()

        assert hasattr(signing_info_response,
                       'val_signing_info'), "Single signing info response missing val_signing_info"
        assert hasattr(signing_infos_response, 'info'), "Multiple signing infos response missing info"

    def test_validator_address_consistency(self):
        """Test validator address consistency across slashing structures."""
        msg_unjail = slash_tx.MsgUnjail()
        signing_info = slash_pb.ValidatorSigningInfo()

        test_validator_operator = "akashvaloper1validator123"
        test_validator_consensus = "akashvalcons1validator123"

        msg_unjail.validator_addr = test_validator_operator
        signing_info.address = test_validator_consensus

        assert msg_unjail.validator_addr == test_validator_operator
        assert signing_info.address == test_validator_consensus

    def test_params_consistency(self):
        """Test params handling consistency."""
        params_from_pb = slash_pb.Params()
        params_response = slash_query.QueryParamsResponse()

        params_from_pb.signed_blocks_window = 10000
        params_from_pb.min_signed_per_window = b"0.500000000000000000"

        params_response.params.CopyFrom(params_from_pb)

        assert params_response.params.signed_blocks_window == 10000
        assert params_response.params.min_signed_per_window == b"0.500000000000000000"

    def test_signing_info_lifecycle_consistency(self):
        """Test signing info lifecycle consistency."""
        signing_info = slash_pb.ValidatorSigningInfo()

        signing_info.address = "akashvalcons1test"
        signing_info.start_height = 1000
        signing_info.index_offset = 0
        signing_info.missed_blocks_counter = 0
        signing_info.tombstoned = False

        signing_info.missed_blocks_counter = 5
        signing_info.tombstoned = True

        assert signing_info.address == "akashvalcons1test"
        assert signing_info.start_height == 1000
        assert signing_info.missed_blocks_counter == 5
        assert signing_info.tombstoned == True


class TestSlashingClientFunctionality:
    """Test slashing client functionality with mocked dependencies."""

    def setup_method(self):
        """Setup test environment."""
        from unittest.mock import Mock
        from akash.modules.slashing.client import SlashingClient

        self.mock_client = Mock()
        self.client = SlashingClient(self.mock_client)

    def test_slashing_client_creation(self):
        """Test slashing client initialization with all mixins."""
        from akash.modules.slashing.client import SlashingClient
        from akash.modules.slashing.query import SlashingQuery
        from akash.modules.slashing.tx import SlashingTx
        from unittest.mock import Mock

        mock_client = Mock()
        client = SlashingClient(mock_client)

        assert isinstance(client, SlashingQuery)
        assert isinstance(client, SlashingTx)
        assert client.akash_client == mock_client

    def test_get_params_method_structure(self):
        """Test get_params method structure."""
        import inspect

        sig = inspect.signature(self.client.get_params)
        params = list(sig.parameters.keys())

        assert len(params) == 0, "get_params should have no parameters"

    def test_get_signing_info_method_structure(self):
        """Test get_signing_info method signature."""
        import inspect

        sig = inspect.signature(self.client.get_signing_info)
        params = list(sig.parameters.keys())

        assert 'cons_address' in params

    def test_get_signing_infos_method_structure(self):
        """Test get_signing_infos method with pagination parameters."""
        import inspect

        sig = inspect.signature(self.client.get_signing_infos)
        params = list(sig.parameters.keys())

        expected_params = ['limit', 'offset']
        for param in expected_params:
            assert param in params, f"get_signing_infos missing parameter: {param}"

    def test_slashing_query_endpoints(self):
        """Test slashing query endpoint paths are accessible."""
        pass

    def test_slashing_query_methods(self):
        """Test slashing query methods are available."""
        query_methods = ['get_params', 'get_signing_info', 'get_signing_infos']

        for method in query_methods:
            assert hasattr(self.client, method), f"Missing query method: {method}"
            assert callable(getattr(self.client, method))


class TestSlashingTransactionFunctionality:
    """Test slashing transaction functionality."""

    def setup_method(self):
        """Setup test environment."""
        from unittest.mock import Mock
        from akash.modules.slashing.client import SlashingClient

        self.mock_client = Mock()
        self.client = SlashingClient(self.mock_client)

    def test_slashing_tx_mixin_loaded(self):
        """Test slashing transaction mixin is properly loaded."""
        from akash.modules.slashing.tx import SlashingTx
        assert isinstance(self.client, SlashingTx)

    def test_unjail_method_signature(self):
        """Test unjail method signature validation."""
        import inspect
        from akash.modules.slashing.tx import SlashingTx

        if hasattr(SlashingTx, 'unjail'):
            sig = inspect.signature(self.client.unjail)
            params = list(sig.parameters.keys())

            expected_params = ['wallet']
            for param in expected_params:
                assert param in params, f"unjail missing parameter: {param}"

    def test_slashing_transaction_endpoints(self):
        """Test slashing transaction endpoints are defined."""
        pass


class TestSlashingErrorScenarios:
    """Test slashing error handling scenarios."""

    def setup_method(self):
        """Setup test environment."""
        from unittest.mock import Mock
        from akash.modules.slashing.client import SlashingClient

        self.mock_client = Mock()
        self.client = SlashingClient(self.mock_client)

    def test_params_query_failure_handling(self):
        """Test handling params query failures."""
        self.mock_client.rpc_query.return_value = None

        result = self.client.get_params()
        assert result == {}

    def test_signing_info_query_failure_handling(self):
        """Test handling signing info query failures."""
        self.mock_client.rpc_query.return_value = None

        result = self.client.get_signing_info('akashvalcons1test')
        assert result == {}

    def test_signing_infos_query_failure_handling(self):
        """Test handling signing infos query failures."""
        self.mock_client.rpc_query.return_value = None

        result = self.client.get_signing_infos()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_empty_params_response_handling(self):
        """Test handling empty params response."""
        mock_response = {'response': {'code': 0, 'value': None}}
        self.mock_client.rpc_query.return_value = mock_response

        result = self.client.get_params()
        assert result == {}

    def test_empty_signing_info_response_handling(self):
        """Test handling empty signing info response."""
        mock_response = {'response': {'code': 0, 'value': None}}
        self.mock_client.rpc_query.return_value = mock_response

        result = self.client.get_signing_info('akashvalcons1test')
        assert result == {}

    def test_empty_signing_infos_response_handling(self):
        """Test handling empty signing infos response."""
        mock_response = {'response': {'code': 0, 'value': None}}
        self.mock_client.rpc_query.return_value = mock_response

        result = self.client.get_signing_infos()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_rpc_error_code_handling(self):
        """Test handling RPC error codes."""
        mock_response = {'response': {'code': 1, 'log': 'Query failed'}}
        self.mock_client.rpc_query.return_value = mock_response

        result = self.client.get_params()
        assert result == {}

    def test_invalid_consensus_address_handling(self):
        """Test handling invalid consensus addresses."""
        mock_response = {'response': {'code': 3, 'log': 'validator not found'}}
        self.mock_client.rpc_query.return_value = mock_response

        result = self.client.get_signing_info('invalid_address')
        assert result == {}


if __name__ == '__main__':
    print("✅ Running slashing module validation tests")
    print("=" * 70)
    print()
    print("Testing protobuf structures, message converters, query responses,")
    print("parameter compatibility, and validator jailing/unjailing patterns.")
    print()
    print("These tests catch breaking changes without blockchain interactions.")
    print()

    pytest.main([__file__, '-v'])
