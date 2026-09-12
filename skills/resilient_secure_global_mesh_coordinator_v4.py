import requests
from skills.resilient_secure_global_mesh_router_v3 import ResilientSecureGlobalMeshRouterV3
from skills.resilient_secure_global_mesh_node_v2 import ResilientSecureGlobalMeshNodeV2


class ResilientSecureGlobalMeshCoordinatorV4Error(Exception):
    """Кастомное исключение для координатора v4."""
    pass


class ResilientSecureGlobalMeshCoordinatorV4:
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=False):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.router = ResilientSecureGlobalMeshRouterV3(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.node = ResilientSecureGlobalMeshNodeV2(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )

        self._reports = {}

    def validate_target_headers(self, url: str, timeout: int) -> bool:
        try:
            response = requests.head(url, timeout=timeout)
            return response.status_code == 200
        except (requests.RequestException, OSError):
            return False

    def coordinate_expansion(self, url: str, timeout: int):
        try:
            return self.router.coordinate_expansion(url, timeout)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoordinatorV4Error(str(e)) from e
            raise

    def coordinate_expansion_safe(self, url: str, timeout: int) -> bool:
        try:
            res = self.router.coordinate_expansion(url, timeout)
            if isinstance(res, bool):
                return res
            return True
        except (requests.RequestException, OSError, Exception):
            return False

    def route_request(self, url: str, timeout: int):
        return self.router.route_request(url, timeout)

    def export_analytics_report(self, target: str, report_data: dict) -> None:
        self._reports[target] = {**report_data}

    def get_exported_report(self, target: str) -> dict:
        return {**self._reports.get(target, {})}

    def process_stream(self, url: str, timeout: int):
        response = requests.get(url, stream=True, timeout=timeout)
        for chunk in response.iter_content(chunk_size=1024):
            pass
        return None