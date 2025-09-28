import base64
import logging
from typing import Dict, List, Any

from akash.proto.cosmos.distribution.v1beta1 import query_pb2 as distribution_query_pb2

logger = logging.getLogger(__name__)


class DistributionQuery:
    """
    Mixin for distribution query operations.
    """

    def get_delegator_rewards(
        self, delegator_address: str, validator_address: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Query delegator rewards.

        Args:
            delegator_address: Address of the delegator
            validator_address: Optional validator address to filter by

        Returns:
            list: List of rewards
        """
        try:
            if validator_address:
                request = distribution_query_pb2.QueryDelegationRewardsRequest()
                request.delegator_address = delegator_address
                request.validator_address = validator_address
                path = "/cosmos.distribution.v1beta1.Query/DelegationRewards"
            else:
                request = distribution_query_pb2.QueryDelegationTotalRewardsRequest()
                request.delegator_address = delegator_address
                path = "/cosmos.distribution.v1beta1.Query/DelegationTotalRewards"

            result = self.akash_client.abci_query(
                path=path, data=request.SerializeToString().hex()
            )

            if not result or "response" not in result:
                raise Exception(f"ABCI query failed for {path}: no response")

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                raise Exception(
                    f"ABCI query failed for {path}: Empty or invalid response"
                )

            data = base64.b64decode(response_data["value"])

            if validator_address:
                response = distribution_query_pb2.QueryDelegationRewardsResponse()
                response.ParseFromString(data)
                return [
                    {"denom": reward.denom, "amount": reward.amount}
                    for reward in response.rewards
                ]
            else:
                response = distribution_query_pb2.QueryDelegationTotalRewardsResponse()
                response.ParseFromString(data)
                all_rewards = []
                for delegation_reward in response.rewards:
                    validator_rewards = {
                        "validator_address": delegation_reward.validator_address,
                        "rewards": [
                            {"denom": reward.denom, "amount": reward.amount}
                            for reward in delegation_reward.reward
                        ],
                    }
                    all_rewards.append(validator_rewards)
                return all_rewards

        except Exception as e:
            logger.error(f"Get delegator rewards failed: {e}")
            raise

    def get_validator_commission(self, validator_address: str) -> Dict[str, Any]:
        """
        Query validator commission.

        Args:
            validator_address: Address of the validator

        Returns:
            dict: Validator commission info
        """
        try:
            request = distribution_query_pb2.QueryValidatorCommissionRequest()
            request.validator_address = validator_address
            path = "/cosmos.distribution.v1beta1.Query/ValidatorCommission"

            result = self.akash_client.abci_query(
                path=path, data=request.SerializeToString().hex()
            )

            if not result or "response" not in result:
                raise Exception(
                    "ABCI query failed for ValidatorCommission: no response"
                )

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                raise Exception(
                    "ABCI query failed for ValidatorCommission: Empty or invalid response"
                )

            data = base64.b64decode(response_data["value"])
            response = distribution_query_pb2.QueryValidatorCommissionResponse()
            response.ParseFromString(data)

            return {
                "commission": [
                    {"denom": commission.denom, "amount": commission.amount}
                    for commission in response.commission.commission
                ]
            }

        except Exception as e:
            logger.error(f"Get validator commission failed: {e}")
            raise

    def get_validator_outstanding_rewards(
        self, validator_address: str
    ) -> Dict[str, Any]:
        """
        Query validator outstanding rewards.

        Args:
            validator_address: Address of the validator

        Returns:
            dict: Outstanding rewards info
        """
        try:
            request = distribution_query_pb2.QueryValidatorOutstandingRewardsRequest()
            request.validator_address = validator_address
            path = "/cosmos.distribution.v1beta1.Query/ValidatorOutstandingRewards"

            result = self.akash_client.abci_query(
                path=path, data=request.SerializeToString().hex()
            )

            if not result or "response" not in result:
                raise Exception(
                    "ABCI query failed for ValidatorOutstandingRewards: no response"
                )

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                raise Exception(
                    "ABCI query failed for ValidatorOutstandingRewards: Empty or invalid response"
                )

            data = base64.b64decode(response_data["value"])
            response = distribution_query_pb2.QueryValidatorOutstandingRewardsResponse()
            response.ParseFromString(data)

            return {
                "rewards": [
                    {"denom": reward.denom, "amount": reward.amount}
                    for reward in response.rewards.rewards
                ]
            }

        except Exception as e:
            logger.error(f"Get validator outstanding rewards failed: {e}")
            raise

    def get_distribution_params(self) -> Dict[str, Any]:
        """
        Query distribution parameters.

        Returns:
            dict: Distribution parameters
        """
        try:
            request = distribution_query_pb2.QueryParamsRequest()
            path = "/cosmos.distribution.v1beta1.Query/Params"

            result = self.akash_client.abci_query(
                path=path, data=request.SerializeToString().hex()
            )

            if not result or "response" not in result:
                raise Exception(
                    "ABCI query failed for distribution Params: no response"
                )

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                raise Exception(
                    "ABCI query failed for distribution Params: Empty or invalid response"
                )

            data = base64.b64decode(response_data["value"])
            response = distribution_query_pb2.QueryParamsResponse()
            response.ParseFromString(data)

            return {
                "community_tax": response.params.community_tax,
                "base_proposer_reward": response.params.base_proposer_reward,
                "bonus_proposer_reward": response.params.bonus_proposer_reward,
                "withdraw_addr_enabled": response.params.withdraw_addr_enabled,
            }

        except Exception as e:
            logger.error(f"Get distribution params failed: {e}")
            raise

    def get_community_pool(self) -> Dict[str, Any]:
        """
        Query the community pool coins.

        Returns:
            dict: Community pool information
        """
        try:
            request = distribution_query_pb2.QueryCommunityPoolRequest()
            path = "/cosmos.distribution.v1beta1.Query/CommunityPool"

            result = self.akash_client.abci_query(
                path=path, data=request.SerializeToString().hex()
            )

            if not result or "response" not in result:
                raise Exception("ABCI query failed for CommunityPool: no response")

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                raise Exception(
                    "ABCI query failed for CommunityPool: Empty or invalid response"
                )

            data = base64.b64decode(response_data["value"])
            response = distribution_query_pb2.QueryCommunityPoolResponse()
            response.ParseFromString(data)

            return {
                "pool": [
                    {"denom": coin.denom, "amount": coin.amount}
                    for coin in response.pool
                ]
            }

        except Exception as e:
            logger.error(f"Get community pool failed: {e}")
            raise

    def get_validator_slashes(
        self, validator_address: str, starting_height: int = 1, ending_height: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query validator slashes.

        Args:
            validator_address: Validator operator address
            starting_height: Starting block height
            ending_height: Ending block height

        Returns:
            list: List of validator slashes
        """
        try:
            request = distribution_query_pb2.QueryValidatorSlashesRequest()
            request.validator_address = validator_address
            request.starting_height = starting_height
            request.ending_height = ending_height
            path = "/cosmos.distribution.v1beta1.Query/ValidatorSlashes"

            result = self.akash_client.abci_query(
                path=path, data=request.SerializeToString().hex()
            )

            if not result or "response" not in result:
                raise Exception("ABCI query failed for ValidatorSlashes: no response")

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                return []

            data = base64.b64decode(response_data["value"])
            response = distribution_query_pb2.QueryValidatorSlashesResponse()
            response.ParseFromString(data)

            return [
                {
                    "validator_period": str(slash.validator_period),
                    "fraction": slash.fraction,
                }
                for slash in response.slashes
            ]

        except Exception as e:
            logger.error(f"Get validator slashes failed: {e}")
            raise
