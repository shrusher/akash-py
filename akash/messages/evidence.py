"""
Evidence message conversions.

Converts dictionary representations to protobuf messages for evidence operations.
"""


def convert_msg_submit_evidence(msg_dict, any_msg):
    """Convert MsgSubmitEvidence dictionary to protobuf."""
    from akash.proto.cosmos.evidence.v1beta1.tx_pb2 import MsgSubmitEvidence
    from google.protobuf import any_pb2

    pb_msg = MsgSubmitEvidence()
    pb_msg.submitter = msg_dict.get("submitter", "")

    evidence_data = msg_dict.get("evidence", {})
    if evidence_data:
        evidence_any = any_pb2.Any()
        evidence_any.type_url = evidence_data.get("@type", "")
        evidence_any.value = evidence_data.get("value", b"")
        pb_msg.evidence.CopyFrom(evidence_any)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
