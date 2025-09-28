"""
Audit message conversions.

Converts dictionary representations to protobuf messages for audit operations.
"""


def convert_msg_sign_provider_attributes(msg_dict, any_msg):
    """Convert MsgSignProviderAttributes dictionary to protobuf."""
    from akash.proto.akash.audit.v1beta3.audit_pb2 import MsgSignProviderAttributes

    pb_msg = MsgSignProviderAttributes()
    pb_msg.owner = msg_dict.get("owner", "")
    pb_msg.auditor = msg_dict.get("auditor", "")

    for attr in msg_dict.get("attributes", []):
        attr_pb = pb_msg.attributes.add()
        attr_pb.key = attr.get("key", "")
        attr_pb.value = attr.get("value", "")

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_delete_provider_attributes(msg_dict, any_msg):
    """Convert MsgDeleteProviderAttributes dictionary to protobuf."""
    from akash.proto.akash.audit.v1beta3.audit_pb2 import MsgDeleteProviderAttributes

    pb_msg = MsgDeleteProviderAttributes()
    pb_msg.owner = msg_dict.get("owner", "")
    pb_msg.auditor = msg_dict.get("auditor", "")

    for key in msg_dict.get("keys", []):
        pb_msg.keys.append(key)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
