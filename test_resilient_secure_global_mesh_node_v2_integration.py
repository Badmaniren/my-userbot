import pytest
from skills.resilient_secure_global_mesh_node_v2 import ResilientSecureGlobalMeshNodeV2, ResilientSecureGlobalMeshNodeV2Error
from skills.resilient_secure_global_mesh_node_v1 import ResilientSecureSmartCrawlerHubV11GlobalMesh
from skills.resilient_secure_smart_crawler_hub_analytics_exporter import ResilientSecureSmartCrawlerHubAnalyticsExporter

def test_integration_resilient_secure_global_mesh_node_v2(tmp_path):
    db_file = tmp_path / "mesh_node_v2.db"
    db_path = str(db_file)
    max_memory_mb = 256
    calls = 10
    period = 1.0
    raise_on_limit = True

    node = ResilientSecureGlobalMeshNodeV2(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )

    assert isinstance(node, ResilientSecureGlobalMeshNodeV2)

    test_url = "http://example.com"
    target_name = "test_target"
    report_data = {"status": "active", "metrics": {"load": 0.1}}

    node.export_analytics_report(target_name, report_data)
    exported = node.get_exported_report(target_name)
    assert isinstance(exported, dict)
    assert exported.get("status") == "active"

    headers_valid = node.validate_target_headers(test_url, timeout=5)
    assert isinstance(headers_valid, bool)

    expansion_result = node.coordinate_expansion_safe(test_url, timeout=5)
    assert isinstance(expansion_result, bool)