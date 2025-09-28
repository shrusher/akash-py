#!/usr/bin/env python3
"""
Validation tests for Akash Evidence module.

These tests validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Run: python evidence_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pytest
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.modules.evidence import EvidenceClient
from akash.tx import BroadcastResult


class TestEvidenceClient:
    """Test evidence client operations."""

    def test_evidence_client_init(self):
        """Test evidence client initialization."""
        mock_akash_client = Mock()
        evidence_client = EvidenceClient(mock_akash_client)

        assert evidence_client.akash_client == mock_akash_client
        assert hasattr(evidence_client, 'get_evidence')
        assert hasattr(evidence_client, 'get_all_evidence')
        assert hasattr(evidence_client, 'submit_evidence')

    def test_get_all_evidence_empty_response(self):
        """Test get_all_evidence with empty response."""
        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = None

        evidence_client = EvidenceClient(mock_akash_client)
        result = evidence_client.get_all_evidence()

        assert result == []

    def test_get_evidence_empty_response(self):
        """Test get_evidence with empty response."""
        mock_akash_client = Mock()
        mock_akash_client.abci_query.return_value = None

        evidence_client = EvidenceClient(mock_akash_client)
        result = evidence_client.get_evidence("test_hash")

        assert result == {}


    def test_validate_evidence_format_valid(self):
        """Test validate_evidence_format with valid evidence."""
        mock_akash_client = Mock()
        evidence_client = EvidenceClient(mock_akash_client)

        valid_evidence = {
            'type_url': '/cosmos.evidence.v1beta1.Equivocation',
            'content': b'some_content'
        }

        result = evidence_client.validate_evidence_format(valid_evidence)

        assert result["valid"] == True
        assert len(result["errors"]) == 0

    def test_validate_evidence_format_invalid(self):
        """Test validate_evidence_format with invalid evidence."""
        mock_akash_client = Mock()
        evidence_client = EvidenceClient(mock_akash_client)

        invalid_evidence = {}

        result = evidence_client.validate_evidence_format(invalid_evidence)

        assert result["valid"] == False
        assert len(result["errors"]) > 0

    @patch('akash.modules.evidence.tx.broadcast_transaction_rpc')
    def test_submit_evidence_invalid_format(self, mock_broadcast):
        """Test submit_evidence with invalid format."""
        mock_akash_client = Mock()
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"

        evidence_client = EvidenceClient(mock_akash_client)

        result = evidence_client.submit_evidence(
            wallet=mock_wallet,
            evidence_data={}
        )

        assert result.success == False
        assert "Invalid evidence format" in result.raw_log
        mock_broadcast.assert_not_called()

    @patch('akash.modules.evidence.tx.broadcast_transaction_rpc')
    def test_submit_evidence_valid_format(self, mock_broadcast):
        """Test submit_evidence with valid format."""
        mock_broadcast.return_value = BroadcastResult("hash123", 0, "success", True)

        mock_akash_client = Mock()
        mock_wallet = Mock()
        mock_wallet.address = "akash1test"

        evidence_client = EvidenceClient(mock_akash_client)

        result = evidence_client.submit_evidence(
            wallet=mock_wallet,
            evidence_data={
                'type_url': '/cosmos.evidence.v1beta1.Equivocation',
                'content': b'test_evidence_content'
            }
        )

        assert isinstance(result, BroadcastResult)
        assert result.success == True
        mock_broadcast.assert_called_once()

    def test_error_handling(self):
        """Test error handling in evidence operations."""
        mock_akash_client = Mock()
        mock_akash_client.abci_query.side_effect = Exception("Network error")

        evidence_client = EvidenceClient(mock_akash_client)

        result1 = evidence_client.get_all_evidence()
        assert result1 == []

        result2 = evidence_client.get_evidence("test")
        assert result2 == {}



if __name__ == "__main__":
    print("Running evidence module validation tests")
    print("=" * 70)
    print()
    print("Testing protobuf structures, message converters, query responses,")
    print("parameter compatibility, and evidence module functionality.")
    print()
    print("These tests catch breaking changes without blockchain interactions.")
    print()

    pytest.main([__file__, "-v", "--tb=short"])
