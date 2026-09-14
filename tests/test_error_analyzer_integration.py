import pytest
from skills.error_analyzer import analyze_errors, save_error_report, has_critical_errors

def test_error_analyzer_integration():
    sample_logs = (
        "[ERROR] 2023-10-25 10:00:01 - NullPointerException in module auth\n"
        "[WARNING] 2023-10-25 10:00:05 - Deprecated API usage\n"
        "[CRITICAL] 2023-10-25 10:00:10 - Database connection lost"
    )

    is_critical = has_critical_errors(sample_logs)
    assert isinstance(is_critical, bool)
    assert is_critical is True

    analysis_result = analyze_errors(sample_logs)
    assert isinstance(analysis_result, str)
    assert len(analysis_result) > 0

    save_status = save_error_report(analysis_result)
    assert isinstance(save_status, bool)
    assert save_status is True