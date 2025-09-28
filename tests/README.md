# Test suite

This directory contains unit tests for the Akash Python SDK.

## Test structure

- `unit/` - Unit tests for individual modules and components
- `run_all_tests.py` - Test runner for executing the complete test suite

## Running tests

Execute all unit tests:
```bash
python3 tests/unit/run_all_tests.py
```

Execute individual test modules:
```bash
python3 tests/unit/<test_module>.py
```

## Prerequisites

Ensure all required dependencies are installed before running tests:
```bash
pip install -r requirements.txt
```