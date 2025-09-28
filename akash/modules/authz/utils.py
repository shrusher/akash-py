import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AuthzUtils:
    """
    Mixin for authorization utilities.
    """

    def _parse_authorization_details(self, authorization_any) -> Dict[str, Any]:
        """
        Parse authorization details from Any type protobuf message.

        Args:
            authorization_any: Any type containing authorization data

        Returns:
            Dict: Parsed authorization details with type-specific fields
        """
        auth_dict = {
            "@type": authorization_any.type_url,
        }

        if authorization_any.type_url == "/cosmos.bank.v1beta1.SendAuthorization":
            from akash.proto.cosmos.bank.v1beta1.authz_pb2 import SendAuthorization

            send_auth = SendAuthorization()
            send_auth.ParseFromString(authorization_any.value)
            spend_limit = []
            for coin in send_auth.spend_limit:
                spend_limit.append({"denom": coin.denom, "amount": coin.amount})
            auth_dict["spend_limit"] = spend_limit
        elif authorization_any.type_url == "/cosmos.authz.v1beta1.GenericAuthorization":
            from akash.proto.cosmos.authz.v1beta1.authz_pb2 import GenericAuthorization

            generic_auth = GenericAuthorization()
            generic_auth.ParseFromString(authorization_any.value)
            auth_dict["msg"] = generic_auth.msg

        return auth_dict
