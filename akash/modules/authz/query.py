import base64
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class AuthzQuery:
    """
    Mixin for authorization query operations.
    """

    def get_grants(
        self, granter: str, grantee: str = "", msg_type_url: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Query authorization grants between granter and grantee.

        Args:
            granter: Address of the account that granted authorization
            grantee: Optional address of the grantee to filter by
            msg_type_url: Optional message type to filter by

        Returns:
            List[Dict]: List of grants or raises exception on failure
        """
        logger.info(f"Querying grants for granter {granter}, grantee {grantee}")

        try:
            from akash.proto.cosmos.authz.v1beta1.query_pb2 import (
                QueryGrantsRequest,
                QueryGrantsResponse,
            )

            query_request = QueryGrantsRequest()
            query_request.granter = granter
            query_request.grantee = grantee
            if msg_type_url:
                query_request.msg_type_url = msg_type_url

            request_bytes = query_request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.abci_query(
                "/cosmos.authz.v1beta1.Query/Grants", request_hex
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code") == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = QueryGrantsResponse()
                    query_response.ParseFromString(response_data)

                    grants = []
                    for grant in query_response.grants:
                        grant_dict = {
                            "authorization": self._parse_authorization_details(
                                grant.authorization
                            ),
                            "expiration": {
                                "seconds": grant.expiration.seconds,
                                "nanos": grant.expiration.nanos,
                            },
                        }
                        grants.append(grant_dict)

                    logger.info(f"Retrieved {len(grants)} grants")
                    return grants

            logger.info("No grants found")
            return []

        except Exception as e:
            logger.error(f"Failed to query grants: {e}")
            raise Exception(
                f"Failed to query grants for granter {granter}, grantee {grantee}: {e}"
            )

    def get_granter_grants(self, granter: str) -> List[Dict[str, Any]]:
        """
        Query all grants given by a granter.

        Args:
            granter: Address of the granter

        Returns:
            List[Dict]: List of grants given by the granter or raises exception
        """
        logger.info(f"Querying granter grants for {granter}")

        try:
            from akash.proto.cosmos.authz.v1beta1.query_pb2 import (
                QueryGranterGrantsRequest,
                QueryGranterGrantsResponse,
            )

            query_request = QueryGranterGrantsRequest()
            query_request.granter = granter

            request_bytes = query_request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.abci_query(
                "/cosmos.authz.v1beta1.Query/GranterGrants", request_hex
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code") == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = QueryGranterGrantsResponse()
                    query_response.ParseFromString(response_data)

                    grants = []
                    for grant_auth in query_response.grants:
                        grant_dict = {
                            "granter": grant_auth.granter,
                            "grantee": grant_auth.grantee,
                            "authorization": self._parse_authorization_details(
                                grant_auth.authorization
                            ),
                            "expiration": {
                                "seconds": grant_auth.expiration.seconds,
                                "nanos": grant_auth.expiration.nanos,
                            },
                        }
                        grants.append(grant_dict)

                    logger.info(f"Retrieved {len(grants)} granter grants")
                    return grants

            logger.info("No granter grants found")
            return []

        except Exception as e:
            logger.error(f"Failed to query granter grants: {e}")
            raise Exception(f"Failed to query granter grants for {granter}: {e}")

    def get_grantee_grants(self, grantee: str) -> List[Dict[str, Any]]:
        """
        Query all grants received by a grantee.

        Args:
            grantee: Address of the grantee

        Returns:
            List[Dict]: List of grants received by the grantee or raises exception
        """
        logger.info(f"Querying grantee grants for {grantee}")

        try:
            from akash.proto.cosmos.authz.v1beta1.query_pb2 import (
                QueryGranteeGrantsRequest,
                QueryGranteeGrantsResponse,
            )

            query_request = QueryGranteeGrantsRequest()
            query_request.grantee = grantee

            request_bytes = query_request.SerializeToString()
            request_hex = request_bytes.hex().upper()

            result = self.akash_client.abci_query(
                "/cosmos.authz.v1beta1.Query/GranteeGrants", request_hex
            )

            if result and "response" in result:
                response = result["response"]
                if response.get("code") == 0 and response.get("value"):

                    response_data = base64.b64decode(response["value"])
                    query_response = QueryGranteeGrantsResponse()
                    query_response.ParseFromString(response_data)

                    grants = []
                    for grant_auth in query_response.grants:
                        grant_dict = {
                            "granter": grant_auth.granter,
                            "grantee": grant_auth.grantee,
                            "authorization": self._parse_authorization_details(
                                grant_auth.authorization
                            ),
                            "expiration": {
                                "seconds": grant_auth.expiration.seconds,
                                "nanos": grant_auth.expiration.nanos,
                            },
                        }
                        grants.append(grant_dict)

                    logger.info(f"Retrieved {len(grants)} grantee grants")
                    return grants

            logger.info("No grantee grants found")
            return []

        except Exception as e:
            logger.error(f"Failed to query grantee grants: {e}")
            raise Exception(f"Failed to query grantee grants for {grantee}: {e}")
