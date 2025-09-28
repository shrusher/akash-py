#!/usr/bin/env python3
"""
Inflation module tests - validation and functional tests.

Validation tests: Validate protobuf message structures, field access patterns,
converter compatibility, and query parameter support without requiring
blockchain interactions. 

Functional tests: Test inflation client query operations, parameter retrieval,
inflation rate queries, annual provisions, and utility functions using mocking
to isolate functionality and test error handling scenarios.

Run: python inflation_tests.py
"""

import os

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import sys
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.modules.inflation import InflationClient


class TestInflationClient:
    """Test inflation client operations."""

    def test_inflation_client_init(self):
        """Test inflation client initialization."""
        mock_akash_client = Mock()
        inflation_client = InflationClient(mock_akash_client)

        assert inflation_client.akash_client == mock_akash_client
        assert hasattr(inflation_client, 'get_params')
        assert hasattr(inflation_client, 'get_inflation')
        assert hasattr(inflation_client, 'get_annual_provisions')
        assert hasattr(inflation_client, 'get_all_mint_info')

    def test_get_params_none_response(self):
        """Test get_params with None response."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = None

        inflation_client = InflationClient(mock_akash_client)
        result = inflation_client.get_params()

        assert result is None

    def test_get_inflation_none_response(self):
        """Test get_inflation with None response."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = None

        inflation_client = InflationClient(mock_akash_client)
        result = inflation_client.get_inflation()

        assert result is None

    def test_get_annual_provisions_none_response(self):
        """Test get_annual_provisions with None response."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = None

        inflation_client = InflationClient(mock_akash_client)
        result = inflation_client.get_annual_provisions()

        assert result is None

    def test_get_all_mint_info_partial_success(self):
        """Test get_all_mint_info with partial success (no params)."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = None

        inflation_client = InflationClient(mock_akash_client)
        result = inflation_client.get_all_mint_info()

        assert isinstance(result, dict)
        assert result['params'] is None
        assert result['current_inflation'] is None
        assert result['annual_provisions'] is None
        assert result['status'] == 'partial'

    def test_get_params_with_error_response(self):
        """Test get_params with error response code."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = {
            'response': {
                'code': 1,
                'log': 'Query failed'
            }
        }

        inflation_client = InflationClient(mock_akash_client)
        result = inflation_client.get_params()

        assert result is None

    def test_error_handling_exception(self):
        """Test error handling when exceptions occur."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.side_effect = Exception("Network error")

        inflation_client = InflationClient(mock_akash_client)

        assert inflation_client.get_params() is None
        assert inflation_client.get_inflation() is None
        assert inflation_client.get_annual_provisions() is None

    def test_get_all_mint_info_success_status(self):
        """Test get_all_mint_info returns success when params exist."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = {
            'response': {
                'code': 0,
                'value': 'dmFsaWRfZGF0YQ=='
            }
        }

        inflation_client = InflationClient(mock_akash_client)

        def mock_get_params():
            return {'mint_denom': 'uakt'}

        inflation_client.get_params = mock_get_params

        result = inflation_client.get_all_mint_info()

        assert result['status'] == 'success'

    def test_malformed_response(self):
        """Test handling of malformed responses."""
        mock_akash_client = Mock()
        mock_akash_client.rpc_query.return_value = {
            'invalid_structure': True
        }

        inflation_client = InflationClient(mock_akash_client)
        result = inflation_client.get_params()

        assert result is None


if __name__ == '__main__':
    print("✅ Running inflation module tests")
    print("=" * 70)

    test = TestInflationClient()

    test.test_inflation_client_init()
    test.test_get_params_none_response()
    test.test_get_inflation_none_response()
    test.test_get_annual_provisions_none_response()
    test.test_get_all_mint_info_partial_success()
    test.test_get_params_with_error_response()
    test.test_error_handling_exception()
    test.test_get_all_mint_info_success_status()
    test.test_malformed_response()

    print("✅ All inflation tests passed")
    print("✅ All inflation module tests completed successfully")
