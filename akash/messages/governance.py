"""
Governance message conversions.

Converts dictionary representations to protobuf messages for governance operations.
"""

from google.protobuf.any_pb2 import Any

from akash.proto.cosmos.base.v1beta1.coin_pb2 import Coin


def convert_msg_submit_proposal(msg_dict, any_msg):
    """Convert MsgSubmitProposal dictionary to protobuf."""
    from akash.proto.cosmos.gov.v1beta1.tx_pb2 import MsgSubmitProposal
    from akash.proto.cosmos.gov.v1beta1.gov_pb2 import TextProposal
    from akash.proto.cosmos.params.v1beta1.params_pb2 import (
        ParameterChangeProposal,
        ParamChange,
    )
    from akash.proto.cosmos.upgrade.v1beta1.upgrade_pb2 import (
        SoftwareUpgradeProposal,
        Plan,
    )

    pb_msg = MsgSubmitProposal()
    pb_msg.proposer = msg_dict.get("proposer", "")

    if "content" in msg_dict:
        content = msg_dict["content"]
        content_type = content.get("@type", "")
        content_any = Any()

        if content_type == "/cosmos.gov.v1beta1.TextProposal":
            content_msg = TextProposal()
            content_msg.title = content.get("title", "")
            content_msg.description = content.get("description", "")
            content_any.Pack(content_msg)
            content_any.type_url = "/cosmos.gov.v1beta1.TextProposal"

        elif content_type == "/cosmos.params.v1beta1.ParameterChangeProposal":
            content_msg = ParameterChangeProposal()
            content_msg.title = content.get("title", "")
            content_msg.description = content.get("description", "")

            for change_data in content.get("changes", []):
                param_change = ParamChange()
                param_change.subspace = change_data.get("subspace", "")
                param_change.key = change_data.get("key", "")
                param_change.value = change_data.get("value", "")
                content_msg.changes.append(param_change)

            content_any.Pack(content_msg)
            content_any.type_url = "/cosmos.params.v1beta1.ParameterChangeProposal"

        elif content_type == "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal":
            content_msg = SoftwareUpgradeProposal()
            content_msg.title = content.get("title", "")
            content_msg.description = content.get("description", "")

            if "plan" in content:
                plan_data = content["plan"]
                upgrade_plan = Plan()
                upgrade_plan.name = plan_data.get("name", "")
                upgrade_plan.height = int(plan_data.get("height", 0))
                upgrade_plan.info = plan_data.get("info", "")
                content_msg.plan.CopyFrom(upgrade_plan)

            content_any.Pack(content_msg)
            content_any.type_url = "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal"

        pb_msg.content.CopyFrom(content_any)

    for coin_data in msg_dict.get("initial_deposit", []):
        coin = Coin(
            denom=coin_data.get("denom", "uakt"),
            amount=str(coin_data.get("amount", "0")),
        )
        pb_msg.initial_deposit.append(coin)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_deposit(msg_dict, any_msg):
    """Convert MsgDeposit dictionary to protobuf."""
    from akash.proto.cosmos.gov.v1beta1.tx_pb2 import MsgDeposit

    pb_msg = MsgDeposit()
    pb_msg.proposal_id = int(msg_dict.get("proposal_id", 0))
    pb_msg.depositor = msg_dict.get("depositor", "")

    for coin_data in msg_dict.get("amount", []):
        coin = Coin(
            denom=coin_data.get("denom", "uakt"),
            amount=str(coin_data.get("amount", "0")),
        )
        pb_msg.amount.append(coin)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_vote(msg_dict, any_msg):
    """Convert MsgVote dictionary to protobuf."""
    from akash.proto.cosmos.gov.v1beta1.tx_pb2 import MsgVote

    pb_msg = MsgVote()
    pb_msg.proposal_id = int(msg_dict.get("proposal_id", 0))
    pb_msg.voter = msg_dict.get("voter", "")

    vote_options = {"YES": 1, "Abstain": 2, "NO": 3, "NO_WITH_VETO": 4}
    pb_msg.option = vote_options.get(msg_dict.get("option", "Abstain"), 2)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
