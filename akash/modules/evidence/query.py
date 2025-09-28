import base64
import logging
from typing import Dict, List, Any

from akash.proto.cosmos.base.query.v1beta1 import pagination_pb2 as pagination_pb
from akash.proto.cosmos.evidence.v1beta1 import query_pb2 as evidence_query_pb

logger = logging.getLogger(__name__)


class EvidenceQuery:
    """
    Mixin for evidence query operations.
    """

    def get_evidence(self, evidence_hash: str) -> Dict[str, Any]:
        """
        Query specific evidence by hash.

        Args:
            evidence_hash: Hash of the evidence to query

        Returns:
            dict: Evidence information
        """
        try:
            logger.info(f"Querying evidence with hash: {evidence_hash}")

            request = evidence_query_pb.QueryEvidenceRequest()
            request.evidence_hash = (
                bytes.fromhex(evidence_hash) if evidence_hash else b""
            )

            result = self.akash_client.abci_query(
                path="/cosmos.evidence.v1beta1.Query/Evidence",
                data=request.SerializeToString().hex(),
            )

            if not result or "response" not in result:
                raise Exception("ABCI query failed for Evidence: no response")

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                raise Exception(
                    "ABCI query failed for Evidence: Empty or invalid response"
                )

            data = base64.b64decode(response_data["value"])
            response = evidence_query_pb.QueryEvidenceResponse()
            response.ParseFromString(data)

            evidence_info = {
                "evidence": {
                    "type_url": (
                        response.evidence.type_url if response.evidence else None
                    )
                }
            }

            logger.info(f"Retrieved evidence for hash: {evidence_hash}")
            return evidence_info

        except Exception as e:
            logger.error(f"Get evidence failed: {e}")
            return {}

    def get_all_evidence(
        self, limit: int = 100, offset: int = 0, count_total: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query all evidence records.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            count_total: Include total count in response

        Returns:
            list: List of evidence records
        """
        try:
            logger.info(f"Querying all evidence with limit: {limit}, offset: {offset}")

            request = evidence_query_pb.QueryAllEvidenceRequest()
            pagination = pagination_pb.PageRequest()
            pagination.limit = limit
            pagination.offset = offset
            pagination.count_total = count_total
            request.pagination.CopyFrom(pagination)

            result = self.akash_client.abci_query(
                path="/cosmos.evidence.v1beta1.Query/AllEvidence",
                data=request.SerializeToString().hex(),
            )

            if not result or "response" not in result:
                raise Exception("ABCI query failed for AllEvidence: no response")

            response_data = result["response"]
            if response_data.get("code", -1) != 0 or not response_data.get("value"):
                return []

            data = base64.b64decode(response_data["value"])
            response = evidence_query_pb.QueryAllEvidenceResponse()
            response.ParseFromString(data)

            evidence_list = [
                {"type_url": evidence.type_url, "evidence_data": evidence.value.hex()}
                for evidence in response.evidence
            ]

            logger.info(f"Retrieved {len(evidence_list)} evidence records")
            return evidence_list

        except Exception as e:
            logger.error(f"Get all evidence failed: {e}")
            return []
