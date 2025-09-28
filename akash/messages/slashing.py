"""
Slashing message conversions.

Converts dictionary representations to protobuf messages for slashing operations.
"""


def convert_msg_unjail(msg_dict, any_msg):
    """Convert MsgUnjail dictionary to protobuf."""
    from akash.proto.cosmos.slashing.v1beta1.tx_pb2 import MsgUnjail

    pb_msg = MsgUnjail()
    pb_msg.validator_addr = msg_dict.get("validator_addr", "")
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
