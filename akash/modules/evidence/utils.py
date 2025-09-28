import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EvidenceUtils:
    """
    Mixin for evidence utilities.
    """

    def validate_evidence_format(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate evidence data format.

        Args:
            evidence_data: Evidence data to validate

        Returns:
            dict: Validation results
        """
        try:
            logger.info("Validating evidence format")

            validation_results = {"valid": False, "errors": [], "warnings": []}

            if not evidence_data.get("type_url"):
                validation_results["errors"].append("Missing type_url")

            type_url = evidence_data.get("type_url", "")
            if type_url and not type_url.startswith("/cosmos.evidence."):
                validation_results["warnings"].append("Unusual type_url format")

            if not evidence_data.get("content") and not evidence_data.get("evidence"):
                validation_results["errors"].append("Missing evidence content")

            validation_results["valid"] = len(validation_results["errors"]) == 0

            logger.info(
                f"Evidence format validation: {'valid' if validation_results['valid'] else 'invalid'}"
            )
            return validation_results

        except Exception as e:
            logger.error(f"Validate evidence format failed: {e}")
            return {"valid": False, "errors": [str(e)], "warnings": []}
