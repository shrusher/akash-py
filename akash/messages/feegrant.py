"""
Feegrant message conversions.

Converts dictionary representations to protobuf messages for fee grant operations.
"""

from datetime import datetime

from akash.proto.cosmos.base.v1beta1.coin_pb2 import Coin


def convert_msg_grant_allowance(msg_dict, any_msg):
    """Convert MsgGrantAllowance dictionary to protobuf."""
    from akash.proto.cosmos.feegrant.v1beta1.tx_pb2 import MsgGrantAllowance

    pb_msg = MsgGrantAllowance()
    pb_msg.granter = msg_dict.get("granter", "")
    pb_msg.grantee = msg_dict.get("grantee", "")

    allowance_data = msg_dict.get("allowance")
    if allowance_data:
        from google.protobuf.any_pb2 import Any as AnyProto

        allowance_any = AnyProto()
        if isinstance(allowance_data, dict) and "@type" in allowance_data:
            from akash.tx import _convert_dict_to_any

            allowance_any = _convert_dict_to_any(allowance_data)
        pb_msg.allowance.CopyFrom(allowance_any)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_revoke_allowance(msg_dict, any_msg):
    """Convert MsgRevokeAllowance dictionary to protobuf."""
    from akash.proto.cosmos.feegrant.v1beta1.tx_pb2 import MsgRevokeAllowance

    pb_msg = MsgRevokeAllowance()
    pb_msg.granter = msg_dict.get("granter", "")
    pb_msg.grantee = msg_dict.get("grantee", "")
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_basic_allowance(msg_dict, any_msg):
    """Convert BasicAllowance dictionary to protobuf."""
    from akash.proto.cosmos.feegrant.v1beta1.feegrant_pb2 import BasicAllowance

    pb_msg = BasicAllowance()

    spend_limit = msg_dict.get("spend_limit", [])
    for coin_data in spend_limit:
        coin = Coin()
        coin.denom = coin_data.get("denom", "")
        coin.amount = coin_data.get("amount", "")
        pb_msg.spend_limit.append(coin)

    expiration = msg_dict.get("expiration")
    if expiration:
        from google.protobuf.timestamp_pb2 import Timestamp

        exp_timestamp = Timestamp()
        if isinstance(expiration, str):
            dt = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
            exp_timestamp.seconds = int(dt.timestamp())
            exp_timestamp.nanos = dt.microsecond * 1000
        pb_msg.expiration.CopyFrom(exp_timestamp)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_periodic_allowance(msg_dict, any_msg):
    """Convert PeriodicAllowance dictionary to protobuf."""
    from akash.proto.cosmos.feegrant.v1beta1.feegrant_pb2 import (
        PeriodicAllowance,
        BasicAllowance,
    )

    pb_msg = PeriodicAllowance()

    basic_data = msg_dict.get("basic")
    if basic_data:
        basic_allowance = BasicAllowance()
        spend_limit = basic_data.get("spend_limit", [])
        for coin_data in spend_limit:
            coin = Coin()
            coin.denom = coin_data.get("denom", "")
            coin.amount = coin_data.get("amount", "")
            basic_allowance.spend_limit.append(coin)
        pb_msg.basic.CopyFrom(basic_allowance)

    period = msg_dict.get("period")
    if period:
        from google.protobuf.duration_pb2 import Duration

        period_duration = Duration()
        if isinstance(period, dict):
            period_duration.seconds = period.get("seconds", 0)
            period_duration.nanos = period.get("nanos", 0)
        elif isinstance(period, int):
            period_duration.seconds = period
        pb_msg.period.CopyFrom(period_duration)

    period_spend_limit = msg_dict.get("period_spend_limit", [])
    for coin_data in period_spend_limit:
        coin = Coin()
        coin.denom = coin_data.get("denom", "")
        coin.amount = coin_data.get("amount", "")
        pb_msg.period_spend_limit.append(coin)
    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
