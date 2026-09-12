import pytest
from skills.resilient_secure_smart_crawler_hub_v7_orchestrator import (
    ResilientSecureSmartCrawlerHubV7,
    ResilientSecureSmartCrawlerHubV7Error,
    ResilientSecureSmartCrawlerHubV7OrchestratorError,
    start_new
)

def test_resilient_secure_smart_crawler_hub_v7_integration():
    db_path = ":memory:"
    max_memory_mb = 128
    calls = 10
    period = 1.0
    raise_on_limit = True
    test_url = "https://example.com/sitemap.xml"
    timeout = 5

    hub = ResilientSecureSmartCrawlerHubV7(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )

    assert hub.db_path == db_path
    assert hub.max_memory_mb == max_memory_mb

    headers_valid = hub.validate_target_headers(test_url, timeout)
    assert isinstance(headers_valid, bool)

    expansion_safe = hub.coordinate_expansion_safe(test_url, timeout)
    assert isinstance(expansion_safe, bool)

    stream_result = hub.process_stream(test_url, timeout)
    assert isinstance(stream_result, dict)
    assert stream_result.get("status") == "success"

    with pytest.raises(ResilientSecureSmartCrawlerHubV7Error):
        hub.coordinate_expansion(test_url, timeout)

    orchestrator_result = start_new(
        url=test_url,
        timeout=timeout,
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    assert isinstance(orchestrator_result, dict)
    assert orchestrator_result.get("status") == "success"