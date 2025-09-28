import base64
import logging
from typing import Dict, List, Optional, Any

from akash.proto.cosmos.staking.v1beta1 import query_pb2 as staking_query_pb2

logger = logging.getLogger(__name__)


class StakingQuery:
    """
    Mixin for staking query operations.
    """

    def get_validators(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        count_total: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get validators list with optional status filtering.

        Args:
            status: Optional validator status filter. Valid values:
                   - "BOND_STATUS_UNSPECIFIED" (or 0)
                   - "BOND_STATUS_UNBONDED" (or 1)
                   - "BOND_STATUS_UNBONDING" (or 2)
                   - "BOND_STATUS_BONDED" (or 3)
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            List[Dict[str, Any]]: List of validators (optionally filtered by status)
        """
        try:
            request = staking_query_pb2.QueryValidatorsRequest()

            if limit is not None or offset is not None or count_total:
                try:
                    from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import (
                        PageRequest,
                    )

                    pagination = PageRequest()
                    if limit is not None:
                        pagination.limit = limit
                    if offset is not None:
                        pagination.offset = offset
                    if count_total:
                        pagination.count_total = count_total
                    request.pagination.CopyFrom(pagination)
                except ImportError:
                    pass

            if status is not None:
                if isinstance(status, str):
                    if status in [
                        "BOND_STATUS_UNSPECIFIED",
                        "BOND_STATUS_UNBONDED",
                        "BOND_STATUS_UNBONDING",
                        "BOND_STATUS_BONDED",
                    ]:
                        request.status = status
                    elif status in ["0", "1", "2", "3"]:
                        numeric_to_string = {
                            "0": "BOND_STATUS_UNSPECIFIED",
                            "1": "BOND_STATUS_UNBONDED",
                            "2": "BOND_STATUS_UNBONDING",
                            "3": "BOND_STATUS_BONDED",
                        }
                        request.status = numeric_to_string[status]
                    else:
                        valid_values = [
                            "BOND_STATUS_UNSPECIFIED",
                            "BOND_STATUS_UNBONDED",
                            "BOND_STATUS_UNBONDING",
                            "BOND_STATUS_BONDED",
                            "0",
                            "1",
                            "2",
                            "3",
                        ]
                        raise ValueError(
                            f"Invalid status value: {status}. Valid values: {valid_values}"
                        )
                else:
                    int_to_string = {
                        0: "BOND_STATUS_UNSPECIFIED",
                        1: "BOND_STATUS_UNBONDED",
                        2: "BOND_STATUS_UNBONDING",
                        3: "BOND_STATUS_BONDED",
                    }
                    int_status = int(status)
                    if int_status in int_to_string:
                        request.status = int_to_string[int_status]
                    else:
                        raise ValueError(
                            f"Invalid status value: {status}. Valid values: 0, 1, 2, 3"
                        )

            data = request.SerializeToString().hex()

            query_path = "/cosmos.staking.v1beta1.Query/Validators"
            result = self.akash_client.rpc_query(
                "abci_query", [query_path, data, "0", False]
            )

            if not result or "response" not in result:
                error_msg = f"Query failed: No response from {query_path}"
                logger.error(error_msg)
                raise Exception(error_msg)

            response = result["response"]
            response_code = response.get("code", -1)

            if response_code != 0:
                error_msg = f"Query failed: {query_path} returned code {response_code}: {response.get('log', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            if "value" not in response or not response["value"]:
                logger.info("Query succeeded but no validators found")
                return []

            response_data = base64.b64decode(response["value"])
            validators_response = staking_query_pb2.QueryValidatorsResponse()
            validators_response.ParseFromString(response_data)

            validators = []
            for validator in validators_response.validators:
                validators.append(
                    {
                        "operator_address": validator.operator_address,
                        "consensus_pubkey": str(validator.consensus_pubkey),
                        "jailed": validator.jailed,
                        "status": validator.status,
                        "tokens": validator.tokens,
                        "delegator_shares": validator.delegator_shares,
                        "description": {
                            "moniker": validator.description.moniker,
                            "identity": validator.description.identity,
                            "website": validator.description.website,
                            "details": validator.description.details,
                        },
                        "commission_rate": validator.commission.commission_rates.rate,
                        "min_self_delegation": validator.min_self_delegation,
                    }
                )

            return validators

        except Exception as e:
            logger.error(f"Failed to get validators: {e}")
            raise

    def get_validator(self, validator_address: str) -> Optional[Dict[str, Any]]:
        """
        Get single validator by address.

        Args:
            validator_address: Validator operator address

        Returns:
            Validator information or None
        """
        try:
            validators = self.get_validators()
            for validator in validators:
                if validator.get("operator_address") == validator_address:
                    return validator
            return None
        except Exception as e:
            logger.warning(f"Failed to get validator {validator_address}: {e}")
            return None

    def get_delegations(
        self,
        delegator_address: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        count_total: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get delegations for an address.

        Args:
            delegator_address: Delegator address
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            List of delegation information
        """
        try:
            request = staking_query_pb2.QueryDelegatorDelegationsRequest()
            request.delegator_addr = delegator_address

            if limit is not None or offset is not None or count_total:
                try:
                    from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import (
                        PageRequest,
                    )

                    pagination = PageRequest()
                    if limit is not None:
                        pagination.limit = limit
                    if offset is not None:
                        pagination.offset = offset
                    if count_total:
                        pagination.count_total = count_total
                    request.pagination.CopyFrom(pagination)
                except ImportError:
                    pass
            data = request.SerializeToString().hex()

            query_path = "/cosmos.staking.v1beta1.Query/DelegatorDelegations"
            result = self.akash_client.rpc_query(
                "abci_query", [query_path, data, "0", False]
            )

            if not result or "response" not in result:
                error_msg = f"Query failed: No response from {query_path}"
                logger.error(error_msg)
                raise Exception(error_msg)

            response = result["response"]
            response_code = response.get("code", -1)

            if response_code != 0:
                error_msg = f"Query failed: {query_path} returned code {response_code}: {response.get('log', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            if "value" not in response or not response["value"]:
                logger.info(
                    f"Query succeeded but no delegations found for {delegator_address}"
                )
                return []

            response_data = base64.b64decode(response["value"])
            delegations_response = staking_query_pb2.QueryDelegatorDelegationsResponse()
            delegations_response.ParseFromString(response_data)

            delegations = []
            for delegation_response in delegations_response.delegation_responses:
                delegations.append(
                    {
                        "delegation": {
                            "delegator_address": delegation_response.delegation.delegator_address,
                            "validator_address": delegation_response.delegation.validator_address,
                            "shares": delegation_response.delegation.shares,
                        },
                        "balance": {
                            "denom": delegation_response.balance.denom,
                            "amount": delegation_response.balance.amount,
                        },
                    }
                )

            return delegations

        except Exception as e:
            logger.error(f"Failed to get delegations: {e}")
            raise

    def get_delegation(
        self, delegator_address: str, validator_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific delegation between delegator and validator.

        Args:
            delegator_address: Delegator address
            validator_address: Validator operator address

        Returns:
            Delegation information or None
        """
        try:
            request = staking_query_pb2.QueryDelegationRequest()
            request.delegator_addr = delegator_address
            request.validator_addr = validator_address
            path = "/cosmos.staking.v1beta1.Query/Delegation"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = staking_query_pb2.QueryDelegationResponse()
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    if response_obj.delegation_response:
                        delegation = response_obj.delegation_response
                        return {
                            "delegation": {
                                "delegator_address": delegation.delegation.delegator_address,
                                "validator_address": delegation.delegation.validator_address,
                                "shares": delegation.delegation.shares,
                            },
                            "balance": {
                                "denom": delegation.balance.denom,
                                "amount": delegation.balance.amount,
                            },
                        }

            return None

        except Exception as e:
            logger.warning(f"Failed to get delegation: {e}")
            return None

    def get_staking_params(self) -> Dict[str, Any]:
        """
        Get staking module parameters.

        Returns:
            Staking parameters
        """
        try:
            request = staking_query_pb2.QueryParamsRequest()
            data = request.SerializeToString().hex()

            query_path = "/cosmos.staking.v1beta1.Query/Params"
            result = self.akash_client.rpc_query(
                "abci_query", [query_path, data, "0", False]
            )

            if not result or "response" not in result:
                error_msg = f"Query failed: No response from {query_path}"
                logger.error(error_msg)
                raise Exception(error_msg)

            response = result["response"]
            response_code = response.get("code", -1)

            if response_code != 0:
                error_msg = f"Query failed: {query_path} returned code {response_code}: {response.get('log', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            if "value" not in response or not response["value"]:
                logger.info("Query succeeded but no staking params found")
                return {}

            response_data = base64.b64decode(response["value"])
            params_response = staking_query_pb2.QueryParamsResponse()
            params_response.ParseFromString(response_data)

            return {
                "unbonding_time": str(params_response.params.unbonding_time),
                "max_validators": params_response.params.max_validators,
                "max_entries": params_response.params.max_entries,
                "historical_entries": params_response.params.historical_entries,
                "bond_denom": params_response.params.bond_denom,
            }

        except Exception as e:
            logger.error(f"Failed to get staking params: {e}")
            raise

    def get_unbonding_delegations(
        self,
        delegator_address: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        count_total: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get unbonding delegations for an address.

        Args:
            delegator_address: Delegator address
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            List of unbonding delegation information
        """
        try:
            request = staking_query_pb2.QueryDelegatorUnbondingDelegationsRequest()
            request.delegator_addr = delegator_address

            if limit is not None or offset is not None or count_total:
                try:
                    from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import (
                        PageRequest,
                    )

                    pagination = PageRequest()
                    if limit is not None:
                        pagination.limit = limit
                    if offset is not None:
                        pagination.offset = offset
                    if count_total:
                        pagination.count_total = count_total
                    request.pagination.CopyFrom(pagination)
                except ImportError:
                    pass

            path = "/cosmos.staking.v1beta1.Query/DelegatorUnbondingDelegations"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            unbonding_delegations = []
            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = (
                        staking_query_pb2.QueryDelegatorUnbondingDelegationsResponse()
                    )
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    for unbonding_delegation in response_obj.unbonding_responses:
                        unbonding_entry = {
                            "delegator_address": unbonding_delegation.delegator_address,
                            "validator_address": unbonding_delegation.validator_address,
                            "entries": [],
                        }

                        for entry in unbonding_delegation.entries:
                            unbonding_entry["entries"].append(
                                {
                                    "creation_height": str(entry.creation_height),
                                    "completion_time": (
                                        entry.completion_time.ToDatetime().isoformat()
                                        if entry.completion_time
                                        else ""
                                    ),
                                    "initial_balance": entry.initial_balance,
                                    "balance": entry.balance,
                                }
                            )

                        unbonding_delegations.append(unbonding_entry)

                    logger.info(
                        f"Retrieved {len(unbonding_delegations)} unbonding delegations"
                    )

            return unbonding_delegations

        except Exception as e:
            logger.error(
                f"Failed to get unbonding delegations for {delegator_address}: {e}"
            )
            raise

    def get_redelegations(
        self,
        delegator_address: str,
        src_validator_address: str = "",
        dst_validator_address: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Get redelegations for an address.

        Args:
            delegator_address: Delegator address
            src_validator_address: Source validator address (optional)
            dst_validator_address: Destination validator address (optional)

        Returns:
            List of redelegation information
        """
        try:
            request = staking_query_pb2.QueryRedelegationsRequest()
            request.delegator_addr = delegator_address
            if src_validator_address:
                request.src_validator_addr = src_validator_address
            if dst_validator_address:
                request.dst_validator_addr = dst_validator_address
            path = "/cosmos.staking.v1beta1.Query/Redelegations"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            redelegations = []
            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = staking_query_pb2.QueryRedelegationsResponse()
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    for redelegation_response in response_obj.redelegation_responses:
                        redelegation = redelegation_response.redelegation
                        redelegation_entry = {
                            "delegator_address": redelegation.delegator_address,
                            "validator_src_address": redelegation.validator_src_address,
                            "validator_dst_address": redelegation.validator_dst_address,
                            "entries": [],
                        }

                        for entry in redelegation_response.entries:
                            redelegation_entry["entries"].append(
                                {
                                    "creation_height": str(
                                        entry.redelegation_entry.creation_height
                                    ),
                                    "completion_time": (
                                        entry.redelegation_entry.completion_time.ToDatetime().isoformat()
                                        if entry.redelegation_entry.completion_time
                                        else ""
                                    ),
                                    "initial_balance": entry.redelegation_entry.initial_balance,
                                    "shares_dst": entry.redelegation_entry.shares_dst,
                                    "balance": entry.balance,
                                }
                            )

                        redelegations.append(redelegation_entry)

                    logger.info(f"Retrieved {len(redelegations)} redelegations")

            return redelegations

        except Exception as e:
            logger.error(f"Failed to get redelegations for {delegator_address}: {e}")
            raise

    def get_delegations_to_validator(
        self, validator_address: str
    ) -> List[Dict[str, Any]]:
        """
        Get all delegations made to one validator.

        Args:
            validator_address: Validator operator address

        Returns:
            List of delegation information to this validator
        """
        try:
            request = staking_query_pb2.QueryValidatorDelegationsRequest()
            request.validator_addr = validator_address
            path = "/cosmos.staking.v1beta1.Query/ValidatorDelegations"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            delegations = []
            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = staking_query_pb2.QueryValidatorDelegationsResponse()
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    for delegation_response in response_obj.delegation_responses:
                        delegations.append(
                            {
                                "delegation": {
                                    "delegator_address": delegation_response.delegation.delegator_address,
                                    "validator_address": delegation_response.delegation.validator_address,
                                    "shares": delegation_response.delegation.shares,
                                },
                                "balance": {
                                    "denom": delegation_response.balance.denom,
                                    "amount": delegation_response.balance.amount,
                                },
                            }
                        )

                    logger.info(
                        f"Retrieved {len(delegations)} delegations to validator {validator_address}"
                    )

            return delegations

        except Exception as e:
            logger.error(
                f"Failed to get delegations to validator {validator_address}: {e}"
            )
            raise

    def get_redelegations_from_validator(
        self, src_validator_address: str
    ) -> List[Dict[str, Any]]:
        """
        Get all outgoing redelegations from a validator.

        Args:
            src_validator_address: Source validator address

        Returns:
            List of redelegation information from this validator
        """
        try:
            request = staking_query_pb2.QueryRedelegationsRequest()
            request.src_validator_addr = src_validator_address
            path = "/cosmos.staking.v1beta1.Query/Redelegations"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            redelegations = []
            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = staking_query_pb2.QueryRedelegationsResponse()
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    for redelegation_response in response_obj.redelegation_responses:
                        redelegation = redelegation_response.redelegation
                        redelegation_entry = {
                            "delegator_address": redelegation.delegator_address,
                            "validator_src_address": redelegation.validator_src_address,
                            "validator_dst_address": redelegation.validator_dst_address,
                            "entries": [],
                        }

                        for entry in redelegation_response.entries:
                            redelegation_entry["entries"].append(
                                {
                                    "creation_height": str(
                                        entry.redelegation_entry.creation_height
                                    ),
                                    "completion_time": (
                                        entry.redelegation_entry.completion_time.ToDatetime().isoformat()
                                        if entry.redelegation_entry.completion_time
                                        else ""
                                    ),
                                    "initial_balance": entry.redelegation_entry.initial_balance,
                                    "shares_dst": entry.redelegation_entry.shares_dst,
                                    "balance": entry.balance,
                                }
                            )

                        redelegations.append(redelegation_entry)

                    logger.info(
                        f"Retrieved {len(redelegations)} redelegations from validator {src_validator_address}"
                    )

            return redelegations

        except Exception as e:
            logger.error(
                f"Failed to get redelegations from validator {src_validator_address}: {e}"
            )
            raise

    def get_unbonding_delegations_from_validator(
        self, validator_address: str
    ) -> List[Dict[str, Any]]:
        """
        Get all unbonding delegations from a validator.

        Args:
            validator_address: Validator operator address

        Returns:
            List of unbonding delegation information from this validator
        """
        try:
            request = staking_query_pb2.QueryValidatorUnbondingDelegationsRequest()
            request.validator_addr = validator_address
            path = "/cosmos.staking.v1beta1.Query/ValidatorUnbondingDelegations"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            unbonding_delegations = []
            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = (
                        staking_query_pb2.QueryValidatorUnbondingDelegationsResponse()
                    )
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    for unbonding_delegation in response_obj.unbonding_responses:
                        unbonding_entry = {
                            "delegator_address": unbonding_delegation.delegator_address,
                            "validator_address": unbonding_delegation.validator_address,
                            "entries": [],
                        }

                        for entry in unbonding_delegation.entries:
                            unbonding_entry["entries"].append(
                                {
                                    "creation_height": str(entry.creation_height),
                                    "completion_time": (
                                        entry.completion_time.ToDatetime().isoformat()
                                        if entry.completion_time
                                        else ""
                                    ),
                                    "initial_balance": entry.initial_balance,
                                    "balance": entry.balance,
                                }
                            )

                        unbonding_delegations.append(unbonding_entry)

                    logger.info(
                        f"Retrieved {len(unbonding_delegations)} unbonding delegations from validator {validator_address}"
                    )

            return unbonding_delegations

        except Exception as e:
            logger.error(
                f"Failed to get unbonding delegations from validator {validator_address}: {e}"
            )
            raise

    def get_historical_info(self, height: int) -> Optional[Dict[str, Any]]:
        """
        Query historical info at given height.

        Args:
            height: Block height to query

        Returns:
            Historical info or None
        """
        try:
            request = staking_query_pb2.QueryHistoricalInfoRequest()
            request.height = height
            path = "/cosmos.staking.v1beta1.Query/HistoricalInfo"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = staking_query_pb2.QueryHistoricalInfoResponse()
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    if response_obj.hist:
                        return {
                            "header": {
                                "height": str(response_obj.hist.header.height),
                                "time": (
                                    response_obj.hist.header.time.ToDatetime().isoformat()
                                    if response_obj.hist.header.time
                                    else ""
                                ),
                                "chain_id": response_obj.hist.header.chain_id,
                            },
                            "validators_count": len(response_obj.hist.valset),
                        }

            return None

        except Exception as e:
            logger.error(f"Failed to get historical info at height {height}: {e}")
            raise

    def get_pool(self) -> Dict[str, Any]:
        """
        Query the current staking pool values.

        Returns:
            Staking pool information
        """
        try:
            request = staking_query_pb2.QueryPoolRequest()
            path = "/cosmos.staking.v1beta1.Query/Pool"
            request_data = request.SerializeToString()

            response = self.akash_client.rpc_query(
                "abci_query", [path, request_data.hex().upper(), "0", False]
            )

            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    response_obj = staking_query_pb2.QueryPoolResponse()
                    response_obj.ParseFromString(
                        base64.b64decode(response_data["value"])
                    )

                    if response_obj.pool:
                        return {
                            "not_bonded_tokens": response_obj.pool.not_bonded_tokens,
                            "bonded_tokens": response_obj.pool.bonded_tokens,
                        }

            return {}

        except Exception as e:
            logger.error(f"Failed to get staking pool: {e}")
            raise
