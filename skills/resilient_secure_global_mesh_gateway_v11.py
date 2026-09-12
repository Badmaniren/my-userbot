import requests
from skills.resilient_secure_global_mesh_federation_v10 import ResilientSecureGlobalMeshFederationV10
from skills.resilient_secure_smart_crawler_hub_v11_global_mesh import ResilientSecureSmartCrawlerHubV11GlobalMesh


class ResilientSecureGlobalMeshGatewayV11Error(Exception):
    """Custom exception for ResilientSecureGlobalMeshGatewayV11 errors."""
    pass


class ResilientSecureGlobalMeshGatewayV11:
    def __init__(self, db_path=":memory:", max_memory_mb=256, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.federation_node = ResilientSecureGlobalMeshFederationV10(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.mesh_hub_node = ResilientSecureSmartCrawlerHubV11GlobalMesh(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )

    def validate_target_headers(self, target, timeout):
        try:
            response = requests.head(target, timeout=timeout)
            return bool(response.status_code == 200)
        except Exception:
            return False

    def coordinate_expansion(self, target, timeout):
        return self.mesh_hub_node.coordinate_expansion(target, timeout)

    def coordinate_expansion_safe(self, target, timeout):
        try:
            return self.coordinate_expansion(target, timeout)
        except Exception:
            return False

    def export_analytics_report(self, target, report_data):
        return self.mesh_hub_node.export_analytics_report(target, report_data)

    def get_exported_report(self, target):
        return self.mesh_hub_node.get_exported_report(target)

    def process_stream(self, target, timeout):
        return self.mesh_hub_node.process_stream(target, timeout)

    def route_request(self, target, timeout):
        return self.federation_node.route_request(target, timeout)