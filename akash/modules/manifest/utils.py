import hashlib
import json
import logging
import yaml
from collections import OrderedDict
from typing import Any, Dict, List, Optional

try:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

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
            endpoints = sdl_data.get("endpoints", {})

            dependency_validation = self._validate_dependencies(services)
            if not dependency_validation["valid"]:
                return {
                    "status": "failed",
                    "error": f"Dependency validation failed: {dependency_validation['error']}"
                }

            endpoint_validation = self._validate_endpoints(endpoints)
            if not endpoint_validation["valid"]:
                return {
                    "status": "failed",
                    "error": f"Endpoint validation failed: {endpoint_validation['error']}"
                }

            endpoint_usage_validation = self._validate_endpoint_usage(services, endpoints)
            if not endpoint_usage_validation["valid"]:
                return {
                    "status": "failed",
                    "error": f"Endpoint usage validation failed: {endpoint_usage_validation['error']}"
                }

            endpoint_sequence_numbers = self._compute_endpoint_sequence_numbers(services, endpoints)

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

                        if not service_def.get("image"):
                            return {"valid": False, "error": f"Service '{service_name}' missing required field 'image'"}

                        if placement_config.get("count") is None:
                            return {"valid": False, "error": f"Service '{service_name}' missing required field 'count'"}

                        expose_list = service_def.get("expose", [])
                        has_global_endpoints = self._has_global_endpoints(expose_list)

                        resources = self._build_resources(compute_profile, has_global_endpoints, service_def,
                                                          endpoint_sequence_numbers)
                        storage_names = [s["name"] for s in resources["storage"]]

                        credentials = self._build_credentials(service_def.get("credentials"), service_name)

                        service_manifest = {
                            "name": service_name,
                            "image": service_def.get("image"),
                            "command": service_def.get("command", None),
                            "args": service_def.get("args", None),
                            "env": service_def.get("env", None),
                            "resources": resources,
                            "count": placement_config.get("count"),
                            "expose": self._build_expose(expose_list, endpoint_sequence_numbers),
                            "params": self._build_service_params(service_def, storage_names),
                            "credentials": credentials
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

    def _build_resources(self, compute_profile: Dict, has_global_endpoints: bool = False, service_def: Dict = None,
                         endpoint_sequence_numbers: Dict = None) -> Dict:
        """Build resources section."""

        cpu_units = compute_profile.get("resources", {}).get("cpu", {}).get("units")
        if cpu_units is None:
            raise ValueError("CPU units are required in compute profile")

        memory_size = compute_profile.get("resources", {}).get("memory", {}).get("size")
        if memory_size is None:
            raise ValueError("Memory size is required in compute profile")

        resources = {
            "id": 1,
            "cpu": {
                "units": {
                    "val": self._parse_cpu_to_string(cpu_units)
                }
            },
            "memory": {
                "size": {
                    "val": self._parse_memory_to_string(memory_size)
                }
            },
            "storage": self._build_storage(compute_profile.get("resources", {}).get("storage")),
            "gpu": self._build_gpu(compute_profile.get("resources", {}).get("gpu", {}))
        }

        if service_def:
            endpoints = self._build_service_endpoints(service_def, endpoint_sequence_numbers or {})
            resources["endpoints"] = endpoints if endpoints else []
        elif has_global_endpoints:
            resources["endpoints"] = [{"sequence_number": 0}]
        else:
            resources["endpoints"] = []

        return resources

    def _has_global_endpoints(self, expose_list: List) -> bool:
        """Check if any expose configuration requires global endpoints."""
        for expose in expose_list:
            if "to" in expose:
                for to_config in expose["to"]:
                    if isinstance(to_config, dict) and to_config.get("global"):
                        return True
        return False

    def _build_expose(self, expose_list: List, endpoint_sequence_numbers: Dict = None) -> List:
        """Build expose section."""
        result = []
        if endpoint_sequence_numbers is None:
            endpoint_sequence_numbers = {}

        for expose in expose_list:
            port = expose.get("port")
            if port is None:
                raise ValueError("Port is required in expose configuration")

            http_options_defaults = {
                "maxBodySize": 1048576,
                "readTimeout": 60000,
                "sendTimeout": 60000,
                "nextTries": 3,
                "nextTimeout": 0,
                "nextCases": ["error", "timeout"]
            }

            custom_http_options = expose.get("http_options", {})
            http_options = {
                "maxBodySize": custom_http_options.get("max_body_size", http_options_defaults["maxBodySize"]),
                "readTimeout": custom_http_options.get("read_timeout", http_options_defaults["readTimeout"]),
                "sendTimeout": custom_http_options.get("send_timeout", http_options_defaults["sendTimeout"]),
                "nextTries": custom_http_options.get("next_tries", http_options_defaults["nextTries"]),
                "nextTimeout": custom_http_options.get("next_timeout", http_options_defaults["nextTimeout"]),
                "nextCases": custom_http_options.get("next_cases", http_options_defaults["nextCases"])
            }

            hosts = expose.get("accept") or None

            to_list = expose.get("to", [])
            if not to_list:
                continue

            for to_config in to_list:
                if not isinstance(to_config, dict):
                    continue

                expose_entry = {
                    "port": port,
                    "externalPort": expose.get("as") or 0,
                    "proto": expose.get("proto", "tcp").upper(),
                    "service": to_config.get("service", ""),
                    "global": to_config.get("global", False),
                    "hosts": hosts,
                    "httpOptions": http_options,
                    "ip": to_config.get("ip", ""),
                    "endpointSequenceNumber": endpoint_sequence_numbers.get(to_config.get("ip", ""), 0)
                }

                result.append(expose_entry)

        result.sort(key=lambda e: (
            e["service"],
            e["port"],
            e["proto"],
            not e["global"]
        ))

        return result

    def _build_dependencies(self, depends_on_list: List) -> List[Dict]:
        """Build dependencies section from depends_on list."""
        if not depends_on_list:
            return []

        dependencies = []
        for dep in depends_on_list:
            if isinstance(dep, str):
                dependencies.append({"service": dep})
            elif isinstance(dep, dict) and "service" in dep:
                dependencies.append(dep)
            else:
                logger.warning(f"Invalid dependency format: {dep}")

        return dependencies

    def _build_service_params(self, service_def: Dict, storage_names: List[str]) -> Optional[Dict]:
        """Build service parameters including storage mounts with validation."""
        params = service_def.get("params", {})
        if not params:
            return None

        result = {}

        storage_params = params.get("storage", {})
        if storage_params:
            storage_list = []
            for name, config in storage_params.items():
                if name not in storage_names:
                    raise ValueError(
                        f"Storage '{name}' referenced in service params but not defined in compute profile")

                storage_entry = {
                    "name": name,
                    "mount": config.get("mount", ""),
                    "readOnly": config.get("readOnly", False)
                }
                storage_list.append(storage_entry)

            if storage_list:
                result["storage"] = storage_list

        return result if result else None

    def _build_storage(self, storage_config) -> List[Dict]:
        """Build storage array supporting multiple named volumes with attributes."""
        if isinstance(storage_config, list):
            storage_list = []
            for storage_item in storage_config:
                if isinstance(storage_item, dict):
                    storage_list.append(self._build_single_storage(storage_item))
                else:
                    storage_list.append({
                        "name": "default",
                        "size": {"val": self._parse_storage_to_string(str(storage_item))}
                    })
            return storage_list
        elif isinstance(storage_config, dict):
            return [self._build_single_storage(storage_config)]
        else:
            return [{
                "name": "default",
                "size": {"val": self._parse_storage_to_string(str(storage_config))}
            }]

    def _build_single_storage(self, storage: Dict) -> Dict:
        """Build single storage volume with attributes and validation."""
        storage_name = storage.get("name", "default")
        result = {
            "name": storage_name,
            "size": {"val": self._parse_storage_to_string(storage.get("size"))}
        }

        attributes = storage.get("attributes", {})
        if attributes:
            validation = self._validate_storage_attributes(storage_name, attributes)
            if not validation["valid"]:
                raise ValueError(f"Storage '{storage_name}' validation failed: {validation['error']}")

            result["attributes"] = self._build_storage_attributes(attributes)

        return result

    def _build_storage_attributes(self, attributes: Dict) -> List[Dict]:
        """Build storage attributes with validation."""
        if not attributes:
            return []

        pairs = []
        for key, value in attributes.items():
            if isinstance(value, bool):
                pairs.append({"key": key, "value": str(value).lower()})
            else:
                pairs.append({"key": key, "value": str(value)})

        if attributes.get("class") == "ram" and "persistent" not in attributes:
            pairs.append({"key": "persistent", "value": "false"})

        pairs.sort(key=lambda x: x["key"])
        return pairs

    def _validate_storage_attributes(self, storage_name: str, attributes: Dict) -> Dict[str, Any]:
        """Validate storage attributes according to akash rules."""
        try:
            storage_class = attributes.get("class")
            persistent = attributes.get("persistent")

            if storage_class and storage_class not in ["beta1", "beta2", "beta3", "ram"]:
                return {
                    "valid": False,
                    "error": f"Storage '{storage_name}' has invalid class '{storage_class}'. Must be one of: beta1, beta2, beta3, ram"
                }

            if isinstance(persistent, str):
                if persistent.lower() in ["true", "false"]:
                    persistent = persistent.lower() == "true"
                else:
                    return {
                        "valid": False,
                        "error": f"Storage '{storage_name}' has invalid persistent value '{persistent}'. Must be true or false"
                    }

            if storage_class == "ram" and persistent is True:
                return {
                    "valid": False,
                    "error": f"Storage '{storage_name}' with class 'ram' cannot have 'persistent' set to true"
                }

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"Storage '{storage_name}' attribute validation error: {str(e)}"}

    def _build_gpu(self, gpu_config: Dict) -> Dict:
        """Build GPU configuration with vendor/model/RAM/interface support."""
        if not gpu_config:
            return {"units": {"val": "0"}}

        units = gpu_config.get("units", 0)
        units_str = str(units)

        result = {
            "units": {"val": units_str}
        }

        validation = self._validate_gpu_config(gpu_config)
        if not validation["valid"]:
            raise ValueError(f"GPU validation failed: {validation['error']}")

        attributes = gpu_config.get("attributes", {})
        if attributes and int(units) > 0:
            result["attributes"] = self._build_gpu_attributes(attributes)

        return result

    def _build_gpu_attributes(self, attributes: Dict) -> List[Dict]:
        """Transform GPU attributes to key-value pairs."""
        if not attributes:
            return []

        pairs = []
        vendor_specs = attributes.get("vendor", {})

        for vendor, models in vendor_specs.items():
            if not models:
                pairs.append({
                    "key": f"vendor/{vendor}/model/*",
                    "value": "true"
                })
            else:
                for model_spec in models:
                    if isinstance(model_spec, str):
                        pairs.append({
                            "key": f"vendor/{vendor}/model/{model_spec}",
                            "value": "true"
                        })
                    elif isinstance(model_spec, dict):
                        model_name = model_spec.get("model", "*")
                        key = f"vendor/{vendor}/model/{model_name}"

                        if "ram" in model_spec:
                            key += f"/ram/{model_spec['ram']}"

                        if "interface" in model_spec:
                            key += f"/interface/{model_spec['interface']}"

                        pairs.append({
                            "key": key,
                            "value": "true"
                        })

        pairs.sort(key=lambda x: x["key"])
        return pairs

    def _validate_gpu_config(self, gpu_config: Dict) -> Dict[str, Any]:
        """Validate GPU configuration according to akash rules."""
        try:
            GPU_SUPPORTED_VENDORS = ["nvidia", "amd"]
            GPU_SUPPORTED_INTERFACES = ["pcie", "sxm"]

            units = gpu_config.get("units", 0)
            units_int = int(units) if units is not None else 0
            attributes = gpu_config.get("attributes", {})

            if units_int < 0:
                return {"valid": False, "error": "GPU units cannot be negative"}

            if units_int == 0 and attributes:
                return {"valid": False, "error": "GPU must not have attributes if units is 0"}

            if units_int > 0 and not attributes:
                return {"valid": False, "error": "GPU must have attributes if units is not 0"}

            if units_int > 0:
                vendor_specs = attributes.get("vendor", {})
                if not vendor_specs:
                    return {"valid": False, "error": "GPU must specify a vendor if units is not 0"}

                for vendor in vendor_specs.keys():
                    if vendor not in GPU_SUPPORTED_VENDORS:
                        return {
                            "valid": False,
                            "error": f"Unsupported GPU vendor '{vendor}'. Must be one of: {', '.join(GPU_SUPPORTED_VENDORS)}"
                        }

                for vendor, models in vendor_specs.items():
                    if models:
                        for model_spec in models:
                            if isinstance(model_spec, dict):
                                interface = model_spec.get("interface")
                                if interface and interface not in GPU_SUPPORTED_INTERFACES:
                                    return {
                                        "valid": False,
                                        "error": f"Unsupported GPU interface '{interface}'. Must be one of: {', '.join(GPU_SUPPORTED_INTERFACES)}"
                                    }

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"GPU validation error: {str(e)}"}

    def _validate_endpoints(self, endpoints: Dict) -> Dict[str, Any]:
        """Validate endpoints section."""
        try:
            import re
            ENDPOINT_NAME_VALIDATION_REGEX = re.compile(r'^[a-z]([a-z0-9\-]*[a-z0-9])?$')

            for endpoint_name, endpoint_config in endpoints.items():
                if not ENDPOINT_NAME_VALIDATION_REGEX.match(endpoint_name):
                    return {
                        "valid": False,
                        "error": f"Endpoint named '{endpoint_name}' is not a valid name"
                    }

                if not endpoint_config or "kind" not in endpoint_config:
                    return {
                        "valid": False,
                        "error": f"Endpoint named '{endpoint_name}' has no kind"
                    }

                if endpoint_config["kind"] != "ip":
                    return {
                        "valid": False,
                        "error": f"Endpoint named '{endpoint_name}' has an unknown kind '{endpoint_config['kind']}'"
                    }

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"Endpoint validation error: {str(e)}"}

    def _validate_endpoint_usage(self, services: Dict, endpoints: Dict) -> Dict[str, Any]:
        """Validate that all declared endpoints are used and all used endpoints are declared."""
        try:
            declared_endpoints = set(endpoints.keys())
            used_endpoints = set()

            for service_name, service_def in services.items():
                expose_list = service_def.get("expose", [])
                for expose in expose_list:
                    to_list = expose.get("to", [])
                    for to_config in to_list:
                        if isinstance(to_config, dict) and "ip" in to_config:
                            ip_name = to_config["ip"]
                            if ip_name not in declared_endpoints:
                                return {
                                    "valid": False,
                                    "error": f"Unknown endpoint '{ip_name}' in service '{service_name}'. Add to the list of endpoints in the 'endpoints' section"
                                }
                            used_endpoints.add(ip_name)

            unused_endpoints = declared_endpoints - used_endpoints
            if unused_endpoints:
                unused = next(iter(unused_endpoints))
                return {
                    "valid": False,
                    "error": f"Endpoint {unused} declared but never used"
                }

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"Endpoint usage validation error: {str(e)}"}

    def _compute_endpoint_sequence_numbers(self, services: Dict, endpoints: Dict) -> Dict[str, int]:
        """
        Compute endpoint sequence numbers for IP endpoints.
        """
        ip_names = set()

        for service_name, service_def in services.items():
            expose_list = service_def.get("expose", [])
            for expose in expose_list:
                to_configs = expose.get("to", [])
                for to_config in to_configs:
                    if isinstance(to_config, dict) and to_config.get("global") and to_config.get("ip"):
                        ip_names.add(to_config["ip"])

        sorted_ips = sorted(ip_names)
        return {ip_name: idx + 1 for idx, ip_name in enumerate(sorted_ips)}

    def _build_service_endpoints(self, service_def: Dict, endpoint_sequence_numbers: Dict) -> List[Dict]:
        """
        Build service endpoints for resources section.
        """
        endpoints = []
        expose_list = service_def.get("expose", [])

        for expose in expose_list:
            port = expose.get("port", 0)
            external_port = expose.get("as", 0)
            proto = expose.get("proto", "tcp").upper()
            actual_external_port = external_port if external_port != 0 else port

            to_list = expose.get("to", [])
            for to_config in to_list:
                if not isinstance(to_config, dict):
                    continue

                if to_config.get("global"):
                    is_ingress = proto == "TCP" and actual_external_port == 80

                    if is_ingress:
                        endpoints.append({"sequence_number": 0})
                    else:
                        endpoints.append({"kind": 1, "sequence_number": 0})

                    if "ip" in to_config:
                        ip_name = to_config["ip"]
                        sequence_number = endpoint_sequence_numbers.get(ip_name, 0)
                        endpoints.append({"kind": 2, "sequence_number": sequence_number})

        seen = set()
        unique_endpoints = []
        for endpoint in endpoints:
            key = tuple(sorted(endpoint.items()))
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(endpoint)

        return unique_endpoints

    def _build_credentials(self, credentials_config: Dict, service_name: str) -> Optional[Dict]:
        """Build and validate service image credentials."""
        if not credentials_config:
            return None

        required_fields = ["host", "username", "password"]
        for field in required_fields:
            if not credentials_config.get(field, "").strip():
                raise ValueError(f"Service '{service_name}' credentials missing '{field}'")

        result = {
            "host": credentials_config["host"],
            "username": credentials_config["username"],
            "password": credentials_config["password"],
            "email": credentials_config.get("email", "")
        }

        return result

    def _validate_dependencies(self, services: Dict) -> Dict[str, Any]:
        """Validate that all service dependencies reference existing services."""
        try:
            service_names = set(services.keys())

            for service_name, service_def in services.items():
                depends_on = service_def.get("depends_on", [])
                if not depends_on:
                    continue

                for dep in depends_on:
                    dep_service = dep if isinstance(dep, str) else dep.get("service")
                    if not dep_service:
                        return {
                            "valid": False,
                            "error": f"Service '{service_name}' has invalid dependency format: {dep}"
                        }

                    if dep_service not in service_names:
                        return {
                            "valid": False,
                            "error": f"Service '{service_name}' depends on non-existent service '{dep_service}'"
                        }

                    if dep_service == service_name:
                        return {
                            "valid": False,
                            "error": f"Service '{service_name}' cannot depend on itself"
                        }

            circular_check = self._check_circular_dependencies(services)
            if not circular_check["valid"]:
                return circular_check

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"Dependency validation error: {str(e)}"}

    def _check_circular_dependencies(self, services: Dict) -> Dict[str, Any]:
        """Check for circular dependencies using DFS."""
        try:
            graph = {}
            for service_name, service_def in services.items():
                depends_on = service_def.get("depends_on", [])
                deps = []
                for dep in depends_on:
                    dep_service = dep if isinstance(dep, str) else dep.get("service")
                    if dep_service:
                        deps.append(dep_service)
                graph[service_name] = deps

            WHITE, GRAY, BLACK = 0, 1, 2
            colors = {service: WHITE for service in services.keys()}

            def dfs(node, path):
                if colors[node] == GRAY:
                    cycle_start = path.index(node)
                    cycle = " -> ".join(path[cycle_start:] + [node])
                    return {"valid": False, "error": f"Circular dependency detected: {cycle}"}

                if colors[node] == BLACK:
                    return {"valid": True}

                colors[node] = GRAY
                path.append(node)

                for neighbor in graph.get(node, []):
                    result = dfs(neighbor, path[:])
                    if not result["valid"]:
                        return result

                colors[node] = BLACK
                return {"valid": True}

            for service in services.keys():
                if colors[service] == WHITE:
                    result = dfs(service, [])
                    if not result["valid"]:
                        return result

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"Circular dependency check error: {str(e)}"}

    def _parse_cpu_to_string(self, cpu_value: Any) -> str:
        """Convert CPU value to string in millicpu units."""
        if isinstance(cpu_value, str):
            if cpu_value.endswith("m"):
                return cpu_value[:-1]
            else:
                return str(int(float(cpu_value) * 1000))
        elif isinstance(cpu_value, (int, float)):
            return str(int(cpu_value * 1000))
        raise ValueError(f"Invalid CPU value: {cpu_value}. Expected string with 'm' suffix or numeric value.")

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
            raise ValueError(f"Invalid memory value: {memory_value}. Expected format like '128Mi', '2Gi', '512Ki'.")

    def _get_storage_size(self, resources: Dict) -> str:
        """Extract storage size from either list or dict format."""
        storage = resources.get("storage")
        if not storage:
            raise ValueError("Storage configuration is required")
        if isinstance(storage, list) and storage:
            size = storage[0].get("size")
            if not size:
                raise ValueError("Storage size is required")
            return size
        elif isinstance(storage, dict):
            size = storage.get("size")
            if not size:
                raise ValueError("Storage size is required")
            return size
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
            raise ValueError(f"Invalid storage value: {storage_value}. Expected format like '512Mi', '2Gi', '1Ti'.")

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

    def _escape_html(self, text: str) -> str:
        return text.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

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
                        "units": {"val": str(resources.get("gpu", {}).get("units", {}).get("val", "0"))},
                        **({"attributes": resources.get("gpu", {}).get("attributes", [])} if resources.get("gpu",
                                                                                                           {}).get(
                            "attributes") else {})
                    },
                    "storage": []
                }

                storage_list = resources.get("storage", [])
                if storage_list:
                    for storage in storage_list:
                        legacy_storage = {
                            "name": storage.get("name", "default"),
                            "size": {"val": str(storage.get("size", {}).get("val", "536870912"))}
                        }
                        if "attributes" in storage:
                            legacy_storage["attributes"] = storage["attributes"]
                        legacy_resources["storage"].append(legacy_storage)
                else:
                    legacy_resources["storage"] = [{"name": "default", "size": {"val": "536870912"}}]

                expose_list = service.get("expose", [])
                has_global = any(exp.get("global", False) for exp in expose_list)
                if has_global:
                    legacy_resources["endpoints"] = [{"sequence_number": 0}]
                else:
                    legacy_resources["endpoints"] = []

                legacy_expose = []
                for expose in expose_list:
                    legacy_exp = {
                        "port": expose.get("port", 80),
                        "externalPort": expose.get("externalPort", expose.get("port", 80)),
                        "proto": expose.get("proto", "TCP"),
                        "global": expose.get("global", False),
                        "hosts": expose.get("hosts"),
                        "httpOptions": expose.get("httpOptions", {
                            "maxBodySize": 1048576,
                            "nextCases": ["error", "timeout"],
                            "nextTimeout": 0,
                            "nextTries": 3,
                            "readTimeout": 60000,
                            "sendTimeout": 60000
                        }),
                        "service": expose.get("service", ""),
                        "ip": expose.get("ip", ""),
                        "endpointSequenceNumber": expose.get("endpointSequenceNumber", 0)
                    }

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
        """Submit to legacy provider."""
        logger.info("Submitting to legacy provider")

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
                logger.warning(f"❌ Legacy provider manifest submission failed: {error}")
                return {
                    "status": "error",
                    "error": f"Legacy provider manifest submission failed: {error}",
                    "provider_version": provider_version
                }

        except Exception as e:
            logger.error(f"❌ Exception with legacy provider manifest submission: {e}")
            return {
                "status": "error",
                "error": f"Exception with legacy provider manifest submission: {str(e)}",
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
            logger.info(f"Legacy provider detected (v{provider_version})")
            return self._submit_legacy_with_fallback(
                provider_endpoint, lease_id, sdl_content, cert_pem, key_pem, provider_version
            )
        else:
            logger.info(f"Modern provider detected (v{provider_version}) - using legacy format for version hash compatibility")
            result = self.parse_sdl(sdl_content)
            if result.get('status') != 'success':
                return {
                    "status": "error",
                    "error": f"SDL parsing failed: {result.get('error')}",
                    "provider_version": provider_version
                }

            parsed_manifest_data = result.get('manifest_data', [])
            manifest_data = self._create_legacy_manifest(parsed_manifest_data)

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

        For modern providers (v0.7+), uses the mtls. prefix convention to signal
        mTLS authentication intent via SNI.
        """
        try:
            import requests
            import tempfile
            import os
            import ssl
            import socket
            from urllib.parse import urlparse

            logger.info(f"Sending manifest via HTTP to {provider_endpoint}")

            provider_version = "unknown"
            is_modern_provider = False

            if adaptive:
                provider_version = self._detect_provider_version(provider_endpoint)
                logger.info(f"Detected provider version: {provider_version}")

                if self._is_legacy_provider(provider_version):
                    logger.info("Legacy provider - will convert quantity to size fields")
                else:
                    is_modern_provider = True
                    logger.info("Modern provider - will use mtls. prefix for authentication")

            manifest_json = self._create_manifest_json(manifest_data)
            manifest_hash = self._calculate_manifest_version(manifest_json)
            logger.info(f"Manifest hash: {manifest_hash.hex()}")
            logger.info(f"Manifest JSON (first 500 chars): {manifest_json[:500]}")

            dseq = lease_id.get("dseq")
            path = f"/deployment/{dseq}/manifest"

            parsed_uri = urlparse(provider_endpoint)
            hostname = parsed_uri.hostname
            port = parsed_uri.port or 8443

            use_socket_approach = False
            socket_cert_file = None
            socket_key_file = None

            if cert_pem and key_pem and is_modern_provider:
                logger.info(f"Attempting socket-based approach with mtls. prefix: mtls.{hostname}")

                socket_cert_file = tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False)
                socket_key_file = tempfile.NamedTemporaryFile(mode="w", suffix=".key", delete=False)

                try:
                    socket_cert_file.write(cert_pem)
                    socket_cert_file.flush()
                    socket_key_file.write(key_pem)
                    socket_key_file.flush()

                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                    try:
                        ctx.load_cert_chain(socket_cert_file.name, socket_key_file.name)
                        use_socket_approach = True
                    except ssl.SSLError as ssl_err:
                        logger.debug(f"Failed to load certificate chain: {ssl_err}, falling back to requests library")
                        socket_cert_file.close()
                        socket_key_file.close()
                        os.unlink(socket_cert_file.name)
                        os.unlink(socket_key_file.name)
                        socket_cert_file = None
                        socket_key_file = None
                        use_socket_approach = False
                except Exception as e:
                    logger.debug(f"Failed to prepare socket approach: {e}, falling back to requests library")
                    if socket_cert_file:
                        socket_cert_file.close()
                        os.unlink(socket_cert_file.name)
                    if socket_key_file:
                        socket_key_file.close()
                        os.unlink(socket_key_file.name)
                    socket_cert_file = None
                    socket_key_file = None
                    use_socket_approach = False

            if use_socket_approach:
                try:
                    sock = socket.create_connection((hostname, port), timeout=timeout)
                    ssl_sock = ctx.wrap_socket(sock, server_hostname=f"mtls.{hostname}")

                    request_str = (
                        f"PUT {path} HTTP/1.1\r\n"
                        f"Host: {hostname}\r\n"
                        f"Content-Type: application/json\r\n"
                        f"Accept: application/json\r\n"
                        f"Content-Length: {len(manifest_json)}\r\n"
                        f"\r\n"
                        f"{manifest_json}"
                    )
                    ssl_sock.sendall(request_str.encode())

                    ssl_sock.settimeout(timeout)
                    response_data = b""
                    socket_error = None
                    try:
                        while len(response_data) < 1048576:  # 1MB max
                            try:
                                chunk = ssl_sock.recv(4096)
                                if not chunk:
                                    break
                                response_data += chunk

                                if b"\r\n\r\n" in response_data:
                                    parts = response_data.split(b"\r\n\r\n", 1)
                                    headers = parts[0].decode('utf-8', errors='ignore')

                                    content_length = None
                                    for line in headers.split("\r\n"):
                                        if line.lower().startswith("content-length:"):
                                            content_length = int(line.split(":", 1)[1].strip())
                                            break

                                    if content_length is not None:
                                        body = parts[1] if len(parts) > 1 else b""
                                        if len(body) >= content_length:
                                            break
                                    elif "204" in headers or content_length == 0:
                                        break
                            except socket.timeout:
                                logger.debug("Socket timeout while reading response, using data received so far")
                                socket_error = "Socket timeout"
                                break
                            except ssl.SSLError as e:
                                logger.debug(f"SSL error while reading response: {e}")
                                socket_error = f"SSL error: {str(e)}"
                                break
                            except Exception as e:
                                logger.debug(f"Error reading from socket: {e}, using data received so far")
                                socket_error = str(e)
                                break
                    finally:
                        ssl_sock.close()

                    response_str = response_data.decode('utf-8', errors='ignore')
                    if not response_str:
                        if socket_error:
                            raise Exception(f"No response from provider ({socket_error})")
                        else:
                            raise Exception("Empty response from provider")

                    lines = response_str.split("\r\n")
                    status_line = lines[0]
                    status_code = int(status_line.split()[1])

                    response_body = ""
                    if "\r\n\r\n" in response_str:
                        response_body = response_str.split("\r\n\r\n", 1)[1]

                    if status_code in [200, 201, 202, 204]:
                        logger.info(f"Manifest submission successful: {status_code}")
                        return {
                            "status": "success",
                            "provider": provider_endpoint,
                            "lease_id": lease_id,
                            "method": "HTTP (socket-based)",
                            "status_code": status_code,
                            "provider_version": provider_version,
                        }
                    else:
                        error_msg = response_body[:500] if response_body else f"HTTP {status_code}"
                        logger.error(f"Manifest submission failed: {error_msg}")
                        return {
                            "status": "error",
                            "error": error_msg,
                            "provider": provider_endpoint,
                            "method": "HTTP (socket-based)",
                            "status_code": status_code,
                            "provider_version": provider_version,
                        }
                finally:
                    if socket_cert_file:
                        socket_cert_file.close()
                        os.unlink(socket_cert_file.name)
                    if socket_key_file:
                        socket_key_file.close()
                        os.unlink(socket_key_file.name)

            elif cert_pem and key_pem:
                url = f"{provider_endpoint.rstrip('/')}{path}"

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Content-Length": str(len(manifest_json))
                }

                cert_file = tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False)
                key_file = tempfile.NamedTemporaryFile(mode="w", suffix=".key", delete=False)

                try:
                    cert_file.write(cert_pem)
                    cert_file.flush()
                    key_file.write(key_pem)
                    key_file.flush()

                    response = requests.put(
                        url,
                        data=manifest_json,
                        headers=headers,
                        timeout=timeout,
                        cert=(cert_file.name, key_file.name),
                        verify=False
                    )

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

                finally:
                    cert_file.close()
                    key_file.close()
                    os.unlink(cert_file.name)
                    os.unlink(key_file.name)
            else:
                url = f"{provider_endpoint.rstrip('/')}{path}"

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Content-Length": str(len(manifest_json))
                }

                response = requests.put(
                    url,
                    data=manifest_json,
                    headers=headers,
                    timeout=timeout
                )

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
