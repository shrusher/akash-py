"""
Distribution message conversions.

Converts dictionary representations to protobuf messages for distribution operations.
"""


def convert_msg_withdraw_delegator_reward(msg_dict, any_msg):
    """Convert MsgWithdrawDelegatorReward dictionary to protobuf."""
    from akash.proto.cosmos.distribution.v1beta1.tx_pb2 import (
        MsgWithdrawDelegatorReward,
    )

    pb_msg = MsgWithdrawDelegatorReward()
    pb_msg.delegator_address = msg_dict.get("delegator_address", "")
    pb_msg.validator_address = msg_dict.get("validator_address", "")
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_set_withdraw_address(msg_dict, any_msg):
    """Convert MsgSetWithdrawAddress dictionary to protobuf."""
    from akash.proto.cosmos.distribution.v1beta1.tx_pb2 import MsgSetWithdrawAddress

    pb_msg = MsgSetWithdrawAddress()
    pb_msg.delegator_address = msg_dict.get("delegator_address", "")
    pb_msg.withdraw_address = msg_dict.get("withdraw_address", "")
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
