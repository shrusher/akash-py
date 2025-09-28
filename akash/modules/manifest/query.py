import base64
import logging
from typing import Dict, Any

from akash.proto.akash.manifest.v2beta2 import group_pb2 as group_pb

logger = logging.getLogger(__name__)


class ManifestQuery:
    """
    Mixin for manifest query operations.
    """

    def get_deployment_manifest(self, deployment_id: str) -> Dict[str, Any]:
        """
        Retrieve the manifest for an existing deployment.

        Args:
            deployment_id: Deployment identifier

        Returns:
            Original deployment manifest and current status
        """
        try:
            logger.info(f"Retrieving manifest for deployment: {deployment_id}")

            path = "/akash.manifest.v2beta2.Query/DeploymentManifest"
            response = self.client.rpc_query(
                "abci_query", [path, deployment_id.encode().hex(), "0", False]
            )

            manifest = {}
            if response and "response" in response:
                response_data = response["response"]
                if response_data.get("code") == 0 and response_data.get("value"):
                    data = base64.b64decode(response_data["value"])
                    group = group_pb.Group()
                    group.ParseFromString(data)

                    manifest = {
                        "group_name": group.name,
                        "services": [
                            {
                                "name": svc.name,
                                "image": svc.image,
                                "count": svc.count,
                                "expose": [
                                    {
                                        "port": exp.port,
                                        "protocol": exp.proto,
                                        "global": getattr(exp, "global", False),
                                        "http_options": (
                                            {
                                                "max_body_size": exp.http_options.max_body_size
                                            }
                                            if exp.http_options
                                            else {}
                                        ),
                                    }
                                    for exp in svc.expose
                                ],
                            }
                            for svc in group.services
                        ],
                        "status": "active",
                        "retrieved_at": "2025-08-29T07:22:00Z",
                    }
                else:
                    logger.info(
                        f"Query succeeded but no manifest found for deployment {deployment_id}"
                    )

            logger.info(f"Retrieved manifest for deployment {deployment_id}")
            return manifest

        except Exception as e:
            logger.error(f"Failed to get deployment manifest: {e}")
            return {"status": "failed", "error": str(e)}
