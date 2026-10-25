import unittest
from unittest.mock import patch
import random
import uuid

from skills.anomaly_pattern_matcher import (
    AnomalyPatternMatcherError,
    PatternDefinition,
    AnomalyPatternMatcher,
    match_pattern,
    _default_matcher
)


class TestAnomalyPatternMatcher(unittest.TestCase):

    def setUp(self):
        _default_matcher.registry.clear()

    def test_pattern_definition_initialization(self):
        pid = uuid.uuid4().hex
        regex_str = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        category = random.choice(["DATABASE", "SYSTEM", "NETWORK", "SECURITY"])

        def_obj = PatternDefinition(
            pattern_id=pid,
            regex=regex_str,
            severity=severity,
            category=category
        )

        self.assertEqual(def_obj.pattern_id, pid)
        self.assertEqual(def_obj.regex, regex_str)
        self.assertEqual(def_obj.severity, severity)
        self.assertEqual(def_obj.category, category)

    def test_anomaly_pattern_matcher_add_invalid(self):
        matcher = AnomalyPatternMatcher()
        fake_payload = uuid.uuid4().hex

        with self.assertRaises(AnomalyPatternMatcherError):
            matcher.add_pattern(fake_payload)

    def test_anomaly_pattern_matcher_match_log(self):
        pid = uuid.uuid4().hex
        keyword = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        category = uuid.uuid4().hex

        pattern = PatternDefinition(
            pattern_id=pid,
            regex=keyword,
            severity=severity,
            category=category
        )

        matcher = AnomalyPatternMatcher([pattern])
        log_line = f"INFO process started {keyword} error encountered"

        matches = matcher.match_log(log_line)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["pattern_id"], pid)
        self.assertEqual(matches[0]["severity"], severity)
        self.assertEqual(matches[0]["category"], category)
        self.assertEqual(matches[0]["matched_line"], log_line)

    def test_anomaly_pattern_matcher_match_regex(self):
        pid = uuid.uuid4().hex
        regex_expr = r"ERR-\d{3}"
        severity = random.choice(["HIGH", "CRITICAL"])
        category = uuid.uuid4().hex

        pattern = PatternDefinition(
            pattern_id=pid,
            regex=regex_expr,
            severity=severity,
            category=category
        )

        matcher = AnomalyPatternMatcher([pattern])
        err_code = f"{random.randint(100, 999)}"
        log_line = f"System failure code: ERR-{err_code} occurred."

        matches = matcher.match_log(log_line)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["pattern_id"], pid)

    def test_anomaly_pattern_matcher_match_telemetry(self):
        matcher = AnomalyPatternMatcher()
        telemetry_payload = {uuid.uuid4().hex: random.random()}
        result = matcher.match_telemetry(telemetry_payload)
        self.assertEqual(result, [])

    def test_match_pattern_with_registered(self):
        pid = uuid.uuid4().hex
        keyword = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        category = uuid.uuid4().hex

        _default_matcher.add_pattern(
            PatternDefinition(
                pattern_id=pid,
                regex=keyword,
                severity=severity,
                category=category
            )
        )

        log_line = f"Traceback {keyword} failed."

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = match_pattern(log_line)
            self.assertTrue(mock_exists.called)

        self.assertIsNotNone(result)
        self.assertIn("pattern", result)
        self.assertEqual(result["pattern"]["pattern_id"], pid)

    def test_match_pattern_fallback_critical(self):
        random_suffix = uuid.uuid4().hex
        log_line = f"CRITICAL_EVENT_{random_suffix}"

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = match_pattern(log_line)
            self.assertTrue(mock_exists.called)

        self.assertIsNotNone(result)
        self.assertIn("pattern", result)
        self.assertEqual(result["pattern"]["pattern_id"], "fallback-pattern-id")
        self.assertEqual(result["pattern"]["severity"], "CRITICAL")
        self.assertEqual(result["pattern"]["matched_line"], log_line)

    def test_match_pattern_fallback_timeout(self):
        random_suffix = uuid.uuid4().hex
        log_line = f"Operation timeout on socket {random_suffix}"

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = match_pattern(log_line)
            self.assertTrue(mock_exists.called)

        self.assertIsNotNone(result)
        self.assertIn("pattern", result)
        self.assertEqual(result["pattern"]["pattern_id"], "fallback-pattern-id")
        self.assertEqual(result["pattern"]["matched_line"], log_line)

    def test_match_pattern_none(self):
        random_text = uuid.uuid4().hex

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = match_pattern(random_text)
            self.assertTrue(mock_exists.called)

        self.assertIsNone(result)

    def test_mocked_external_dependency_behavior(self):
        random_msg = uuid.uuid4().hex
        log_line = f"Normal log line {random_msg}"

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            match_pattern(log_line)
            self.assertTrue(mock_exists.called)


if __name__ == "__main__":
    unittest.main()