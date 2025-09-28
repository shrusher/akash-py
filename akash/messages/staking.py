"""
Staking message conversions.

Converts dictionary representations to protobuf messages for staking operations.
"""

import base64
from google.protobuf.any_pb2 import Any

from akash.proto.cosmos.base.v1beta1.coin_pb2 import Coin


def convert_msg_delegate(msg_dict, any_msg):
    """Convert MsgDelegate dictionary to protobuf."""
    from akash.proto.cosmos.staking.v1beta1.tx_pb2 import MsgDelegate

    pb_msg = MsgDelegate()
    pb_msg.delegator_address = msg_dict.get("delegator_address", "")
    pb_msg.validator_address = msg_dict.get("validator_address", "")
    amount_data = msg_dict.get("amount", {})
    coin = Coin(
        denom=amount_data.get("denom", "uakt"),
        amount=str(amount_data.get("amount", "0")),
    )
    pb_msg.amount.CopyFrom(coin)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_undelegate(msg_dict, any_msg):
    """Convert MsgUndelegate dictionary to protobuf."""
    from akash.proto.cosmos.staking.v1beta1.tx_pb2 import MsgUndelegate

    pb_msg = MsgUndelegate()
    pb_msg.delegator_address = msg_dict.get("delegator_address", "")
    pb_msg.validator_address = msg_dict.get("validator_address", "")
    amount_data = msg_dict.get("amount", {})
    coin = Coin(
        denom=amount_data.get("denom", "uakt"),
        amount=str(amount_data.get("amount", "0")),
    )
    pb_msg.amount.CopyFrom(coin)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_begin_redelegate(msg_dict, any_msg):
    """Convert MsgBeginRedelegate dictionary to protobuf."""
    from akash.proto.cosmos.staking.v1beta1.tx_pb2 import MsgBeginRedelegate

    pb_msg = MsgBeginRedelegate()
    pb_msg.delegator_address = msg_dict.get("delegator_address", "")
    pb_msg.validator_src_address = msg_dict.get("validator_src_address", "")
    pb_msg.validator_dst_address = msg_dict.get("validator_dst_address", "")
    amount_data = msg_dict.get("amount", {})
    coin = Coin(
        denom=amount_data.get("denom", "uakt"),
        amount=str(amount_data.get("amount", "0")),
    )
    pb_msg.amount.CopyFrom(coin)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_create_validator(msg_dict, any_msg):
    """Convert MsgCreateValidator dictionary to protobuf."""
    from akash.proto.cosmos.staking.v1beta1.tx_pb2 import MsgCreateValidator
    from akash.proto.cosmos.staking.v1beta1.staking_pb2 import (
        CommissionRates,
        Description,
    )

    pb_msg = MsgCreateValidator()

    desc_data = msg_dict.get("description", {})
    description = Description(
        moniker=desc_data.get("moniker", ""),
        identity=desc_data.get("identity", ""),
        website=desc_data.get("website", ""),
        security_contact=desc_data.get("security_contact", ""),
        details=desc_data.get("details", ""),
    )
    pb_msg.description.CopyFrom(description)

    comm_data = msg_dict.get("commission", {})

    def decimal_to_int(decimal_str):
        from decimal import Decimal

        decimal_val = Decimal(decimal_str)
        return str(int(decimal_val * (10**18)))

    commission = CommissionRates(
        rate=decimal_to_int(comm_data.get("rate", "0.100000000000000000")),
        max_rate=decimal_to_int(comm_data.get("max_rate", "0.200000000000000000")),
        max_change_rate=decimal_to_int(
            comm_data.get("max_change_rate", "0.010000000000000000")
        ),
    )
    pb_msg.commission.CopyFrom(commission)

    pb_msg.min_self_delegation = str(msg_dict.get("min_self_delegation", "1"))
    pb_msg.delegator_address = msg_dict.get("delegator_address", "")
    pb_msg.validator_address = msg_dict.get("validator_address", "")

    if "pubkey" in msg_dict:
        pubkey_data = msg_dict["pubkey"]
        if isinstance(pubkey_data, dict) and "key" in pubkey_data:
            pubkey_bytes = base64.b64decode(pubkey_data.get("key", ""))
        else:
            pubkey_bytes = base64.b64decode(pubkey_data)
        from akash.proto.cosmos.crypto.ed25519.keys_pb2 import PubKey as Ed25519PubKey

        ed25519_pubkey = Ed25519PubKey(key=pubkey_bytes)
        pubkey_any = Any()
        pubkey_any.Pack(ed25519_pubkey)
        pubkey_any.type_url = "/cosmos.crypto.ed25519.PubKey"
        pb_msg.pubkey.CopyFrom(pubkey_any)

    value_data = msg_dict.get("value", {})
    if value_data:
        coin = Coin(
            denom=value_data.get("denom", "uakt"),
            amount=str(value_data.get("amount", "0")),
        )
        pb_msg.value.CopyFrom(coin)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_edit_validator(msg_dict, any_msg):
    """Convert MsgEditValidator dictionary to protobuf."""
    from akash.proto.cosmos.staking.v1beta1.tx_pb2 import MsgEditValidator
    from akash.proto.cosmos.staking.v1beta1.staking_pb2 import Description

    pb_msg = MsgEditValidator()
    pb_msg.validator_address = msg_dict.get("validator_address", "")

    if "description" in msg_dict:
        desc_data = msg_dict["description"]
        description = Description(
            moniker=desc_data.get("moniker", ""),
            identity=desc_data.get("identity", ""),
            website=desc_data.get("website", ""),
            security_contact=desc_data.get("security_contact", ""),
            details=desc_data.get("details", ""),
        )
        pb_msg.description.CopyFrom(description)

    if "commission_rate" in msg_dict:
        pb_msg.commission_rate = str(msg_dict.get("commission_rate"))

    if "min_self_delegation" in msg_dict:
        pb_msg.min_self_delegation = str(msg_dict.get("min_self_delegation"))

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
