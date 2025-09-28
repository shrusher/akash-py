"""
Bank message conversions.

Converts dictionary representations to protobuf messages for banking operations.
"""

from akash.proto.cosmos.base.v1beta1.coin_pb2 import Coin


def convert_msg_send(msg_dict, any_msg):
    """Convert MsgSend dictionary to protobuf."""
    from akash.proto.cosmos.bank.v1beta1.tx_pb2 import MsgSend

    pb_msg = MsgSend()
    pb_msg.from_address = msg_dict.get("from_address", "")
    pb_msg.to_address = msg_dict.get("to_address", "")
    for coin_data in msg_dict.get("amount", []):
        coin = Coin(
            denom=coin_data.get("denom", "uakt"),
            amount=str(coin_data.get("amount", "0")),
        )
        pb_msg.amount.append(coin)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
