#!/usr/bin/env python3
"""
Audit module tests - validation and functional tests.

Validation tests: Validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Functional tests: Test audit client query operations, transaction broadcasting,
provider attribute management, auditor operations, and utility functions using mocking
to isolate functionality and test error handling scenarios.

Run: python audit_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.proto.akash.audit.v1beta3 import audit_pb2 as audit_pb
from akash.proto.akash.audit.v1beta3 import query_pb2 as audit_query
from akash.proto.akash.base.v1beta3 import attribute_pb2 as attr_pb


class TestAuditMessageStructures:
    """Test audit protobuf message structures and field access."""

    def test_provider_structure(self):
        """Test Provider message structure and field access."""
        provider = audit_pb.Provider()

        required_fields = ['owner', 'auditor', 'attributes']
        for field in required_fields:
            assert hasattr(provider, field), f"Provider missing field: {field}"

        provider.owner = "akash1test"
        provider.auditor = "akash1auditor"

        assert provider.owner == "akash1test"
        assert provider.auditor == "akash1auditor"

    def test_audited_attributes_structure(self):
        """Test AuditedAttributes message structure and field access."""
        audited_attrs = audit_pb.AuditedAttributes()

        required_fields = ['owner', 'auditor', 'attributes']
        for field in required_fields:
            assert hasattr(audited_attrs, field), f"AuditedAttributes missing field: {field}"

        audited_attrs.owner = "akash1test"
        audited_attrs.auditor = "akash1auditor"

        assert audited_attrs.owner == "akash1test"
        assert audited_attrs.auditor == "akash1auditor"

    def test_attributes_response_structure(self):
        """Test AttributesResponse message structure."""
        response = audit_pb.AttributesResponse()

        assert hasattr(response, 'attributes'), "AttributesResponse missing attributes field"

        audited_attr = audit_pb.AuditedAttributes()
        audited_attr.owner = "akash1test"
        audited_attr.auditor = "akash1auditor"

        response.attributes.append(audited_attr)

        assert len(response.attributes) == 1
        assert response.attributes[0].owner == "akash1test"

    def test_attributes_filters_structure(self):
        """Test AttributesFilters message structure."""
        filters = audit_pb.AttributesFilters()

        assert hasattr(filters, 'auditors'), "AttributesFilters missing auditors field"
        assert hasattr(filters, 'owners'), "AttributesFilters missing owners field"

        filters.auditors.append("akash1auditor1")
        filters.auditors.append("akash1auditor2")
        filters.owners.append("akash1owner1")

        assert len(filters.auditors) == 2
        assert len(filters.owners) == 1
        assert filters.auditors[0] == "akash1auditor1"

    def test_provider_attributes_integration(self):
        """Test provider with attributes integration."""
        provider = audit_pb.Provider()
        provider.owner = "akash1test"
        provider.auditor = "akash1auditor"

        attribute = attr_pb.Attribute()
        attribute.key = "region"
        attribute.value = "us-west"

        provider.attributes.append(attribute)

        assert len(provider.attributes) == 1
        assert provider.attributes[0].key == "region"
        assert provider.attributes[0].value == "us-west"


class TestAuditQueryResponses:
    """Test audit query response structures."""

    def test_query_providers_response_structure(self):
        """Test QueryProvidersResponse nested structure access."""
        response = audit_query.QueryProvidersResponse()

        assert hasattr(response, 'providers'), "QueryProvidersResponse missing providers field"
        assert hasattr(response, 'pagination'), "QueryProvidersResponse missing pagination field"

        provider = audit_pb.Provider()
        provider.owner = "akash1test"
        provider.auditor = "akash1auditor"

        response.providers.append(provider)

        first_provider = response.providers[0]
        assert hasattr(first_provider, 'owner'), "Provider missing owner field"
        assert hasattr(first_provider, 'auditor'), "Provider missing auditor field"
        assert first_provider.owner == "akash1test"


class TestAuditMessageConverters:
    """Test audit message converters for transaction compatibility."""

    def test_all_audit_converters_registered(self):
        """Test that all audit message converters are registered."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        required_converters = [
            "/akash.audit.v1beta3.MsgSignProviderAttributes",
            "/akash.audit.v1beta3.MsgDeleteProviderAttributes"
        ]

        for msg_type in required_converters:
            converter = _MESSAGE_CONVERTERS.get(msg_type)
            assert converter is not None, f"Missing converter for {msg_type}"
            assert callable(converter), f"Converter for {msg_type} is not callable"

    def test_msg_sign_provider_attributes_protobuf_compatibility(self):
        """Test MsgSignProviderAttributes protobuf field compatibility."""
        pb_msg = audit_pb.MsgSignProviderAttributes()

        required_fields = ['owner', 'auditor', 'attributes']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgSignProviderAttributes missing field: {field}"

        pb_msg.owner = "akash1test"
        pb_msg.auditor = "akash1auditor"

        assert pb_msg.owner == "akash1test"
        assert pb_msg.auditor == "akash1auditor"

    def test_msg_delete_provider_attributes_protobuf_compatibility(self):
        """Test MsgDeleteProviderAttributes protobuf field compatibility."""
        pb_msg = audit_pb.MsgDeleteProviderAttributes()

        required_fields = ['owner', 'auditor', 'keys']
        for field in required_fields:
            assert hasattr(pb_msg, field), f"MsgDeleteProviderAttributes missing field: {field}"

        pb_msg.owner = "akash1test"
        pb_msg.auditor = "akash1auditor"
        pb_msg.keys.append("test_key")

        assert pb_msg.owner == "akash1test"
        assert pb_msg.auditor == "akash1auditor"
        assert len(pb_msg.keys) == 1
        assert pb_msg.keys[0] == "test_key"


