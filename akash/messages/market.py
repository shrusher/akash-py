"""
Market message conversions.

Converts dictionary representations to protobuf messages for market operations.
"""


def convert_msg_create_bid(msg_dict, any_msg):
    """Convert MsgCreateBid dictionary to protobuf."""
    from akash.proto.akash.market.v1beta4.bid_pb2 import MsgCreateBid
    from akash.proto.akash.market.v1beta4.order_pb2 import OrderID
    from akash.proto.cosmos.base.v1beta1.coin_pb2 import DecCoin, Coin

    pb_msg = MsgCreateBid()

    order = msg_dict.get("order", {})
    order_id = OrderID()
    order_id.owner = order.get("owner", "")
    order_id.dseq = int(order.get("dseq", 0))
    order_id.gseq = int(order.get("gseq", 0))
    order_id.oseq = int(order.get("oseq", 0))
    pb_msg.order.CopyFrom(order_id)

    pb_msg.provider = msg_dict.get("provider", "")

    price_data = msg_dict.get("price", {})
    price = DecCoin()
    price.denom = price_data.get("denom", "")
    price.amount = price_data.get("amount", "")
    pb_msg.price.CopyFrom(price)

    deposit_data = msg_dict.get("deposit", {})
    if deposit_data:
        deposit = Coin()
        deposit.denom = deposit_data.get("denom", "")
        deposit.amount = deposit_data.get("amount", "")
        pb_msg.deposit.CopyFrom(deposit)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_close_bid(msg_dict, any_msg):
    """Convert MsgCloseBid dictionary to protobuf."""
    from akash.proto.akash.market.v1beta4.bid_pb2 import MsgCloseBid, BidID

    pb_msg = MsgCloseBid()

    id_data = msg_dict.get("id", {})
    bid_id = BidID()
    bid_id.owner = id_data.get("owner", "")
    bid_id.dseq = int(id_data.get("dseq", 0))
    bid_id.gseq = int(id_data.get("gseq", 0))
    bid_id.oseq = int(id_data.get("oseq", 0))
    bid_id.provider = id_data.get("provider", "")
    pb_msg.bid_id.CopyFrom(bid_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_create_lease(msg_dict, any_msg):
    """Convert MsgCreateLease dictionary to protobuf."""
    from akash.proto.akash.market.v1beta4.lease_pb2 import MsgCreateLease
    from akash.proto.akash.market.v1beta4.bid_pb2 import BidID

    pb_msg = MsgCreateLease()

    bid_id = BidID()
    bid_id.owner = msg_dict.get("owner", "")
    bid_id.dseq = int(msg_dict.get("dseq", 0))
    bid_id.gseq = int(msg_dict.get("gseq", 0))
    bid_id.oseq = int(msg_dict.get("oseq", 0))
    bid_id.provider = msg_dict.get("provider", "")
    pb_msg.bid_id.CopyFrom(bid_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_close_lease(msg_dict, any_msg):
    """Convert MsgCloseLease dictionary to protobuf."""
    from akash.proto.akash.market.v1beta4.lease_pb2 import MsgCloseLease, LeaseID

    pb_msg = MsgCloseLease()

    id_data = msg_dict.get("id", {})
    lease_id = LeaseID()
    lease_id.owner = id_data.get("owner", "")
    lease_id.dseq = int(id_data.get("dseq", 0))
    lease_id.gseq = int(id_data.get("gseq", 0))
    lease_id.oseq = int(id_data.get("oseq", 0))
    lease_id.provider = id_data.get("provider", "")
    pb_msg.lease_id.CopyFrom(lease_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_withdraw_lease(msg_dict, any_msg):
    """Convert MsgWithdrawLease dictionary to protobuf."""
    from akash.proto.akash.market.v1beta4.lease_pb2 import MsgWithdrawLease, LeaseID

    pb_msg = MsgWithdrawLease()

    id_data = msg_dict.get("id", {})
    lease_id = LeaseID()
    lease_id.owner = id_data.get("owner", "")
    lease_id.dseq = int(id_data.get("dseq", 0))
    lease_id.gseq = int(id_data.get("gseq", 0))
    lease_id.oseq = int(id_data.get("oseq", 0))
    lease_id.provider = id_data.get("provider", "")
    pb_msg.bid_id.CopyFrom(lease_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
