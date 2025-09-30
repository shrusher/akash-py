"""
Deployment message conversions.

Converts dictionary representations to protobuf messages for deployment operations.
"""

from akash.proto.cosmos.base.v1beta1.coin_pb2 import Coin


def convert_msg_create_deployment(msg_dict, any_msg):
    """Convert MsgCreateDeployment dictionary to protobuf."""
    from akash.proto.akash.deployment.v1beta3.deploymentmsg_pb2 import (
        MsgCreateDeployment,
    )
    from akash.proto.akash.deployment.v1beta3.deployment_pb2 import DeploymentID
    from akash.proto.akash.deployment.v1beta3.groupspec_pb2 import GroupSpec
    from akash.proto.akash.base.v1beta3.attribute_pb2 import (
        PlacementRequirements,
        SignedBy,
    )
    from akash.proto.akash.deployment.v1beta3.resourceunit_pb2 import ResourceUnit
    from akash.proto.akash.base.v1beta3.resources_pb2 import Resources
    from akash.proto.akash.base.v1beta3.cpu_pb2 import CPU
    from akash.proto.akash.base.v1beta3.memory_pb2 import Memory
    from akash.proto.akash.base.v1beta3.storage_pb2 import Storage
    from akash.proto.akash.base.v1beta3.resourcevalue_pb2 import ResourceValue
    from akash.proto.cosmos.base.v1beta1.coin_pb2 import DecCoin

    pb_msg = MsgCreateDeployment()

    deployment_id = DeploymentID()
    deployment_id.owner = msg_dict["id"]["owner"]
    deployment_id.dseq = int(msg_dict["id"]["dseq"])
    pb_msg.id.CopyFrom(deployment_id)

    if "version" in msg_dict and msg_dict["version"]:
        if isinstance(msg_dict["version"], str):
            try:
                pb_msg.version = bytes.fromhex(msg_dict["version"])
            except ValueError:
                import hashlib
                pb_msg.version = hashlib.sha256(msg_dict["version"].encode("utf-8")).digest()
        else:
            pb_msg.version = msg_dict["version"]
    else:
        import hashlib
        import json
        deployment_data = json.dumps(msg_dict, sort_keys=True).encode("utf-8")
        version_hash = hashlib.sha256(deployment_data).digest()
        pb_msg.version = version_hash
    pb_msg.depositor = msg_dict["depositor"]

    deposit_coin = Coin()
    deposit_coin.denom = msg_dict["deposit"]["denom"]
    deposit_coin.amount = msg_dict["deposit"]["amount"]
    pb_msg.deposit.CopyFrom(deposit_coin)

    for group_data in msg_dict["groups"]:
        group_spec = GroupSpec()
        group_spec.name = group_data["name"]

        signed_by = SignedBy()
        placement_reqs = PlacementRequirements(signed_by=signed_by)
        group_spec.requirements.CopyFrom(placement_reqs)

        for resource_data in group_data["resources"]:
            resource_unit = ResourceUnit()

            resources = Resources()
            resources.id = resource_data["resource"]["id"]

            cpu_val = ResourceValue(
                val=resource_data["resource"]["cpu"]["units"]["val"].encode("utf-8")
            )
            cpu = CPU(units=cpu_val)
            resources.cpu.CopyFrom(cpu)

            memory_val = ResourceValue(
                val=resource_data["resource"]["memory"]["quantity"]["val"].encode(
                    "utf-8"
                )
            )
            memory = Memory(quantity=memory_val)
            resources.memory.CopyFrom(memory)

            for storage_data in resource_data["resource"]["storage"]:
                storage_val = ResourceValue(
                    val=storage_data["quantity"]["val"].encode("utf-8")
                )
                storage = Storage(name=storage_data["name"], quantity=storage_val)

                if "attributes" in storage_data and storage_data["attributes"]:
                    from akash.proto.akash.base.v1beta3.attribute_pb2 import Attribute
                    for attr_data in storage_data["attributes"]:
                        attr = Attribute()
                        attr.key = attr_data["key"]
                        attr.value = attr_data["value"]
                        storage.attributes.append(attr)

                resources.storage.append(storage)

            from akash.proto.akash.base.v1beta3.gpu_pb2 import GPU

            gpu_units = resource_data["resource"].get("gpu", {}).get("units", {}).get("val", "0")
            gpu_val = ResourceValue(val=gpu_units.encode("utf-8"))
            gpu = GPU(units=gpu_val)

            gpu_attributes = resource_data["resource"].get("gpu", {}).get("attributes", [])
            if gpu_attributes:
                from akash.proto.akash.base.v1beta3.attribute_pb2 import Attribute
                for attr_data in gpu_attributes:
                    attr = Attribute()
                    attr.key = attr_data["key"]
                    attr.value = attr_data["value"]
                    gpu.attributes.append(attr)

            resources.gpu.CopyFrom(gpu)

            if "endpoints" in resource_data["resource"]:
                from akash.proto.akash.base.v1beta3.endpoint_pb2 import Endpoint

                for endpoint_data in resource_data["resource"]["endpoints"]:
                    endpoint = Endpoint()
                    endpoint.kind = endpoint_data.get("kind", 0)  # 0 = SHARED_HTTP
                    endpoint.sequence_number = endpoint_data.get("sequence_number", 0)
                    resources.endpoints.append(endpoint)

            resource_unit.resource.CopyFrom(resources)
            resource_unit.count = resource_data["count"]

            price_coin = DecCoin()
            price_coin.denom = resource_data["price"]["denom"]
            price_coin.amount = resource_data["price"]["amount"]
            resource_unit.price.CopyFrom(price_coin)

            group_spec.resources.append(resource_unit)

        pb_msg.groups.append(group_spec)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_update_deployment(msg_dict, any_msg):
    """Convert MsgUpdateDeployment dictionary to protobuf."""
    from akash.proto.akash.deployment.v1beta3.deploymentmsg_pb2 import (
        MsgUpdateDeployment,
    )
    from akash.proto.akash.deployment.v1beta3.deployment_pb2 import DeploymentID

    pb_msg = MsgUpdateDeployment()

    deployment_id = DeploymentID()
    deployment_id.owner = msg_dict["id"]["owner"]
    deployment_id.dseq = int(msg_dict["id"]["dseq"])
    pb_msg.id.CopyFrom(deployment_id)

    if "version" in msg_dict and msg_dict["version"]:
        if isinstance(msg_dict["version"], str):
            try:
                pb_msg.version = bytes.fromhex(msg_dict["version"])
            except ValueError:
                import hashlib
                pb_msg.version = hashlib.sha256(msg_dict["version"].encode("utf-8")).digest()
        else:
            pb_msg.version = msg_dict["version"]
    else:
        import hashlib
        import json
        deployment_data = json.dumps(msg_dict, sort_keys=True).encode("utf-8")
        version_hash = hashlib.sha256(deployment_data).digest()
        pb_msg.version = version_hash

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_close_deployment(msg_dict, any_msg):
    """Convert MsgCloseDeployment dictionary to protobuf."""
    from akash.proto.akash.deployment.v1beta3.deploymentmsg_pb2 import (
        MsgCloseDeployment,
    )
    from akash.proto.akash.deployment.v1beta3.deployment_pb2 import DeploymentID

    pb_msg = MsgCloseDeployment()

    deployment_id = DeploymentID()
    deployment_id.owner = msg_dict["id"]["owner"]
    deployment_id.dseq = int(msg_dict["id"]["dseq"])
    pb_msg.id.CopyFrom(deployment_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_deposit_deployment(msg_dict, any_msg):
    """Convert MsgDepositDeployment dictionary to protobuf."""
    from akash.proto.akash.deployment.v1beta3.deploymentmsg_pb2 import (
        MsgDepositDeployment,
    )
    from akash.proto.akash.deployment.v1beta3.deployment_pb2 import DeploymentID
    from akash.proto.cosmos.base.v1beta1.coin_pb2 import Coin

    pb_msg = MsgDepositDeployment()

    deployment_id = DeploymentID()
    deployment_id.owner = msg_dict["id"]["owner"]
    deployment_id.dseq = int(msg_dict["id"]["dseq"])
    pb_msg.id.CopyFrom(deployment_id)

    amount_coin = Coin()
    amount_coin.denom = msg_dict["amount"]["denom"]
    amount_coin.amount = msg_dict["amount"]["amount"]
    pb_msg.amount.CopyFrom(amount_coin)

    pb_msg.depositor = msg_dict["depositor"]

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_close_group(msg_dict, any_msg):
    """Convert MsgCloseGroup dictionary to protobuf."""
    from akash.proto.akash.deployment.v1beta3.groupmsg_pb2 import MsgCloseGroup
    from akash.proto.akash.deployment.v1beta3.groupid_pb2 import GroupID

    pb_msg = MsgCloseGroup()

    group_id = GroupID()
    group_id.owner = msg_dict["id"]["owner"]
    group_id.dseq = int(msg_dict["id"]["dseq"])
    group_id.gseq = msg_dict["id"]["gseq"]
    pb_msg.id.CopyFrom(group_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_pause_group(msg_dict, any_msg):
    """Convert MsgPauseGroup dictionary to protobuf."""
    from akash.proto.akash.deployment.v1beta3.groupmsg_pb2 import MsgPauseGroup
    from akash.proto.akash.deployment.v1beta3.groupid_pb2 import GroupID

    pb_msg = MsgPauseGroup()

    group_id = GroupID()
    group_id.owner = msg_dict["id"]["owner"]
    group_id.dseq = int(msg_dict["id"]["dseq"])
    group_id.gseq = msg_dict["id"]["gseq"]
    pb_msg.id.CopyFrom(group_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg


def convert_msg_start_group(msg_dict, any_msg):
    """Convert MsgStartGroup dictionary to protobuf."""
    from akash.proto.akash.deployment.v1beta3.groupmsg_pb2 import MsgStartGroup
    from akash.proto.akash.deployment.v1beta3.groupid_pb2 import GroupID

    pb_msg = MsgStartGroup()

    group_id = GroupID()
    group_id.owner = msg_dict["id"]["owner"]
    group_id.dseq = int(msg_dict["id"]["dseq"])
    group_id.gseq = msg_dict["id"]["gseq"]
    pb_msg.id.CopyFrom(group_id)

    any_msg.Pack(pb_msg, type_url_prefix="")
    return any_msg