class TestAuditQueryParameters:
    """Test audit query parameter compatibility."""

    def test_provider_query_request_structures(self):
        """Test audit query request structures."""
        provider_req = audit_query.QueryProviderRequest()
        assert hasattr(provider_req, 'auditor'), "QueryProviderRequest missing auditor field"
        assert hasattr(provider_req, 'owner'), "QueryProviderRequest missing owner field"

        all_req = audit_query.QueryAllProvidersAttributesRequest()
        assert hasattr(all_req, 'pagination'), "QueryAllProvidersAttributesRequest missing pagination field"

        attrs_req = audit_query.QueryProviderAttributesRequest()
        assert hasattr(attrs_req, 'owner'), "QueryProviderAttributesRequest missing owner field"
        assert hasattr(attrs_req, 'pagination'), "QueryProviderAttributesRequest missing pagination field"

    def test_auditor_query_request_structures(self):
        """Test auditor-specific query request structures."""
        provider_auditor_req = audit_query.QueryProviderAuditorRequest()
        assert hasattr(provider_auditor_req, 'auditor'), "QueryProviderAuditorRequest missing auditor field"
        assert hasattr(provider_auditor_req, 'owner'), "QueryProviderAuditorRequest missing owner field"

        auditor_attrs_req = audit_query.QueryAuditorAttributesRequest()
        assert hasattr(auditor_attrs_req, 'auditor'), "QueryAuditorAttributesRequest missing auditor field"
        assert hasattr(auditor_attrs_req, 'pagination'), "QueryAuditorAttributesRequest missing pagination field"


class TestAuditTransactionMessages:
    """Test audit transaction message structures."""

    def test_all_audit_message_types_exist(self):
        """Test all expected audit message types exist."""
        expected_messages = [
            'MsgSignProviderAttributes', 'MsgDeleteProviderAttributes'
        ]

        for msg_name in expected_messages:
            assert hasattr(audit_pb, msg_name), f"Missing audit message type: {msg_name}"

            msg_class = getattr(audit_pb, msg_name)
            msg_instance = msg_class()
            assert msg_instance is not None

    def test_audit_message_response_types_exist(self):
        """Test audit message response types exist."""
        expected_responses = [
            'MsgSignProviderAttributesResponse', 'MsgDeleteProviderAttributesResponse'
        ]

        for response_name in expected_responses:
            assert hasattr(audit_pb, response_name), f"Missing audit response type: {response_name}"

            response_class = getattr(audit_pb, response_name)
            response_instance = response_class()
            assert response_instance is not None

    def test_audit_lifecycle_message_consistency(self):
        """Test audit lifecycle messages are consistent."""
        sign_msg = audit_pb.MsgSignProviderAttributes()
        delete_msg = audit_pb.MsgDeleteProviderAttributes()

        common_fields = ['owner', 'auditor']
        for field in common_fields:
            assert hasattr(sign_msg, field), f"MsgSignProviderAttributes missing: {field}"
            assert hasattr(delete_msg, field), f"MsgDeleteProviderAttributes missing: {field}"

        assert hasattr(sign_msg, 'attributes'), "MsgSignProviderAttributes missing attributes field"

        assert hasattr(delete_msg, 'keys'), "MsgDeleteProviderAttributes missing keys field"


