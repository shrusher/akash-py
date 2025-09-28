"""
Authz message conversions.

Converts dictionary representations to protobuf messages for authorization operations.
"""

from datetime import datetime
from google.protobuf.any_pb2 import Any

from akash.proto.cosmos.base.v1beta1.coin_pb2 import Coin


def convert_msg_grant(msg_dict, any_msg):
    """Convert MsgGrant dictionary to protobuf."""
    from akash.proto.cosmos.authz.v1beta1.tx_pb2 import MsgGrant
    from akash.proto.cosmos.authz.v1beta1.authz_pb2 import Grant, GenericAuthorization
    from akash.proto.cosmos.bank.v1beta1.authz_pb2 import SendAuthorization
    from google.protobuf.timestamp_pb2 import Timestamp

    pb_msg = MsgGrant()
    pb_msg.granter = msg_dict["granter"]
    pb_msg.grantee = msg_dict["grantee"]

    grant = Grant()

    grant_data = msg_dict["grant"]
    authorization_any = Any()

    if "authorization" in grant_data:
        auth_data = grant_data["authorization"]
        auth_type = auth_data.get("@type", "")

        if auth_type == "/cosmos.bank.v1beta1.SendAuthorization":
            send_auth = SendAuthorization()
            for coin_data in auth_data.get("spend_limit", []):
                coin = Coin()
                coin.denom = coin_data["denom"]
                coin.amount = coin_data["amount"]
                send_auth.spend_limit.append(coin)
            authorization_any.Pack(send_auth)
            authorization_any.type_url = auth_type
        elif auth_type == "/cosmos.authz.v1beta1.GenericAuthorization":
            generic_auth = GenericAuthorization()
            generic_auth.msg = auth_data.get("msg", "")
            authorization_any.Pack(generic_auth)
            authorization_any.type_url = auth_type

        grant.authorization.CopyFrom(authorization_any)

    if "expiration" in grant_data:
        expiration_data = grant_data["expiration"]
        timestamp = Timestamp()

        if isinstance(expiration_data, str):
            dt = datetime.fromisoformat(expiration_data.replace("Z", "+00:00"))
            timestamp.seconds = int(dt.timestamp())
            timestamp.nanos = 0
        elif isinstance(expiration_data, dict):
            if "seconds" in expiration_data:
                timestamp.seconds = int(expiration_data["seconds"])
            if "nanos" in expiration_data:
                timestamp.nanos = int(expiration_data["nanos"])

        grant.expiration.CopyFrom(timestamp)

    pb_msg.grant.CopyFrom(grant)
    any_msg.Pack(pb_msg)
    any_msg.type_url = "/cosmos.authz.v1beta1.MsgGrant"
    return any_msg


def convert_msg_revoke(msg_dict, any_msg):
    """Convert MsgRevoke dictionary to protobuf."""
    from akash.proto.cosmos.authz.v1beta1.tx_pb2 import MsgRevoke

    pb_msg = MsgRevoke()
    pb_msg.granter = msg_dict.get("granter", "")
    pb_msg.grantee = msg_dict.get("grantee", "")
    pb_msg.msg_type_url = msg_dict.get("msg_type_url", "")
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_exec(msg_dict, any_msg):
    """Convert MsgExec dictionary to protobuf."""
    from akash.proto.cosmos.authz.v1beta1.tx_pb2 import MsgExec
    from akash.tx import _convert_dict_to_any

    pb_msg = MsgExec()
    pb_msg.grantee = msg_dict.get("grantee", "")
    for exec_msg in msg_dict.get("msgs", []):
        exec_any = _convert_dict_to_any(exec_msg)
        pb_msg.msgs.append(exec_any)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
