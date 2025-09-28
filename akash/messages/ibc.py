"""
IBC message conversions.

Converts dictionary representations to protobuf messages for IBC operations.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def convert_msg_transfer(msg_dict: Dict[str, Any], any_msg) -> Any:
    """Convert MsgTransfer dictionary to protobuf Any message."""
    try:
        from akash.proto.ibc.applications.transfer.v1 import tx_pb2

        msg = tx_pb2.MsgTransfer()
        msg.source_port = msg_dict.get("source_port", "transfer")
        msg.source_channel = msg_dict.get("source_channel", "")
        msg.sender = msg_dict.get("sender", "")
        msg.receiver = msg_dict.get("receiver", "")
        msg.memo = msg_dict.get("memo", "")

        if "token" in msg_dict:
            token_info = msg_dict["token"]
            msg.token.denom = token_info.get("denom", "")
            msg.token.amount = str(token_info.get("amount", "0"))

        if "timeout_height" in msg_dict:
            height_info = msg_dict["timeout_height"]
            msg.timeout_height.revision_number = int(
                height_info.get("revision_number", 0)
            )
            msg.timeout_height.revision_height = int(
                height_info.get("revision_height", 0)
            )

        if "timeout_timestamp" in msg_dict:
            msg.timeout_timestamp = int(msg_dict["timeout_timestamp"])

        any_msg.Pack(msg, type_url_prefix="")
        return any_msg

    except Exception as e:
        logger.error(f"Failed to convert MsgTransfer: {e}")
        raise


def convert_msg_create_client(msg_dict, any_msg):
    """Convert MsgCreateClient dictionary to protobuf."""
    try:
        from akash.proto.ibc.core.client.v1 import tx_pb2
        from akash.proto.ibc.lightclients.tendermint.v1 import tendermint_pb2
        from akash.proto import proofs_pb2
        from google.protobuf import any_pb2
        from datetime import datetime

        msg = tx_pb2.MsgCreateClient()
        msg.signer = msg_dict.get("signer", "")

        if "client_state" in msg_dict:
            client_state_dict = msg_dict["client_state"]

            if (
                isinstance(client_state_dict, dict)
                and client_state_dict.get("@type")
                == "/ibc.lightclients.tendermint.v1.ClientState"
            ):
                tm_client_state = tendermint_pb2.ClientState()
                tm_client_state.chain_id = client_state_dict.get("chain_id", "")

                trust_level = client_state_dict.get("trust_level", {})
                tm_client_state.trust_level.numerator = int(
                    trust_level.get("numerator", 1)
                )
                tm_client_state.trust_level.denominator = int(
                    trust_level.get("denominator", 3)
                )

                trusting_period = client_state_dict.get("trusting_period", "1209600s")
                tm_client_state.trusting_period.seconds = int(
                    trusting_period.rstrip("s")
                )

                unbonding_period = client_state_dict.get("unbonding_period", "1814400s")
                tm_client_state.unbonding_period.seconds = int(
                    unbonding_period.rstrip("s")
                )

                max_clock_drift = client_state_dict.get("max_clock_drift", "600s")
                tm_client_state.max_clock_drift.seconds = int(
                    max_clock_drift.rstrip("s")
                )

                frozen_height = client_state_dict.get("frozen_height", {})
                tm_client_state.frozen_height.revision_number = int(
                    frozen_height.get("revision_number", 0)
                )
                tm_client_state.frozen_height.revision_height = int(
                    frozen_height.get("revision_height", 0)
                )

                latest_height = client_state_dict.get("latest_height", {})
                tm_client_state.latest_height.revision_number = int(
                    latest_height.get("revision_number", 0)
                )
                tm_client_state.latest_height.revision_height = int(
                    latest_height.get("revision_height", 0)
                )

                for spec_dict in client_state_dict.get("proof_specs", []):
                    proof_spec = proofs_pb2.ProofSpec()

                    leaf = spec_dict.get("leaf_spec", {})
                    proof_spec.leaf_spec.hash = 1  # SHA256
                    proof_spec.leaf_spec.prehash_key = 0  # NO_HASH
                    proof_spec.leaf_spec.prehash_value = 1  # SHA256
                    proof_spec.leaf_spec.length = 1  # VAR_PROTO
                    if leaf.get("prefix"):
                        import base64

                        proof_spec.leaf_spec.prefix = base64.b64decode(leaf["prefix"])

                    inner = spec_dict.get("inner_spec", {})
                    proof_spec.inner_spec.child_order.extend(
                        inner.get("child_order", [0, 1])
                    )
                    proof_spec.inner_spec.child_size = inner.get("child_size", 33)
                    proof_spec.inner_spec.min_prefix_length = inner.get(
                        "min_prefix_length", 4
                    )
                    proof_spec.inner_spec.max_prefix_length = inner.get(
                        "max_prefix_length", 12
                    )
                    proof_spec.inner_spec.hash = 1  # SHA256

                    proof_spec.max_depth = spec_dict.get("max_depth", 0)
                    proof_spec.min_depth = spec_dict.get("min_depth", 0)

                    tm_client_state.proof_specs.append(proof_spec)

                tm_client_state.upgrade_path.extend(
                    client_state_dict.get(
                        "upgrade_path", ["upgrade", "upgradedIBCState"]
                    )
                )

                tm_client_state.allow_update_after_expiry = client_state_dict.get(
                    "allow_update_after_expiry", True
                )
                tm_client_state.allow_update_after_misbehaviour = client_state_dict.get(
                    "allow_update_after_misbehaviour", True
                )

                client_state_any = any_pb2.Any()
                client_state_any.type_url = (
                    "/ibc.lightclients.tendermint.v1.ClientState"
                )
                client_state_any.value = tm_client_state.SerializeToString()
                msg.client_state.CopyFrom(client_state_any)
            else:
                if hasattr(client_state_dict, "CopyFrom"):
                    msg.client_state.CopyFrom(client_state_dict)
                else:
                    client_state_any = any_pb2.Any()
                    client_state_any.CopyFrom(client_state_dict)
                    msg.client_state.CopyFrom(client_state_any)

        if "consensus_state" in msg_dict:
            consensus_state_dict = msg_dict["consensus_state"]

            if (
                isinstance(consensus_state_dict, dict)
                and consensus_state_dict.get("@type")
                == "/ibc.lightclients.tendermint.v1.ConsensusState"
            ):

                tm_consensus_state = tendermint_pb2.ConsensusState()

                timestamp_str = consensus_state_dict.get("timestamp", "")
                if timestamp_str:
                    if "." in timestamp_str:
                        # Nanosecond precision
                        dt_str = timestamp_str.split(".")[0] + "Z"
                        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    else:
                        dt = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )

                    tm_consensus_state.timestamp.seconds = int(dt.timestamp())
                    tm_consensus_state.timestamp.nanos = dt.microsecond * 1000

                root = consensus_state_dict.get("root", {})
                if isinstance(root, dict):
                    import base64

                    root_hash = root.get("hash", "")
                    if root_hash:
                        tm_consensus_state.root.hash = base64.b64decode(root_hash)

                next_validators_hash = consensus_state_dict.get(
                    "next_validators_hash", ""
                )
                if next_validators_hash:
                    tm_consensus_state.next_validators_hash = bytes.fromhex(
                        next_validators_hash
                    )

                consensus_state_any = any_pb2.Any()
                consensus_state_any.type_url = (
                    "/ibc.lightclients.tendermint.v1.ConsensusState"
                )
                consensus_state_any.value = tm_consensus_state.SerializeToString()
                msg.consensus_state.CopyFrom(consensus_state_any)
            else:
                if hasattr(consensus_state_dict, "CopyFrom"):
                    msg.consensus_state.CopyFrom(consensus_state_dict)
                else:
                    consensus_state_any = any_pb2.Any()
                    consensus_state_any.CopyFrom(consensus_state_dict)
                    msg.consensus_state.CopyFrom(consensus_state_any)

        any_msg.Pack(msg, type_url_prefix="")
        return any_msg

    except Exception as e:
        logger.error(f"Failed to convert MsgCreateClient: {e}")
        raise


def convert_msg_update_client(msg_dict, any_msg):
    """Convert MsgUpdateClient using native protobuf approach."""
    return convert_msg_update_client_with_native_protobuf(msg_dict, any_msg)


def convert_msg_update_client_with_native_protobuf(msg_dict, any_msg):
    """Convert MsgUpdateClient using native protobuf classes."""
    try:
        from akash.proto.ibc.core.client.v1 import tx_pb2
        from akash.proto.ibc.lightclients.tendermint.v1.tendermint_pb2 import Header
        from google.protobuf import any_pb2

        tm_header = Header()

        if "header" in msg_dict and msg_dict["header"]:
            _populate_tendermint_header_no_block_hash(tm_header, msg_dict["header"])

        packed_header = any_pb2.Any()
        packed_header.type_url = "/ibc.lightclients.tendermint.v1.Header"
        packed_header.value = tm_header.SerializeToString()

        msg = tx_pb2.MsgUpdateClient()
        msg.client_id = msg_dict.get("client_id", "")
        msg.signer = msg_dict.get("signer", "")
        msg.header.CopyFrom(packed_header)

        any_msg.type_url = "/ibc.core.client.v1.MsgUpdateClient"
        any_msg.value = msg.SerializeToString()

        return any_msg

    except Exception as e:
        logger.error(f"Native protobuf IBC client update failed: {e}")
        raise


def _populate_tendermint_header_no_block_hash(tm_header, header_data):
    """Populate Tendermint Header without setting block_id.hash to avoid mismatch."""
    try:
        import base64

        if "signed_header" in header_data:
            signed_header_data = header_data["signed_header"]

            if "header" in signed_header_data:
                h = signed_header_data["header"]
                tm_header.signed_header.header.version.block = int(
                    h.get("version", {}).get("block", 11)
                )
                tm_header.signed_header.header.chain_id = h.get("chain_id", "")
                tm_header.signed_header.header.height = int(h.get("height", 0))

                if "time" in h and h["time"]:
                    from datetime import datetime

                    try:
                        time_str = h["time"]
                        if "." in time_str and time_str.endswith("Z"):
                            base_part, nano_part = time_str[:-1].split(".")
                            nano_part = nano_part.ljust(9, "0")
                            dt = datetime.fromisoformat(base_part + "+00:00")
                            tm_header.signed_header.header.time.FromDatetime(dt)
                            tm_header.signed_header.header.time.nanos = int(nano_part)
                        else:
                            dt = datetime.fromisoformat(
                                h["time"].replace("Z", "+00:00")
                            )
                            tm_header.signed_header.header.time.FromDatetime(dt)
                    except Exception as e:
                        logger.error(f"Failed to parse time: {h['time']}, error: {e}")

                if "last_block_id" in h and h["last_block_id"]:
                    lbid = h["last_block_id"]
                    if "hash" in lbid and lbid["hash"]:
                        hash_bytes = (
                            bytes.fromhex(lbid["hash"])
                            if len(lbid["hash"]) == 64
                            else base64.b64decode(lbid["hash"])
                        )
                        tm_header.signed_header.header.last_block_id.hash = hash_bytes

                    psh_key = "parts" if "parts" in lbid else "part_set_header"
                    if psh_key in lbid:
                        psh = lbid[psh_key]
                        tm_header.signed_header.header.last_block_id.part_set_header.total = int(
                            psh.get("total", 0)
                        )
                        if "hash" in psh and psh["hash"]:
                            hash_bytes = (
                                bytes.fromhex(psh["hash"])
                                if len(psh["hash"]) == 64
                                else base64.b64decode(psh["hash"])
                            )
                            tm_header.signed_header.header.last_block_id.part_set_header.hash = (
                                hash_bytes
                            )

                for field in [
                    "last_commit_hash",
                    "data_hash",
                    "validators_hash",
                    "next_validators_hash",
                    "consensus_hash",
                    "app_hash",
                    "last_results_hash",
                    "evidence_hash",
                ]:
                    if field in h and h[field]:
                        hash_bytes = (
                            bytes.fromhex(h[field])
                            if len(h[field]) == 64
                            else base64.b64decode(h[field])
                        )
                        setattr(tm_header.signed_header.header, field, hash_bytes)

                if "proposer_address" in h and h["proposer_address"]:
                    addr = h["proposer_address"]
                    if len(addr) == 40:  # hex
                        tm_header.signed_header.header.proposer_address = bytes.fromhex(
                            addr
                        )
                    elif len(addr) == 28:  # base64
                        tm_header.signed_header.header.proposer_address = (
                            base64.b64decode(addr)
                        )

            if "commit" in signed_header_data:
                commit_data = signed_header_data["commit"]
                tm_header.signed_header.commit.height = int(
                    commit_data.get("height", 0)
                )
                tm_header.signed_header.commit.round = int(commit_data.get("round", 0))

                if "block_id" in commit_data:
                    bid = commit_data["block_id"]
                    if "hash" in bid and bid["hash"]:
                        original_hash_bytes = (
                            bytes.fromhex(bid["hash"])
                            if len(bid["hash"]) == 64
                            else base64.b64decode(bid["hash"])
                        )
                        tm_header.signed_header.commit.block_id.hash = (
                            original_hash_bytes
                        )

                    if "parts" in bid:
                        psh = bid["parts"]
                        tm_header.signed_header.commit.block_id.part_set_header.total = int(
                            psh.get("total", 0)
                        )
                        if "hash" in psh and psh["hash"]:
                            hash_bytes = (
                                bytes.fromhex(psh["hash"])
                                if len(psh["hash"]) == 64
                                else base64.b64decode(psh["hash"])
                            )
                            tm_header.signed_header.commit.block_id.part_set_header.hash = (
                                hash_bytes
                            )

                if "signatures" in commit_data:
                    for sig_data in commit_data["signatures"]:
                        sig = tm_header.signed_header.commit.signatures.add()
                        sig.block_id_flag = int(sig_data.get("block_id_flag", 2))

                        if (
                            "validator_address" in sig_data
                            and sig_data["validator_address"]
                        ):
                            addr = sig_data["validator_address"]
                            if len(addr) == 40:  # hex
                                sig.validator_address = bytes.fromhex(addr)
                            elif len(addr) == 28:  # base64
                                sig.validator_address = base64.b64decode(addr)

                        if "timestamp" in sig_data and sig_data["timestamp"]:
                            from datetime import datetime

                            try:
                                dt = datetime.fromisoformat(
                                    sig_data["timestamp"].replace("Z", "+00:00")
                                )
                                sig.timestamp.FromDatetime(dt)
                            except BaseException:
                                sig.timestamp.FromDatetime(datetime.utcnow())

                        if "signature" in sig_data and sig_data["signature"]:
                            sig.signature = base64.b64decode(sig_data["signature"])

        if "validator_set" in header_data:
            vs = header_data["validator_set"]
            if "validators" in vs:
                for v in vs["validators"]:
                    validator = tm_header.validator_set.validators.add()
                    if "address" in v and v["address"]:
                        addr = v["address"]
                        if len(addr) == 40:  # hex
                            validator.address = bytes.fromhex(addr)
                        elif len(addr) == 28:  # base64
                            validator.address = base64.b64decode(addr)

                    if "pub_key" in v and v["pub_key"]:
                        pk = v["pub_key"]
                        key_data = pk.get("key") or pk.get("value") or pk.get("ed25519")
                        if key_data:
                            validator.pub_key.ed25519 = base64.b64decode(key_data)

                    if "voting_power" in v:
                        validator.voting_power = int(v["voting_power"])

                    if "proposer_priority" in v:
                        validator.proposer_priority = int(v["proposer_priority"])

            if (
                "signed_header" in header_data
                and "header" in header_data["signed_header"]
            ):
                h = header_data["signed_header"]["header"]
                if "proposer_address" in h and h["proposer_address"]:
                    proposer_addr = h["proposer_address"].upper()
                    for v in vs["validators"]:
                        if v.get("address", "").upper() == proposer_addr:
                            tm_header.validator_set.proposer.address = (
                                bytes.fromhex(v["address"])
                                if len(v["address"]) == 40
                                else base64.b64decode(v["address"])
                            )

                            if "pub_key" in v and v["pub_key"]:
                                pk = v["pub_key"]
                                key_data = (
                                    pk.get("key")
                                    or pk.get("value")
                                    or pk.get("ed25519")
                                )
                                if key_data:
                                    tm_header.validator_set.proposer.pub_key.ed25519 = (
                                        base64.b64decode(key_data)
                                    )

                            if "voting_power" in v:
                                tm_header.validator_set.proposer.voting_power = int(
                                    v["voting_power"]
                                )
                            if "proposer_priority" in v:
                                tm_header.validator_set.proposer.proposer_priority = (
                                    int(v["proposer_priority"])
                                )
                            break

            tm_header.validator_set.total_voting_power = 0

        if "trusted_height" in header_data:
            th = header_data["trusted_height"]
            tm_header.trusted_height.revision_number = int(th.get("revision_number", 0))
            tm_header.trusted_height.revision_height = int(th.get("revision_height", 0))

        if "trusted_validators" in header_data:
            tvs = header_data["trusted_validators"]
            if "validators" in tvs:
                for tv in tvs["validators"]:
                    tvalidator = tm_header.trusted_validators.validators.add()
                    if "address" in tv and tv["address"]:
                        addr = tv["address"]
                        if len(addr) == 40:  # hex
                            tvalidator.address = bytes.fromhex(addr)
                        elif len(addr) == 28:  # base64
                            tvalidator.address = base64.b64decode(addr)

                    if "pub_key" in tv and tv["pub_key"]:
                        pk = tv["pub_key"]
                        key_data = pk.get("key") or pk.get("value") or pk.get("ed25519")
                        if key_data:
                            tvalidator.pub_key.ed25519 = base64.b64decode(key_data)

                    if "voting_power" in tv:
                        tvalidator.voting_power = int(tv["voting_power"])

                    if "proposer_priority" in tv:
                        tvalidator.proposer_priority = int(tv["proposer_priority"])

            if tvs["validators"]:
                first_trusted = tvs["validators"][0]
                tm_header.trusted_validators.proposer.address = (
                    bytes.fromhex(first_trusted["address"])
                    if len(first_trusted["address"]) == 40
                    else base64.b64decode(first_trusted["address"])
                )

                if "pub_key" in first_trusted and first_trusted["pub_key"]:
                    pk = first_trusted["pub_key"]
                    key_data = pk.get("key") or pk.get("value") or pk.get("ed25519")
                    if key_data:
                        tm_header.trusted_validators.proposer.pub_key.ed25519 = (
                            base64.b64decode(key_data)
                        )

                if "voting_power" in first_trusted:
                    tm_header.trusted_validators.proposer.voting_power = int(
                        first_trusted["voting_power"]
                    )
                if "proposer_priority" in first_trusted:
                    tm_header.trusted_validators.proposer.proposer_priority = int(
                        first_trusted["proposer_priority"]
                    )

            tm_header.trusted_validators.total_voting_power = 0

    except Exception as e:
        logger.error(f"Error populating Tendermint header: {e}")
        raise