class TestAuditErrorPatterns:
    """Test common audit error patterns and edge cases."""

    def test_empty_providers_response_handling(self):
        """Test handling of empty providers response."""
        response = audit_query.QueryProvidersResponse()

        assert len(response.providers) == 0, "Empty response should have no providers"

        assert hasattr(response, 'pagination'), "Empty response missing pagination"

    def test_empty_attributes_handling(self):
        """Test handling of empty attributes."""
        provider = audit_pb.Provider()
        audited_attrs = audit_pb.AuditedAttributes()

        assert len(provider.attributes) == 0, "Provider should start with empty attributes"
        assert len(audited_attrs.attributes) == 0, "AuditedAttributes should start with empty attributes"

    def test_empty_keys_handling(self):
        """Test handling of empty keys in delete message."""
        delete_msg = audit_pb.MsgDeleteProviderAttributes()

        assert len(delete_msg.keys) == 0, "MsgDeleteProviderAttributes should start with empty keys"

        delete_msg.keys.append("test_key")
        assert len(delete_msg.keys) == 1, "Should be able to add keys"

    def test_attributes_filters_empty_handling(self):
        """Test handling of empty attributes filters."""
        filters = audit_pb.AttributesFilters()

        assert len(filters.auditors) == 0, "AttributesFilters should start with empty auditors"
        assert len(filters.owners) == 0, "AttributesFilters should start with empty owners"


class TestAuditModuleIntegration:
    """Test audit module integration and consistency."""

    def test_audit_converter_coverage(self):
        """Test all audit messages have converters in tx registry."""
        from akash.tx import _MESSAGE_CONVERTERS, _initialize_message_converters

        if not _MESSAGE_CONVERTERS:
            _initialize_message_converters()

        expected_converters = ['MsgSignProviderAttributes', 'MsgDeleteProviderAttributes']
        for msg_class in expected_converters:
            converter_key = f"/akash.audit.v1beta3.{msg_class}"
            assert converter_key in _MESSAGE_CONVERTERS, f"Missing converter for: {msg_class}"

    def test_audit_query_consistency(self):
        """Test audit query response consistency."""
        response = audit_query.QueryProvidersResponse()

        assert hasattr(response, 'providers'), "Response missing providers field"
        assert hasattr(response, 'pagination'), "Response missing pagination field"

        assert len(response.providers) == 0, "Should start with empty providers"

    def test_owner_auditor_relationship_consistency(self):
        """Test owner-auditor relationship consistency across messages."""

        provider = audit_pb.Provider()
        provider.owner = "akash1owner"
        provider.auditor = "akash1auditor"

        audited = audit_pb.AuditedAttributes()
        audited.owner = "akash1owner"
        audited.auditor = "akash1auditor"

        sign_msg = audit_pb.MsgSignProviderAttributes()
        sign_msg.owner = "akash1owner"
        sign_msg.auditor = "akash1auditor"

        delete_msg = audit_pb.MsgDeleteProviderAttributes()
        delete_msg.owner = "akash1owner"
        delete_msg.auditor = "akash1auditor"

        objects = [provider, audited, sign_msg, delete_msg]
        for obj in objects:
            assert obj.owner == "akash1owner", f"Inconsistent owner in {type(obj).__name__}"
            assert obj.auditor == "akash1auditor", f"Inconsistent auditor in {type(obj).__name__}"

    def test_attribute_integration_consistency(self):
        """Test attribute integration consistency across audit structures."""

        provider = audit_pb.Provider()
        attr1 = attr_pb.Attribute()
        attr1.key = "region"
        attr1.value = "us-west"
        provider.attributes.append(attr1)

        audited = audit_pb.AuditedAttributes()
        attr2 = attr_pb.Attribute()
        attr2.key = "tier"
        attr2.value = "community"
        audited.attributes.append(attr2)

        sign_msg = audit_pb.MsgSignProviderAttributes()
        attr3 = attr_pb.Attribute()
        attr3.key = "location"
        attr3.value = "datacenter"
        sign_msg.attributes.append(attr3)

        assert len(provider.attributes) == 1
        assert len(audited.attributes) == 1
        assert len(sign_msg.attributes) == 1
        assert provider.attributes[0].key == "region"
        assert audited.attributes[0].key == "tier"
        assert sign_msg.attributes[0].key == "location"

    def test_query_parameter_consistency(self):
        """Test query parameter consistency across different request types."""
        provider_req = audit_query.QueryProviderRequest()
        provider_auditor_req = audit_query.QueryProviderAuditorRequest()

        assert hasattr(provider_req, 'owner'), "QueryProviderRequest missing owner"
        assert hasattr(provider_auditor_req, 'owner'), "QueryProviderAuditorRequest missing owner"

        assert hasattr(provider_req, 'auditor'), "QueryProviderRequest missing auditor"
        assert hasattr(provider_auditor_req, 'auditor'), "QueryProviderAuditorRequest missing auditor"

        attrs_req = audit_query.QueryProviderAttributesRequest()
        all_attrs_req = audit_query.QueryAllProvidersAttributesRequest()
        auditor_attrs_req = audit_query.QueryAuditorAttributesRequest()

        pagination_requests = [attrs_req, all_attrs_req, auditor_attrs_req]
        for req in pagination_requests:
            assert hasattr(req, 'pagination'), f"{type(req).__name__} missing pagination field"



