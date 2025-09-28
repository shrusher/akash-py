import base64
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GovernanceQuery:
    """
    Mixin for governance query operations.
    """

    def get_proposals(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        count_total: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get governance proposals.

        Args:
            status: Filter by proposal status (voting_period, deposit_period, passed, rejected)
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            List of proposals
        """
        try:
            from akash.proto.cosmos.gov.v1beta1 import query_pb2
            from akash.proto.cosmos.gov.v1beta1.gov_pb2 import ProposalStatus
            from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import PageRequest

            request = query_pb2.QueryProposalsRequest()

            if status:
                status_map = {
                    "deposit_period": ProposalStatus.PROPOSAL_STATUS_DEPOSIT_PERIOD,
                    "voting_period": ProposalStatus.PROPOSAL_STATUS_VOTING_PERIOD,
                    "passed": ProposalStatus.PROPOSAL_STATUS_PASSED,
                    "rejected": ProposalStatus.PROPOSAL_STATUS_REJECTED,
                    "failed": ProposalStatus.PROPOSAL_STATUS_FAILED,
                }
                if status.lower() in status_map:
                    request.proposal_status = status_map[status.lower()]

            page_request = PageRequest()
            page_request.limit = limit
            page_request.offset = offset
            page_request.count_total = count_total
            request.pagination.CopyFrom(page_request)

            data = request.SerializeToString().hex()

            query_path = "/cosmos.gov.v1beta1.Query/Proposals"
            result = self.akash_client.abci_query(query_path, data)

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
                logger.info("Query succeeded but no proposals found")
                return []

            response_data = base64.b64decode(response["value"])
            proposals_response = query_pb2.QueryProposalsResponse()
            proposals_response.ParseFromString(response_data)

            proposals = []
            for proposal in proposals_response.proposals:
                title = "Unknown"
                content_info = {}

                try:
                    if proposal.content and proposal.content.type_url:
                        if (
                            proposal.content.type_url
                            == "/cosmos.gov.v1beta1.TextProposal"
                        ):
                            from akash.proto.cosmos.gov.v1beta1.gov_pb2 import (
                                TextProposal,
                            )

                            text_proposal = TextProposal()
                            proposal.content.Unpack(text_proposal)
                            title = (
                                text_proposal.title[:50]
                                if text_proposal.title
                                else "Text Proposal"
                            )
                            content_info = {
                                "title": text_proposal.title,
                                "description": (
                                    text_proposal.description[:100] + "..."
                                    if len(text_proposal.description) > 100
                                    else text_proposal.description
                                ),
                                "type": "TextProposal",
                            }
                        elif (
                            proposal.content.type_url
                            == "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal"
                        ):
                            title = f"Software Upgrade Proposal {proposal.proposal_id}"
                            content_info = {"type": "SoftwareUpgradeProposal"}
                        elif (
                            proposal.content.type_url
                            == "/cosmos.params.v1beta1.ParameterChangeProposal"
                        ):
                            title = f"Parameter Change Proposal {proposal.proposal_id}"
                            content_info = {"type": "ParameterChangeProposal"}
                        else:
                            title = f"Proposal {proposal.proposal_id}"
                            content_info = {
                                "type": proposal.content.type_url.split("/")[-1]
                            }
                except Exception as e:
                    title = f"Proposal {proposal.proposal_id}"
                    content_info = {"error": f"Failed to parse content: {str(e)[:50]}"}

                proposals.append(
                    {
                        "proposal_id": proposal.proposal_id,
                        "content": content_info,
                        "title": title,
                        "status": proposal.status,
                        "final_tally_result": {
                            "yes": proposal.final_tally_result.yes,
                            "abstain": proposal.final_tally_result.abstain,
                            "no": proposal.final_tally_result.no,
                            "no_with_veto": proposal.final_tally_result.no_with_veto,
                        },
                        "submit_time": str(proposal.submit_time),
                        "deposit_end_time": str(proposal.deposit_end_time),
                        "total_deposit": [
                            {"denom": d.denom, "amount": d.amount}
                            for d in proposal.total_deposit
                        ],
                        "voting_start_time": str(proposal.voting_start_time),
                        "voting_end_time": str(proposal.voting_end_time),
                    }
                )

            return proposals

        except Exception as e:
            logger.error(f"Failed to get proposals: {e}")
            raise

    def get_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """
        Get detailed proposal information.

        Args:
            proposal_id: Proposal ID

        Returns:
            Proposal information
        """
        try:
            from akash.proto.cosmos.gov.v1beta1 import query_pb2

            request = query_pb2.QueryProposalRequest()
            request.proposal_id = proposal_id

            data = request.SerializeToString().hex()

            query_path = "/cosmos.gov.v1beta1.Query/Proposal"
            result = self.akash_client.abci_query(query_path, data)

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
                logger.info(f"Query succeeded but proposal {proposal_id} not found")
                return {}

            response_data = base64.b64decode(response["value"])
            proposal_response = query_pb2.QueryProposalResponse()
            proposal_response.ParseFromString(response_data)

            if proposal_response.proposal:
                proposal = proposal_response.proposal

                title = "Unknown"
                description = "Unknown"

                if proposal.content:
                    try:
                        from akash.proto.cosmos.gov.v1beta1.gov_pb2 import TextProposal
                        from akash.proto.cosmos.params.v1beta1.params_pb2 import (
                            ParameterChangeProposal,
                        )
                        from akash.proto.cosmos.upgrade.v1beta1.upgrade_pb2 import (
                            SoftwareUpgradeProposal,
                        )

                        content_any = proposal.content

                        if content_any.type_url == "/cosmos.gov.v1beta1.TextProposal":
                            text_proposal = TextProposal()
                            content_any.Unpack(text_proposal)
                            title = text_proposal.title
                            description = text_proposal.description
                        elif (
                            content_any.type_url
                            == "/cosmos.params.v1beta1.ParameterChangeProposal"
                        ):
                            param_proposal = ParameterChangeProposal()
                            content_any.Unpack(param_proposal)
                            title = param_proposal.title
                            description = param_proposal.description
                        elif (
                            content_any.type_url
                            == "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal"
                        ):
                            upgrade_proposal = SoftwareUpgradeProposal()
                            content_any.Unpack(upgrade_proposal)
                            title = upgrade_proposal.title
                            description = upgrade_proposal.description
                        else:
                            title = getattr(
                                proposal.content,
                                "title",
                                f"Proposal {content_any.type_url}",
                            )
                            description = getattr(
                                proposal.content,
                                "description",
                                "No description available",
                            )
                    except Exception as e:
                        logger.warning(f"Could not extract proposal content: {e}")
                        title = f"Proposal {proposal.proposal_id}"
                        description = "Could not extract description"

                return {
                    "proposal_id": proposal.proposal_id,
                    "status": proposal.status,
                    "title": title,
                    "description": description,
                    "total_deposit": [
                        {"denom": d.denom, "amount": d.amount}
                        for d in proposal.total_deposit
                    ],
                    "voting_start_time": (
                        str(proposal.voting_start_time)
                        if proposal.voting_start_time
                        else None
                    ),
                    "voting_end_time": (
                        str(proposal.voting_end_time)
                        if proposal.voting_end_time
                        else None
                    ),
                }

            return {}

        except Exception as e:
            logger.error(f"Failed to get proposal info: {e}")
            raise

    def get_proposal_votes(
        self,
        proposal_id: int,
        limit: int = 100,
        offset: int = 0,
        count_total: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all votes for a proposal. Only works for proposals in voting stage.

        Args:
            proposal_id: Proposal ID
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            List of votes
        """
        try:
            from akash.proto.cosmos.gov.v1beta1 import query_pb2
            from akash.proto.cosmos.base.query.v1beta1.pagination_pb2 import PageRequest

            request = query_pb2.QueryVotesRequest()
            request.proposal_id = proposal_id

            page_request = PageRequest()
            page_request.limit = limit
            page_request.offset = offset
            page_request.count_total = count_total
            request.pagination.CopyFrom(page_request)

            data = request.SerializeToString().hex()

            query_path = "/cosmos.gov.v1beta1.Query/Votes"
            result = self.akash_client.abci_query(query_path, data)

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
                    f"Query succeeded but no votes found for proposal {proposal_id}"
                )
                return []

            response_data = base64.b64decode(response["value"])
            votes_response = query_pb2.QueryVotesResponse()
            votes_response.ParseFromString(response_data)

            votes = []
            for vote in votes_response.votes:
                votes.append(
                    {
                        "proposal_id": vote.proposal_id,
                        "voter": vote.voter,
                        "option": vote.option,
                        "options": (
                            [
                                {"option": opt.option, "weight": opt.weight}
                                for opt in vote.options
                            ]
                            if vote.options
                            else []
                        ),
                    }
                )

            return votes

        except Exception as e:
            logger.error(f"Failed to get votes: {e}")
            raise

    def get_vote(self, proposal_id: int, voter_address: str) -> Dict[str, Any]:
        """
        Get a specific vote for a proposal from a voter.

        Args:
            proposal_id: Proposal ID
            voter_address: Voter address

        Returns:
            Vote information or empty dict if no vote found
        """
        try:
            from akash.proto.cosmos.gov.v1beta1 import query_pb2

            request = query_pb2.QueryVoteRequest()
            request.proposal_id = proposal_id
            request.voter = voter_address

            data = request.SerializeToString().hex()

            query_path = "/cosmos.gov.v1beta1.Query/Vote"
            result = self.akash_client.abci_query(query_path, data)

            if not result or "response" not in result:
                logger.debug(f"Query failed: No response from {query_path}")
                return {}

            response = result["response"]
            response_code = response.get("code", -1)

            if response_code != 0:
                logger.debug(
                    f"Query failed: {query_path} returned code {response_code}"
                )
                return {}

            if "value" not in response or not response["value"]:
                logger.debug(
                    f"No vote found for proposal {proposal_id} from voter {voter_address}"
                )
                return {}

            response_data = base64.b64decode(response["value"])
            vote_response = query_pb2.QueryVoteResponse()
            vote_response.ParseFromString(response_data)

            if vote_response.vote:
                vote = vote_response.vote
                return {
                    "proposal_id": vote.proposal_id,
                    "voter": vote.voter,
                    "option": vote.option,
                    "options": (
                        [
                            {"option": opt.option, "weight": opt.weight}
                            for opt in vote.options
                        ]
                        if vote.options
                        else []
                    ),
                }

            return {}

        except Exception as e:
            logger.debug(f"Failed to get vote: {e}")
            return {}

    def get_proposal_deposits(self, proposal_id: int) -> List[Dict[str, Any]]:
        """
        Get all deposits for a proposal.

        Args:
            proposal_id: Proposal ID

        Returns:
            List of deposits
        """
        try:
            from akash.proto.cosmos.gov.v1beta1 import query_pb2

            request = query_pb2.QueryDepositsRequest()
            request.proposal_id = proposal_id

            data = request.SerializeToString().hex()

            query_path = "/cosmos.gov.v1beta1.Query/Deposits"
            result = self.akash_client.abci_query(query_path, data)

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
                    f"Query succeeded but no deposits found for proposal {proposal_id}"
                )
                return []

            response_data = base64.b64decode(response["value"])
            deposits_response = query_pb2.QueryDepositsResponse()
            deposits_response.ParseFromString(response_data)

            deposits = []
            for deposit in deposits_response.deposits:
                deposits.append(
                    {
                        "proposal_id": deposit.proposal_id,
                        "depositor": deposit.depositor,
                        "amount": [
                            {"denom": coin.denom, "amount": coin.amount}
                            for coin in deposit.amount
                        ],
                    }
                )

            return deposits

        except Exception as e:
            logger.error(f"Failed to get deposits: {e}")
            raise

    def get_proposal_tally(self, proposal_id: int) -> Dict[str, Any]:
        """
        Get vote tally for a proposal.

        Args:
            proposal_id: Proposal ID

        Returns:
            Vote tally information
        """
        try:
            from akash.proto.cosmos.gov.v1beta1 import query_pb2

            request = query_pb2.QueryTallyResultRequest()
            request.proposal_id = proposal_id

            data = request.SerializeToString().hex()

            query_path = "/cosmos.gov.v1beta1.Query/TallyResult"
            result = self.akash_client.abci_query(query_path, data)

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
                    f"Query succeeded but no tally available for proposal {proposal_id}"
                )
                return {"yes": "0", "abstain": "0", "no": "0", "no_with_veto": "0"}

            response_data = base64.b64decode(response["value"])
            tally_response = query_pb2.QueryTallyResultResponse()
            tally_response.ParseFromString(response_data)

            if tally_response.tally:
                tally = tally_response.tally
                return {
                    "yes": tally.yes,
                    "abstain": tally.abstain,
                    "no": tally.no,
                    "no_with_veto": tally.no_with_veto,
                }

            return {"yes": "0", "abstain": "0", "no": "0", "no_with_veto": "0"}

        except Exception as e:
            logger.error(f"Failed to get tally: {e}")
            raise

    def get_governance_params(self) -> Dict[str, Any]:
        """
        Get governance module parameters - all param types.

        Returns:
            Dict of governance parameters
        """
        try:
            from akash.proto.cosmos.gov.v1beta1 import query_pb2

            all_params = {}
            param_types = ["voting", "deposit", "tallying"]

            for param_type in param_types:
                logger.info(f"Querying governance {param_type} parameters")

                request = query_pb2.QueryParamsRequest()
                request.params_type = param_type
                data = request.SerializeToString().hex()

                query_path = "/cosmos.gov.v1beta1.Query/Params"
                result = self.akash_client.abci_query(query_path, data)

                if not result or "response" not in result:
                    logger.warning(f"No response for {param_type} params")
                    continue

                response = result["response"]
                response_code = response.get("code", -1)

                if response_code != 0:
                    logger.warning(
                        f"{param_type} params query failed with code {response_code}"
                    )
                    continue

                if "value" not in response or not response["value"]:
                    logger.info(f"No {param_type} params found")
                    continue

                response_data = base64.b64decode(response["value"])
                params_response = query_pb2.QueryParamsResponse()
                params_response.ParseFromString(response_data)

                if param_type == "voting" and params_response.voting_params:
                    voting_period = params_response.voting_params.voting_period
                    if hasattr(voting_period, "seconds"):
                        all_params["voting_period_seconds"] = int(voting_period.seconds)
                    all_params["voting_period"] = str(voting_period)

                elif param_type == "deposit" and params_response.deposit_params:
                    deposit_params = params_response.deposit_params
                    max_deposit_period = deposit_params.max_deposit_period
                    if hasattr(max_deposit_period, "seconds"):
                        all_params["max_deposit_period_seconds"] = int(
                            max_deposit_period.seconds
                        )
                    all_params["max_deposit_period"] = str(max_deposit_period)

                    if deposit_params.min_deposit:
                        all_params["min_deposit"] = []
                        for coin in deposit_params.min_deposit:
                            all_params["min_deposit"].append(
                                {"denom": coin.denom, "amount": coin.amount}
                            )

                elif param_type == "tallying" and params_response.tally_params:
                    tally_params = params_response.tally_params
                    all_params["quorum"] = tally_params.quorum
                    all_params["threshold"] = tally_params.threshold
                    all_params["veto_threshold"] = tally_params.veto_threshold

            return all_params

        except Exception as e:
            logger.error(f"Failed to get governance params: {e}")
            raise
