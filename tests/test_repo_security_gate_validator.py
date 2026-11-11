import io
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.repo_health_metric_validator import MetricValidationError
from skills.repo_security_gate_validator import (
    RepoSecurityGateValidator,
    validate_repo_security_gate,
)


def _rnd_str(prefix="str_"):
    return f"{prefix}{uuid.uuid4().hex}"


def _rnd_path():
    parts = [uuid.uuid4().hex[:8] for _ in range(random.randint(2, 4))]
    return "/" + "/".join(parts)


class TestRepoSecurityGateValidator(unittest.TestCase):
    def test_init_initializes_collaborators(self):
        repo_path = _rnd_path()
        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            dummy_sec_instance = MagicMock()
            dummy_hlth_instance = MagicMock()
            mock_sec_cls.return_value = dummy_sec_instance
            mock_hlth_cls.return_value = dummy_hlth_instance

            validator = RepoSecurityGateValidator(repo_path=repo_path)

            mock_sec_cls.assert_called_once_with(repo_path)
            mock_hlth_cls.assert_called_once_with()
            self.assertEqual(validator.repo_path, repo_path)
            self.assertIs(validator.security_gateway, dummy_sec_instance)
            self.assertIs(validator.health_validator, dummy_hlth_instance)

    def test_validate_gate_both_pass_dict_health(self):
        repo_path = _rnd_path()
        run_id = _rnd_str("run_")
        metric_key = _rnd_str("metric_")
        metric_val = random.randint(10, 100)
        metrics_data = {"run_id": run_id, metric_key: metric_val}

        sec_token = _rnd_str("sec_ok_")
        sec_response = {"passed": True, "token": sec_token, "status": "SUCCESS"}
        hlth_score = random.random()
        hlth_response = {"valid": True, "score": hlth_score}

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = sec_response
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.return_value = hlth_response
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate(metrics_data)

            self.assertTrue(result["passed"])
            self.assertTrue(result["allowed"])
            self.assertFalse(result["blocked"])
            self.assertEqual(result["run_id"], run_id)
            self.assertEqual(result["security_evaluation"]["token"], sec_token)
            self.assertEqual(result["health_evaluation"]["score"], hlth_score)
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["reasons"], [])
            self.assertEqual(result["failures"], [])
            self.assertIn(run_id, result["audit_record"])

    def test_validate_gate_both_pass_boolean_health(self):
        repo_path = _rnd_path()
        metrics_data = {_rnd_str("k_"): _rnd_str("v_")}

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = {"passed": True}
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.return_value = True
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate(metrics_data)

            self.assertTrue(result["passed"])
            self.assertTrue(result["allowed"])
            self.assertFalse(result["blocked"])
            self.assertEqual(result["health_evaluation"], {"valid": True})

    def test_validate_gate_security_fails_with_reason(self):
        repo_path = _rnd_path()
        reason_msg = _rnd_str("sec_violation_")
        sec_response = {"passed": False, "reason": reason_msg}

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = sec_response
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.return_value = {"valid": True}
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate({})

            self.assertFalse(result["passed"])
            self.assertFalse(result["allowed"])
            self.assertTrue(result["blocked"])
            self.assertIn(reason_msg, result["errors"])
            self.assertIn(reason_msg, result["reasons"])

    def test_validate_gate_security_returns_invalid_type(self):
        repo_path = _rnd_path()
        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = random.choice([None, "not_a_dict", 42])
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.return_value = {"valid": True}
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate({})

            self.assertFalse(result["passed"])
            self.assertFalse(result["allowed"])
            self.assertTrue(result["blocked"])
            self.assertIn("Invalid security evaluation response", result["reasons"])
            self.assertIn("Invalid security evaluation response", result["errors"])

    def test_validate_gate_security_exception_caught(self):
        repo_path = _rnd_path()
        err_text = _rnd_str("sec_crash_")

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.side_effect = RuntimeError(err_text)
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.return_value = {"valid": True}
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate({})

            self.assertFalse(result["passed"])
            self.assertFalse(result["allowed"])
            self.assertTrue(result["blocked"])
            self.assertEqual(result["security_evaluation"]["status"], "FAIL")
            self.assertIn(err_text, result["errors"])

    def test_validate_gate_health_metric_validation_error(self):
        repo_path = _rnd_path()
        mve_msg = _rnd_str("metric_invalid_")

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = {"passed": True}
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.side_effect = MetricValidationError(mve_msg)
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate({})

            self.assertFalse(result["passed"])
            self.assertFalse(result["allowed"])
            self.assertTrue(result["blocked"])
            self.assertIn(mve_msg, result["failures"])
            self.assertIn(mve_msg, result["errors"])
            self.assertFalse(result["health_evaluation"]["valid"])
            self.assertEqual(result["health_evaluation"]["error"], mve_msg)

    def test_validate_gate_health_generic_exception(self):
        repo_path = _rnd_path()
        generic_err = _rnd_str("unexpected_health_err_")

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = {"passed": True}
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.side_effect = ValueError(generic_err)
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate({})

            self.assertFalse(result["passed"])
            self.assertFalse(result["allowed"])
            self.assertTrue(result["blocked"])
            self.assertIn(generic_err, result["failures"])

    def test_validate_gate_without_run_id_omits_run_id_key(self):
        repo_path = _rnd_path()
        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = {"passed": True}
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.return_value = {"valid": True}
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_gate({"some_key": _rnd_str()})

            self.assertNotIn("run_id", result)

    def test_validate_stream_gate_success(self):
        repo_path = _rnd_path()
        random_bytes = uuid.uuid4().bytes * random.randint(1, 5)
        stream_io = io.BytesIO(random_bytes)
        run_id = _rnd_str("stream_run_")
        parsed_payload = {"run_id": run_id, _rnd_str("val_"): random.randint(1, 1000)}

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = {"passed": True}
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate_stream.return_value = [parsed_payload]
            hlth_mock.validate.return_value = {"valid": True}
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_stream_gate(stream_io)

            hlth_mock.validate_stream.assert_called_once_with(stream_io)
            hlth_mock.validate.assert_called_once_with(parsed_payload)
            self.assertTrue(result["passed"])
            self.assertTrue(result["allowed"])
            self.assertEqual(result["run_id"], run_id)

    def test_validate_stream_gate_empty_list_from_stream(self):
        repo_path = _rnd_path()
        stream_io = io.BytesIO(b"")

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = {"passed": True}
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate_stream.return_value = []
            hlth_mock.validate.return_value = {"valid": True}
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_stream_gate(stream_io)

            hlth_mock.validate.assert_called_once_with({})
            self.assertTrue(result["passed"])

    def test_validate_stream_gate_stream_exception_caught(self):
        repo_path = _rnd_path()
        random_text = _rnd_str("corrupt_")
        stream_io = io.StringIO(random_text)
        stream_err = _rnd_str("stream_parse_error_")

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            hlth_mock = MagicMock()
            hlth_mock.validate_stream.side_effect = RuntimeError(stream_err)
            mock_hlth_cls.return_value = hlth_mock

            validator = RepoSecurityGateValidator(repo_path=repo_path)
            result = validator.validate_stream_gate(stream_io)

            self.assertFalse(result["passed"])
            self.assertFalse(result["allowed"])
            self.assertTrue(result["blocked"])
            self.assertIn(stream_err, result["errors"])
            self.assertIn(stream_err, result["reasons"])
            self.assertIn(stream_err, result["failures"])
            self.assertEqual(result["health_evaluation"]["error"], stream_err)

    def test_standalone_validate_repo_security_gate(self):
        repo_path = _rnd_path()
        run_id = _rnd_str("standalone_run_")
        metrics_data = {"run_id": run_id}

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_hlth_cls:
            sec_mock = MagicMock()
            sec_mock.scan_and_evaluate.return_value = {"passed": True}
            mock_sec_cls.return_value = sec_mock

            hlth_mock = MagicMock()
            hlth_mock.validate.return_value = {"valid": True}
            mock_hlth_cls.return_value = hlth_mock

            result = validate_repo_security_gate(repo_path=repo_path, metrics_data=metrics_data)

            mock_sec_cls.assert_called_once_with(repo_path)
            self.assertTrue(result["passed"])
            self.assertTrue(result["allowed"])
            self.assertEqual(result["run_id"], run_id)


if __name__ == "__main__":
    unittest.main()