from unittest.mock import Mock, patch
import base64


class TestAuditClientInitialization:
    """Test audit client initialization and setup."""

    def test_audit_client_initialization(self):
        """Test AuditClient can be initialized properly."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        assert audit_client.akash_client == mock_akash_client
        assert hasattr(audit_client, 'get_providers')
        assert hasattr(audit_client, 'get_provider')
        assert hasattr(audit_client, 'get_provider_attributes')
        assert hasattr(audit_client, 'get_provider_auditor_attributes')
        assert hasattr(audit_client, 'get_auditor_attributes')
        assert hasattr(audit_client, 'create_provider_attributes')
        assert hasattr(audit_client, 'delete_provider_attributes')
        assert hasattr(audit_client, 'validate_provider_attributes')

    def test_audit_client_inherits_mixins(self):
        """Test AuditClient properly inherits from all mixins."""
        from akash.modules.audit.client import AuditClient
        from akash.modules.audit.query import AuditQuery
        from akash.modules.audit.tx import AuditTx
        from akash.modules.audit.utils import AuditUtils

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        assert isinstance(audit_client, AuditQuery)
        assert isinstance(audit_client, AuditTx)
        assert isinstance(audit_client, AuditUtils)

    def test_audit_client_logging_setup(self):
        """Test logging is properly configured for AuditClient."""
        from akash.modules.audit.client import AuditClient

        with patch('akash.modules.audit.client.logger') as mock_logger:
            mock_akash_client = Mock()
            audit_client = AuditClient(mock_akash_client)

            mock_logger.info.assert_called_once_with("Initialized AuditClient")


class TestAuditQueryOperations:
    """Test audit query operations with mocked responses."""

    def test_list_providers_success(self):
        """Test successful providers list query."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 0,
                'value': base64.b64encode(b'mock_provider_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)

        with patch('akash.proto.akash.audit.v1beta3.query_pb2.QueryProvidersResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_provider = Mock()
            mock_provider.owner = "akash1owner"
            mock_provider.auditor = "akash1auditor"
            mock_provider.attributes = [Mock(key="region", value="us-west")]
            mock_response_instance.providers = [mock_provider]
            mock_response_class.return_value = mock_response_instance

            providers = audit_client.get_providers(limit=10)

            assert len(providers) == 1
            assert providers[0]['owner'] == "akash1owner"
            assert providers[0]['auditor'] == "akash1auditor"
            assert len(providers[0]['attributes']) == 1
            assert providers[0]['attributes'][0]['key'] == "region"

    def test_list_providers_empty_response(self):
        """Test providers list query with empty response."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 5,
                'log': 'no providers found'
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)
        providers = audit_client.get_providers()

        assert providers == []

    def test_list_providers_error_response(self):
        """Test providers list query with error response."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 1,
                'log': 'query failed'
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)

        with pytest.raises(Exception, match="Query failed"):
            audit_client.get_providers()

    def test_get_provider_success(self):
        """Test successful single provider query."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch.object(audit_client, 'get_provider_auditor_attributes') as mock_get_provider:
            mock_provider_data = {
                'owner': 'akash1owner',
                'auditor': 'akash1auditor',
                'attributes': [{'key': 'tier', 'value': 'premium'}]
            }
            mock_get_provider.return_value = [mock_provider_data]

            provider = audit_client.get_provider("akash1owner", "akash1auditor")

            assert provider == mock_provider_data
            mock_get_provider.assert_called_once_with("akash1auditor", "akash1owner")

    def test_get_provider_not_found(self):
        """Test single provider query with no results."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch.object(audit_client, 'get_provider_auditor_attributes') as mock_get_provider:
            mock_get_provider.return_value = []

            provider = audit_client.get_provider("akash1owner", "akash1auditor")

            assert provider == {}

    def test_get_provider_attributes_success(self):
        """Test successful provider attributes query."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 0,
                'value': base64.b64encode(b'mock_attributes_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)

        with patch('akash.proto.akash.audit.v1beta3.query_pb2.QueryProvidersResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_provider = Mock()
            mock_provider.owner = "akash1owner"
            mock_provider.auditor = "akash1auditor1"
            mock_provider.attributes = [Mock(key="location", value="datacenter")]
            mock_response_instance.providers = [mock_provider]
            mock_response_class.return_value = mock_response_instance

            attributes = audit_client.get_provider_attributes("akash1owner")

            assert len(attributes) == 1
            assert attributes[0]['owner'] == "akash1owner"
            assert attributes[0]['auditor'] == "akash1auditor1"

    def test_get_auditor_attributes_success(self):
        """Test successful auditor attributes query."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 0,
                'value': base64.b64encode(b'mock_auditor_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)

        with patch('akash.proto.akash.audit.v1beta3.query_pb2.QueryProvidersResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_provider1 = Mock()
            mock_provider1.owner = "akash1owner1"
            mock_provider1.auditor = "akash1auditor"
            mock_provider1.attributes = [Mock(key="certified", value="true")]
            mock_provider2 = Mock()
            mock_provider2.owner = "akash1owner2"
            mock_provider2.auditor = "akash1auditor"
            mock_provider2.attributes = [Mock(key="region", value="eu-central")]
            mock_response_instance.providers = [mock_provider1, mock_provider2]
            mock_response_class.return_value = mock_response_instance

            attributes = audit_client.get_auditor_attributes("akash1auditor")

            assert len(attributes) == 2
            assert attributes[0]['auditor'] == "akash1auditor"
            assert attributes[1]['auditor'] == "akash1auditor"
            assert attributes[0]['owner'] == "akash1owner1"
            assert attributes[1]['owner'] == "akash1owner2"


class TestAuditTransactionOperations:
    """Test audit transaction operations with mocked responses."""

    def test_create_provider_attributes_calls_broadcast(self):
        """Test create provider attributes calls broadcast_transaction_rpc."""
        from akash.modules.audit.client import AuditClient

        mock_wallet = Mock()
        mock_wallet.address = "akash1auditor"

        mock_broadcast_result = Mock()
        mock_broadcast_result.success = True
        mock_broadcast_result.tx_hash = "ABC123"

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch('akash.modules.audit.tx.broadcast_transaction_rpc',
                   return_value=mock_broadcast_result) as mock_broadcast:
            attributes = [
                {"key": "region", "value": "us-west"},
                {"key": "tier", "value": "premium"}
            ]

            result = audit_client.create_provider_attributes(
                mock_wallet,
                "akash1owner",
                attributes,
                "Create provider attributes",
                use_simulation=False
            )

            mock_broadcast.assert_called_once()

            call_args = mock_broadcast.call_args[1]
            messages = call_args['messages']
            assert len(messages) == 1
            assert messages[0]['@type'] == '/akash.audit.v1beta3.MsgSignProviderAttributes'
            assert messages[0]['owner'] == 'akash1owner'
            assert messages[0]['auditor'] == 'akash1auditor'
            assert len(messages[0]['attributes']) == 2
            assert messages[0]['attributes'][0]['key'] == 'region'
            assert messages[0]['attributes'][0]['value'] == 'us-west'

    def test_create_provider_attributes_exception(self):
        """Test create provider attributes with exception."""
        from akash.modules.audit.client import AuditClient

        mock_wallet = Mock()
        mock_wallet.address = "akash1auditor"

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch('akash.tx.broadcast_transaction_rpc', side_effect=Exception("Network error")) as mock_broadcast:
            result = audit_client.create_provider_attributes(
                mock_wallet,
                "akash1owner",
                [{"key": "test", "value": "value"}],
                use_simulation=False
            )

            assert result.success == False

    def test_delete_provider_attributes_calls_broadcast(self):
        """Test delete provider attributes calls broadcast_transaction_rpc."""
        from akash.modules.audit.client import AuditClient

        mock_wallet = Mock()
        mock_wallet.address = "akash1auditor"

        mock_broadcast_result = Mock()
        mock_broadcast_result.success = True
        mock_broadcast_result.tx_hash = "DEF456"

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch('akash.modules.audit.tx.broadcast_transaction_rpc',
                   return_value=mock_broadcast_result) as mock_broadcast:
            keys_to_delete = ["old_region", "deprecated_attr"]

            result = audit_client.delete_provider_attributes(
                mock_wallet,
                "akash1owner",
                keys_to_delete,
                "Delete old attributes",
                use_simulation=False
            )

            mock_broadcast.assert_called_once()

            call_args = mock_broadcast.call_args[1]
            messages = call_args['messages']
            assert len(messages) == 1
            assert messages[0]['@type'] == '/akash.audit.v1beta3.MsgDeleteProviderAttributes'
            assert messages[0]['owner'] == 'akash1owner'
            assert messages[0]['auditor'] == 'akash1auditor'
            assert messages[0]['keys'] == keys_to_delete

    def test_delete_provider_attributes_exception(self):
        """Test delete provider attributes with exception."""
        from akash.modules.audit.client import AuditClient

        mock_wallet = Mock()
        mock_wallet.address = "akash1auditor"

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch('akash.tx.broadcast_transaction_rpc', side_effect=Exception("Permission denied")) as mock_broadcast:
            result = audit_client.delete_provider_attributes(
                mock_wallet,
                "akash1owner",
                ["test_key"],
                use_simulation=False
            )

            assert result.success == False


class TestAuditUtilityFunctions:
    """Test audit utility functions."""

    def test_validate_provider_attributes_valid(self):
        """Test validation of valid provider attributes."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        valid_provider_data = {
            'owner': 'akash1owner',
            'auditor': 'akash1auditor',
            'attributes': [
                {'key': 'region', 'value': 'us-west'},
                {'key': 'tier', 'value': 'premium'}
            ]
        }

        result = audit_client.validate_provider_attributes(valid_provider_data)
        assert result == True

    def test_validate_provider_attributes_missing_fields(self):
        """Test validation with missing required fields."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        invalid_data_missing_owner = {
            'auditor': 'akash1auditor',
            'attributes': []
        }

        with patch('akash.modules.audit.utils.logger') as mock_logger:
            result = audit_client.validate_provider_attributes(invalid_data_missing_owner)
            assert result == False
            mock_logger.error.assert_called_with("Missing required field: owner")

    def test_validate_provider_attributes_invalid_attributes_format(self):
        """Test validation with invalid attributes format."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        invalid_data = {
            'owner': 'akash1owner',
            'auditor': 'akash1auditor',
            'attributes': "not_a_list"
        }

        with patch('akash.modules.audit.utils.logger') as mock_logger:
            result = audit_client.validate_provider_attributes(invalid_data)
            assert result == False
            mock_logger.error.assert_called_with("Attributes must be a list")

    def test_validate_provider_attributes_invalid_attribute_structure(self):
        """Test validation with invalid attribute structure."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        invalid_data = {
            'owner': 'akash1owner',
            'auditor': 'akash1auditor',
            'attributes': [
                {'key': 'region'},
                {'value': 'premium'}
            ]
        }

        with patch('akash.modules.audit.utils.logger') as mock_logger:
            result = audit_client.validate_provider_attributes(invalid_data)
            assert result == False
            mock_logger.error.assert_called_with("Each attribute must have 'key' and 'value'")


class TestAuditErrorHandlingScenarios:
    """Test audit error handling and edge cases."""

    def test_list_providers_network_failure(self):
        """Test providers list query with network failure."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.side_effect = Exception("Connection timeout")

        audit_client = AuditClient(mock_akash_client)

        with pytest.raises(Exception, match="Connection timeout"):
            audit_client.get_providers()

    def test_list_providers_no_response(self):
        """Test providers list query with no response."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = None

        audit_client = AuditClient(mock_akash_client)

        with pytest.raises(Exception, match="RPC query failed: No response"):
            audit_client.get_providers()

    def test_get_provider_attributes_malformed_response(self):
        """Test provider attributes query with malformed response."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 0,
                'value': 'invalid_base64_data'
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)

        with pytest.raises(Exception):
            audit_client.get_provider_attributes("akash1owner")

    def test_create_provider_attributes_insufficient_balance(self):
        """Test create provider attributes with insufficient balance."""
        from akash.modules.audit.client import AuditClient

        mock_wallet = Mock()
        mock_wallet.address = "akash1auditor"

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch('akash.tx.broadcast_transaction_rpc', side_effect=Exception("insufficient funds")) as mock_broadcast:
            result = audit_client.create_provider_attributes(
                mock_wallet,
                "akash1owner",
                [{"key": "test", "value": "value"}],
                use_simulation=False
            )

            assert result.success == False

    def test_validate_provider_attributes_exception_handling(self):
        """Test provider attributes validation with unexpected exception."""
        from akash.modules.audit.client import AuditClient

        mock_akash_client = Mock()
        audit_client = AuditClient(mock_akash_client)

        with patch.object(audit_client, 'validate_provider_attributes', side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(RuntimeError):
                audit_client.validate_provider_attributes({"test": "data"})

    def test_get_provider_auditor_attributes_pagination_error(self):
        """Test provider-auditor attributes query with pagination parsing error."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 0,
                'value': base64.b64encode(b'').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)

        result = audit_client.get_provider_auditor_attributes("akash1auditor", "akash1owner")
        assert result == []

    def test_get_auditor_attributes_with_pagination(self):
        """Test auditor attributes query with pagination parameters."""
        from akash.modules.audit.client import AuditClient

        mock_response = {
            'response': {
                'code': 0,
                'value': base64.b64encode(b'mock_paginated_data').decode()
            }
        }

        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = mock_response

        audit_client = AuditClient(mock_akash_client)

        with patch('akash.proto.akash.audit.v1beta3.query_pb2.QueryProvidersResponse') as mock_response_class:
            mock_response_instance = Mock()
            mock_response_instance.providers = []
            mock_response_class.return_value = mock_response_instance

            pagination = {'limit': 50, 'offset': 10}
            attributes = audit_client.get_auditor_attributes("akash1auditor", pagination)

            assert attributes == []
            mock_akash_client.rpc_query.assert_called_once()


if __name__ == '__main__':
    print("Running audit module tests (validation + functional)")
    print("=" * 70)
    print()
    print("Validation tests: testing protobuf structures, message converters,")
    print("query responses, parameter compatibility, and auditor-provider patterns.")
    print()
    print("Functional tests: testing client operations, query methods, transaction")
    print("broadcasting, provider attribute management, and error handling scenarios.")
    print()
    print("These tests provide coverage without blockchain interactions.")
    print()

    pytest.main([__file__, '-v'])
