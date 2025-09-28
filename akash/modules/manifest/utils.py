import hashlib
import json
import logging
import yaml
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from ...grpc_client import ProviderGRPCClient

logger = logging.getLogger(__name__)


class ManifestUtils:
    """
    Manifest utilities for parsing SDL and submitting to providers.

    Public Methods:
    - parse_sdl(): Parse SDL content into manifest data
    - submit_manifest(): Submit manifest to provider with automatic version detection
    - validate_manifest(): Validate manifest structure

    Private methods starting with _ are internal implementation details.
    """

    def _detect_provider_version(self, provider_endpoint: str) -> Optional[str]:
        """Detect provider version by querying /version endpoint."""
        if not hasattr(self, 'version_cache'):
            self.version_cache = {}

        if provider_endpoint in self.version_cache:
            return self.version_cache[provider_endpoint]

        try:
            import requests
            response = requests.get(
                f"{provider_endpoint}/version",
                timeout=10,
                verify=False
            )

            if response.status_code == 200:
                data = response.json()
                version = data.get('akash', {}).get('version', 'unknown')
                self.version_cache[provider_endpoint] = version
                logger.info(f"Provider {provider_endpoint} version: {version}")
                return version
        except Exception as e:
            logger.warning(f"Could not detect provider version: {e}")

        return None

    def _is_legacy_provider(self, version: str) -> bool:
        """Check if provider is running legacy version (<= v0.6.x)."""
        if not version or version == 'unknown':
            return True

        try:
            if version.startswith('v'):
                version = version[1:]

            major, minor = version.split('.')[:2]
            major, minor = int(major), int(minor)

            return major == 0 and minor <= 6
        except:
            return True

    def _clear_version_cache(self):
        """Clear the provider version cache."""
        if hasattr(self, 'version_cache'):
            self.version_cache.clear()
            logger.info("Provider version cache cleared")

    def parse_sdl(self, sdl_content: str) -> Dict[str, Any]:
        """
        Parse SDL (YAML) into a manifest dictionary following Akash SDL specification.
        """
        try:
            if not sdl_content or not sdl_content.strip():
                logger.error("SDL content cannot be empty")
                return {"status": "error", "error": "SDL content cannot be empty"}

            logger.info("Parsing SDL content")
            sdl_data = yaml.safe_load(sdl_content)

            version = sdl_data.get("version", "2.0")
            if version not in ["2.0", "2.1"]:
                return {
                    "status": "failed",
                    "error": f"Unsupported SDL version: {version}",
                }

            services = sdl_data.get("services", {})
            profiles = sdl_data.get("profiles", {})
            compute_profiles = profiles.get("compute", {})
            placement_profiles = profiles.get("placement", {})
            deployment = sdl_data.get("deployment", {})

            manifest_groups = []

            for placement_name, placement_profile in placement_profiles.items():
                group_services = []

                for service_name, deployment_config in deployment.items():
                    if service_name not in services:
                        continue

                    for depl_placement_name, placement_config in deployment_config.items():
                        if depl_placement_name != placement_name:
                            continue

                        profile_name = placement_config.get("profile")
                        if not profile_name or profile_name not in compute_profiles:
                            continue

                        service_def = services[service_name]
                        compute_profile = compute_profiles[profile_name]

                        expose_list = service_def.get("expose", [])
                        has_global_endpoints = self._has_global_endpoints(expose_list)

                        service_manifest = {
                            "name": service_name,
                            "image": service_def.get("image", "nginx:latest"),
                            "command": service_def.get("command", None),
                            "args": service_def.get("args", None),
                            "env": service_def.get("env", None),
                            "resources": self._build_resources(compute_profile, has_global_endpoints),
                            "count": placement_config.get("count", 1),
                            "expose": self._build_expose(expose_list),
                            "params": None,
                            "credentials": None
                        }

                        group_services.append(service_manifest)

                if group_services:
                    group = {
                        "Name": placement_name,
                        "Services": group_services
                    }
                    manifest_groups.append(group)

            manifest_data = manifest_groups

            logger.info(f"Successfully parsed SDL with {len(manifest_groups)} groups")
            return {"status": "success", "manifest_data": manifest_data}

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return {"status": "failed", "error": f"Invalid YAML format: {e}"}
        except Exception as e:
            logger.error(f"SDL parsing failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _build_resources(self, compute_profile: Dict, has_global_endpoints: bool = False) -> Dict:
        """Build resources section."""
        resources = {
            "id": 1,
            "cpu": {
                "units": {
                    "val": self._parse_cpu_to_string(
                        compute_profile.get("resources", {}).get("cpu", {}).get("units", "0.1"))
                }
            },
            "memory": {
                "size": {
                    "val": self._parse_memory_to_string(
                        compute_profile.get("resources", {}).get("memory", {}).get("size", "128Mi"))
                }
            },
            "storage": [
                {
                    "name": "default",
                    "size": {
                        "val": self._parse_storage_to_string(
                            self._get_storage_size(compute_profile.get("resources", {})))
                    }
                }
            ],
            "gpu": {
                "units": {
                    "val": str(compute_profile.get("resources", {}).get("gpu", {}).get("units", 0))
                }
            }
        }

        if has_global_endpoints:
            resources["endpoints"] = [{"sequence_number": 0}]

        return resources

    def _has_global_endpoints(self, expose_list: List) -> bool:
        """Check if any expose configuration requires global endpoints."""
        for expose in expose_list:
            if "to" in expose:
                for to_config in expose["to"]:
                    if isinstance(to_config, dict) and to_config.get("global"):
                        return True
        return False

    def _build_expose(self, expose_list: List) -> List:
        """Build expose section."""
        result = []

        for expose in expose_list:
            expose_entry = {
                "port": expose.get("port", 80),
                "externalPort": expose.get("as", 0),
                "proto": expose.get("proto", "tcp").upper(),
                "service": "",
                "global": False,
                "hosts": None,
                "httpOptions": {
                    "maxBodySize": 1048576,
                    "readTimeout": 60000,
                    "sendTimeout": 60000,
                    "nextTries": 3,
                    "nextTimeout": 0,
                    "nextCases": ["error", "timeout"]
                },
                "ip": "",
                "endpointSequenceNumber": 0
            }

            if "to" in expose:
                for to_config in expose["to"]:
                    if isinstance(to_config, dict) and to_config.get("global"):
                        expose_entry["global"] = True
                        break

            result.append(expose_entry)

        return result

    def _parse_cpu_to_string(self, cpu_value: Any) -> str:
        """Convert CPU value to string in millicpu units."""
        if isinstance(cpu_value, str):
            if cpu_value.endswith("m"):
                return cpu_value[:-1]
            else:
                return str(int(float(cpu_value) * 1000))
        elif isinstance(cpu_value, (int, float)):
            return str(int(cpu_value * 1000))
        return "100"  # Default

    def _parse_memory_to_string(self, memory_value: str) -> str:
        """Convert memory value to bytes string."""
        try:
            if memory_value.endswith("Gi"):
                return str(int(memory_value[:-2]) * 1024 * 1024 * 1024)
            elif memory_value.endswith("Mi"):
                return str(int(memory_value[:-2]) * 1024 * 1024)
            elif memory_value.endswith("Ki"):
                return str(int(memory_value[:-2]) * 1024)
            else:
                return str(int(memory_value))
        except:
            return str(128 * 1024 * 1024)  # Default 128Mi

    def _get_storage_size(self, resources: Dict) -> str:
        """Extract storage size from either list or dict format."""
        storage = resources.get("storage", "512Mi")
        if isinstance(storage, list) and storage:
            return storage[0].get("size", "512Mi")
        elif isinstance(storage, dict):
            return storage.get("size", "512Mi")
        else:
            return str(storage)

    def _parse_storage_to_string(self, storage_value: str) -> str:
        """Convert storage value to bytes string."""
        try:
            if storage_value.endswith("Gi"):
                return str(int(storage_value[:-2]) * 1024 * 1024 * 1024)
            elif storage_value.endswith("Mi"):
                return str(int(storage_value[:-2]) * 1024 * 1024)
            elif storage_value.endswith("Ki"):
                return str(int(storage_value[:-2]) * 1024)
            else:
                return str(int(storage_value))
        except:
            return str(512 * 1024 * 1024)  # Default 512Mi

    def _create_manifest_json(self, manifest_data: Any) -> str:
        """
        Create a deterministically sorted and properly formatted manifest JSON
        that matches the hash calculation used by the provider.
        """

        def sort_dict(obj):
            if isinstance(obj, dict):
                sorted_dict = OrderedDict()
                for key in sorted(obj.keys()):
                    sorted_dict[key] = sort_dict(obj[key])
                return sorted_dict
            elif isinstance(obj, list):
                return [sort_dict(x) for x in obj]
            else:
                return obj

        sorted_manifest = sort_dict(manifest_data)

        json_str = json.dumps(sorted_manifest, separators=(',', ':'), ensure_ascii=False)

        json_str = json_str.replace('<', '\\u003c')
        json_str = json_str.replace('>', '\\u003e')
        json_str = json_str.replace('&', '\\u0026')

        return json_str

    def _create_legacy_manifest(self, manifest_data: List[Dict]) -> List[Dict]:
        """
        Create manifest compatible with legacy providers (v0.6.x).

        Legacy providers require specific field names and structure:
        - memory/storage use "size" instead of "quantity"
        - resources need specific required fields (gpu, endpoints)
        - expose structure is simplified
        """
        if not manifest_data:
            raise ValueError("manifest_data is required - cannot create legacy manifest from empty data")

        logger.info("Creating legacy manifest from input data")
        legacy_manifest = []

        for group in manifest_data:
            group_name = group.get("name", group.get("Name", "default"))
            services = group.get("services", group.get("Services", []))

            legacy_group = {
                "name": group_name,
                "services": []
            }

            for service in services:
                service_name = service.get("name")
                if not service_name:
                    raise ValueError(f"Service name is required in group '{group_name}'")

                image = service.get("image")
                if not image:
                    raise ValueError(f"Service image is required for service '{service_name}'")

                count = service.get("count", 1)

                resources = service.get("resources", {})
                legacy_resources = {
                    "id": resources.get("id", 1),
                    "cpu": {
                        "units": {"val": str(resources.get("cpu", {}).get("units", {}).get("val", "100"))}
                    },
                    "memory": {
                        "size": {"val": str(resources.get("memory", {}).get("size", {}).get("val", "134217728"))}
                    },
                    "gpu": {
                        "units": {"val": str(resources.get("gpu", {}).get("units", {}).get("val", "0"))}
                    },
                    "storage": []
                }

                storage_list = resources.get("storage", [])
                if storage_list:
                    for storage in storage_list:
                        legacy_resources["storage"].append({
                            "name": storage.get("name", "default"),
                            "size": {"val": str(storage.get("size", {}).get("val", "536870912"))}
                        })
                else:
                    legacy_resources["storage"] = [{"name": "default", "size": {"val": "536870912"}}]

                expose_list = service.get("expose", [])
                has_global = any(exp.get("global", False) for exp in expose_list)
                if has_global:
                    legacy_resources["endpoints"] = [{"sequence_number": 0}]

                legacy_expose = []
                for expose in expose_list:
                    legacy_exp = {
                        "port": expose.get("port", 80),
                        "externalPort": expose.get("externalPort", expose.get("port", 80)),
                        "proto": expose.get("proto", "TCP"),
                        "global": expose.get("global", False),
                        "hosts": expose.get("hosts"),
                        "service": expose.get("service", ""),
                        "ip": expose.get("ip", "")
                    }

                    if expose.get("global"):
                        legacy_exp["endpointSequenceNumber"] = expose.get("endpointSequenceNumber", 0)

                        if expose.get("port") in [80, 443, 8080]:
                            legacy_exp["httpOptions"] = expose.get("httpOptions", {
                                "maxBodySize": 1048576,
                                "nextCases": ["error", "timeout"],
                                "nextTimeout": 0,
                                "nextTries": 3,
                                "readTimeout": 60000,
                                "sendTimeout": 60000
                            })

                    legacy_expose.append(legacy_exp)

                legacy_service = {
                    "name": service_name,
                    "image": image,
                    "count": count,
                    "args": service.get("args"),
                    "command": service.get("command"),
                    "env": service.get("env"),
                    "credentials": service.get("credentials"),
                    "params": service.get("params"),
                    "resources": legacy_resources,
                    "expose": legacy_expose
                }

                legacy_group["services"].append(legacy_service)

            legacy_manifest.append(legacy_group)

        return legacy_manifest

    def _submit_legacy_with_fallback(
            self,
            provider_endpoint: str,
            lease_id: Dict[str, Any],
            sdl_content: str,
            cert_pem: str,
            key_pem: str,
            provider_version: str = "unknown"
    ) -> Dict[str, Any]:
        """Submit to legacy provider using the EXACT working format."""
        logger.info("Submitting to legacy provider with EXACT working format")

        try:
            parse_result = self.parse_sdl(sdl_content)
            if parse_result.get('status') != 'success':
                return {
                    "status": "error",
                    "error": f"SDL parsing failed: {parse_result.get('error')}",
                    "provider_version": provider_version
                }

            parsed_manifest_data = parse_result.get('manifest_data', [])

            manifest_data = self._create_legacy_manifest(parsed_manifest_data)

            logger.info("Using legacy manifest format for legacy provider")

            result = self._send_manifest_http(
                provider_endpoint, lease_id, manifest_data, cert_pem, key_pem, adaptive=False
            )

            if result.get("status") == "success":
                logger.info("✅ Legacy provider manifest submission successful")
                result["legacy_format"] = True
                result["method"] = "HTTP"
                result["provider_version"] = provider_version
                return result
            else:
                error = result.get("error", "Unknown error")
                logger.warning(f"❌ EXACT working format failed: {error}")
                return {
                    "status": "error",
                    "error": f"Even exact working format failed: {error}",
                    "provider_version": provider_version
                }

        except Exception as e:
            logger.error(f"❌ Exception with exact working format: {e}")
            return {
                "status": "error",
                "error": f"Exception with exact working format: {str(e)}",
                "provider_version": provider_version
            }

    def _calculate_manifest_version(self, manifest_json: str) -> bytes:
        """
        Calculate the manifest version hash the provider expects.
        """
        hash_obj = hashlib.sha256(manifest_json.encode('utf-8'))
        return hash_obj.digest()


    def _sort_json_deterministic(self, json_str: str) -> str:
        """Sort JSON with deterministic ordering and HTML escaping."""
        import html

        parsed = json.loads(json_str)
        stable_json = self._stringify_sorted(parsed)

        escaped = html.escape(stable_json, quote=False)
        return escaped.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    def _stringify_sorted(self, data):
        """JSON stringify with deterministic key ordering."""

        def sort_keys(obj):
            if isinstance(obj, dict):
                return {k: sort_keys(v) for k, v in sorted(obj.items())}
            elif isinstance(obj, list):
                return [sort_keys(item) for item in obj]
            else:
                return obj

        return json.dumps(sort_keys(data), separators=(',', ':'), ensure_ascii=False)

    def submit_manifest(
            self,
            provider_endpoint: str,
            lease_id: Dict[str, Any],
            sdl_content: str,
            cert_pem: str,
            key_pem: str,
            timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Submit manifest to provider (automatically detects provider version).

        This is the main method for manifest submission - it automatically detects
        the provider version and adapts the manifest format accordingly.

        Args:
            provider_endpoint: Provider endpoint URL
            lease_id: Lease identifier dictionary
            sdl_content: SDL YAML content as string
            cert_pem: Client certificate in PEM format
            key_pem: Client private key in PEM format
            timeout: Request timeout in seconds

        Returns:
            Dict with submission result including status, provider_version, method used
        """
        logger.info(f"Starting adaptive manifest submission to {provider_endpoint}")

        provider_version = self._detect_provider_version(provider_endpoint)
        if not provider_version:
            logger.warning("Could not detect provider version, proceeding with legacy fallback")
            provider_version = "unknown"

        if self._is_legacy_provider(provider_version):
            logger.info(f"Legacy provider detected (v{provider_version}) - using exact working format")
            return self._submit_legacy_with_fallback(
                provider_endpoint, lease_id, sdl_content, cert_pem, key_pem, provider_version
            )
        else:
            logger.info(f"Modern provider detected (v{provider_version}) - using standard approach")
            result = self.parse_sdl(sdl_content)
            if result.get('status') != 'success':
                return {
                    "status": "error",
                    "error": f"SDL parsing failed: {result.get('error')}",
                    "provider_version": provider_version
                }

            manifest_data = result.get('manifest_data')
            return self._send_manifest_http(
                provider_endpoint, lease_id, manifest_data, cert_pem, key_pem, timeout
            )

    def _send_manifest_http(
            self,
            provider_endpoint: str,
            lease_id: Dict[str, Any],
            manifest_data: Any,
            cert_pem: str = None,
            key_pem: str = None,
            timeout: int = 60,
            adaptive: bool = True,
    ) -> Dict[str, Any]:
        """
        Send manifest to provider via HTTP PUT with adaptive provider support.
        """
        try:
            import requests
            import tempfile
            import os

            logger.info(f"Sending manifest via HTTP to {provider_endpoint}")

            provider_version = "unknown"
            if adaptive:
                provider_version = self._detect_provider_version(provider_endpoint)
                logger.info(f"Detected provider version: {provider_version}")

                if self._is_legacy_provider(provider_version):
                    logger.info("Legacy provider - will convert quantity to size fields")

            manifest_json = self._create_manifest_json(manifest_data)

            if adaptive and provider_version and self._is_legacy_provider(provider_version):
                manifest_json = manifest_json.replace('"quantity":', '"size":')
                logger.info("Converted quantity fields to size fields for legacy provider")

            manifest_hash = self._calculate_manifest_version(manifest_json)
            logger.info(f"Manifest hash: {manifest_hash.hex()}")
            logger.info(f"Manifest JSON (first 500 chars): {manifest_json[:500]}")

            dseq = lease_id.get("dseq")
            url = f"{provider_endpoint.rstrip('/')}/deployment/{dseq}/manifest"

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Content-Length": str(len(manifest_json))
            }

            kwargs = {
                "url": url,
                "data": manifest_json,
                "headers": headers,
                "timeout": timeout,
            }

            if cert_pem and key_pem:
                cert_file = tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False)
                key_file = tempfile.NamedTemporaryFile(mode="w", suffix=".key", delete=False)

                try:
                    cert_file.write(cert_pem)
                    cert_file.flush()
                    key_file.write(key_pem)
                    key_file.flush()

                    kwargs["cert"] = (cert_file.name, key_file.name)
                    kwargs["verify"] = False

                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                    response = requests.put(**kwargs)

                finally:
                    cert_file.close()
                    key_file.close()
                    os.unlink(cert_file.name)
                    os.unlink(key_file.name)
            else:
                response = requests.put(**kwargs)

            if response.status_code in [200, 201, 202, 204]:
                logger.info(f"Manifest submission successful: {response.status_code}")
                return {
                    "status": "success",
                    "provider": provider_endpoint,
                    "lease_id": lease_id,
                    "method": "HTTP",
                    "status_code": response.status_code,
                    "provider_version": provider_version if adaptive else "unknown",
                }
            else:
                error_msg = response.text[:500] if response.text else f"HTTP {response.status_code}"
                logger.error(f"Manifest submission failed: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "provider": provider_endpoint,
                    "method": "HTTP",
                    "status_code": response.status_code,
                    "provider_version": provider_version if adaptive else "unknown",
                }

        except Exception as e:
            logger.error(f"Failed to send manifest via HTTP: {e}")
            return {
                "status": "error",
                "error": str(e),
                "provider": provider_endpoint,
                "method": "HTTP",
            }


    def validate_manifest(self, manifest_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic manifest validation."""
        try:
            if not manifest_data:
                return {"valid": False, "error": "Empty manifest data"}

            if not isinstance(manifest_data, list):
                return {"valid": False, "error": "Manifest must be a list of groups"}

            for i, group in enumerate(manifest_data):
                if not isinstance(group, dict):
                    return {"valid": False, "error": f"Group {i} must be a dictionary"}

                if "Name" not in group:
                    return {"valid": False, "error": f"Group {i} missing 'Name' field"}

                if "Services" not in group:
                    return {"valid": False, "error": f"Group {i} missing 'Services' field"}

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _validate_provider_dns(self, endpoint: str) -> bool:
        """Basic DNS validation for provider endpoints."""
        try:
            import socket
            if endpoint.startswith('http://') or endpoint.startswith('https://'):
                from urllib.parse import urlparse
                parsed = urlparse(endpoint)
                hostname = parsed.hostname
            else:
                hostname = endpoint.split(':')[0]

            socket.gethostbyname(hostname)
            return True
        except:
            return False
