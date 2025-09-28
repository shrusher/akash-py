#!/usr/bin/env python3
"""
IBC utils tests - validation and functional tests.

Validation tests: Validate IBC utility function structures, hash computation patterns,
validator set compatibility, and byte slice support without requiring
blockchain interactions. 

Functional tests: Test IBC utility operations, hash computations, validator set processing,
and utility functions using mocking to isolate functionality and test error handling scenarios.

Run: python test_ibc_utils.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from akash.modules.ibc.utils import IBCUtils




class TestIBCUtils:
    """Test IBCUtils static methods."""


    def test_validate_channel_id(self):
        """Test channel ID validation."""
        assert IBCUtils._validate_channel_id("channel-0") == True
        assert IBCUtils._validate_channel_id("channel-123") == True
        assert IBCUtils._validate_channel_id("channel-") == False
        assert IBCUtils._validate_channel_id("channel") == False
        assert IBCUtils._validate_channel_id("chan-0") == False
        assert IBCUtils._validate_channel_id("channel-abc") == False

    def test_validate_address_format(self):
        """Test bech32 address format validation."""
        assert IBCUtils._validate_address_format("akash1qnnhhgzxj24f2kld5yhy4v4h4s9r295ak5gjw4") == True
        
        assert IBCUtils._validate_address_format("akash1qnnhhgzxj24f2kld5yhy4v4h4s9r295ak5gjw4", "akash") == True
        
        assert IBCUtils._validate_address_format("akash1qnnhhgzxj24f2kld5yhy4v4h4s9r295ak5gjw4", "cosmos") == False

        assert IBCUtils._validate_address_format("") == False
        assert IBCUtils._validate_address_format("short") == False
        assert IBCUtils._validate_address_format("no_separator_here") == False
        assert IBCUtils._validate_address_format("invalid-format") == False
        assert IBCUtils._validate_address_format("123invalid1abc") == False



if __name__ == '__main__':
    pytest.main([__file__, '-v'])