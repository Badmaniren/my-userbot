import hashlib
import io
import json
import os
import random
import shutil
import string
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer
from skills.repo_security_gate_validator import RepoSecurityGateValidator


def _rnd_str(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def _rnd_url():
    proto = random.choice(["http", "https"])
    return f"{proto}://{_rnd_str(8)}.example.com/{_rnd_str(10)}"


def _rnd_bytes(min_len=20, max_len=100):
    length = random.randint(min_len, max_len)
    return os.urandom(length)


class TestRepoHealthSecuritySyncer(unittest.TestCase):
    def setUp(self):
        self.temp_dirs_to_remove = []

    def tearDown(self):
        for temp_dir in self.temp_dirs_to_remove:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _create_temp_dir(self):
        prefix = f"syncer_{_rnd_str(6)}_"
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs_to_remove.append(temp_dir)
        return temp_dir

    def test_init_public_fields(self):
        repo_id = f"repo-{_rnd_str(8)}"
        health_url = _rnd_url()
        security_url = _rnd_url()
        target_dir = f"/tmp/{_rnd_str(10)}"

        syncer = RepoHealthSecuritySyncer(
            repo_id=repo_id,
            health_url=health_url,
            security_url=security_url,
            target_directory=target_dir
        )

        self.assertEqual(syncer.repo_id, repo_id)
        self.assertEqual(syncer.health_url, health_url)
        self.assertEqual(syncer.security_url, security_url)
        self.assertEqual(syncer.target_directory, target_dir)

    def test_synchronize_with_payload_success_without_target_directory(self):
        syncer = RepoHealthSecuritySyncer()
        sync_id = f"sync_{_rnd_str(8)}"
        token = f"tok_{_rnd_str(12)}"
        health_score = random.randint(10, 99)
        sec_score = random.randint(50, 100)
        vuln_count = random.randint(0, 5)
        vulns = [f"CVE-{random.randint(2020, 2026)}-{random.randint(1000, 9999)}" for _ in range(vuln_count)]

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": sec_score,
            "vulnerabilities": vulns
        }

        with patch.dict(os.environ, {}, clear=True):
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertEqual(result.get("health_data"), {"health_score": health_score, "token": token})
        self.assertEqual(
            result.get("security_data"),
            {"vulnerabilities": vulns, "security_score": sec_score, "token": token}
        )

    def test_synchronize_with_payload_generates_sync_id_if_missing(self):
        syncer = RepoHealthSecuritySyncer()
        health_score = random.randint(1, 100)
        sec_score = random.randint(1, 100)
        payload = {
            "health_score": health_score,
            "security_score": sec_score,
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {}, clear=True):
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertTrue(bool(result.get("synced_id")))
        self.assertNotIn("token", result.get("health_data", {}))
        self.assertNotIn("token", result.get("security_data", {}))

    def test_synchronize_with_payload_token_mismatch(self):
        syncer = RepoHealthSecuritySyncer()
        sync_id = f"sync_{_rnd_str(8)}"
        expected_env_token = f"valid_{_rnd_str(10)}"
        invalid_payload_token = f"invalid_{_rnd_str(10)}"

        payload = {
            "sync_id": sync_id,
            "token": invalid_payload_token,
            "health_score": random.randint(10, 80),
            "security_score": random.randint(10, 80),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": expected_env_token}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertNotIn("health_data", result)
        self.assertNotIn("security_data", result)

    def test_synchronize_with_payload_token_match(self):
        syncer = RepoHealthSecuritySyncer()
        sync_id = f"sync_{_rnd_str(8)}"
        matching_token = f"token_{_rnd_str(14)}"

        payload = {
            "sync_id": sync_id,
            "token": matching_token,
            "health_score": random.randint(50, 95),
            "security_score": random.randint(40, 90),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": matching_token}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_with_payload_writes_audit_file_and_calls_validator(self):
        base_dir = self._create_temp_dir()
        target_dir = os.path.join(base_dir, f"sub_{_rnd_str(6)}")
        syncer = RepoHealthSecuritySyncer(target_directory=target_dir)

        sync_id = f"audit_sync_{_rnd_str(8)}"
        health_score = random.randint(60, 100)
        sec_score = random.randint(70, 100)
        vulns = [f"VULN-{_rnd_str(6)}"]

        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": sec_score,
            "vulnerabilities": vulns
        }

        with patch("skills.repo_health_security_syncer.RepoSecurityGateValidator") as mock_val_cls:
            mock_val_inst = MagicMock()
            mock_val_cls.return_value = mock_val_inst

            with patch.dict(os.environ, {}, clear=True):
                result = syncer.synchronize(metric_payload=payload)

            self.assertTrue(result.get("success"))
            mock_val_cls.assert_called_with(repo_path=target_dir)
            expected_file = os.path.join(target_dir, f"audit_{sync_id}.json")
            self.assertTrue(os.path.isfile(expected_file))
            mock_val_inst.validate.assert_called_once_with(expected_file)

            with open(expected_file, "r", encoding="utf-8") as f:
                saved_audit = json.load(f)

            self.assertEqual(saved_audit.get("correlation_id"), sync_id)
            self.assertEqual(saved_audit.get("health_metrics", {}).get("health_score"), health_score)
            self.assertEqual(saved_audit.get("security_metrics", {}).get("security_score"), sec_score)
            self.assertEqual(saved_audit.get("security_metrics", {}).get("vulnerabilities"), vulns)

    def test_synchronize_with_payload_validator_gate_fallback(self):
        target_dir = self._create_temp_dir()
        syncer = RepoHealthSecuritySyncer(target_directory=target_dir)
        sync_id = f"gate_sync_{_rnd_str(6)}"

        payload = {
            "sync_id": sync_id,
            "health_score": random.randint(10, 90),
            "security_score": random.randint(10, 90),
            "vulnerabilities": []
        }

        with patch("skills.repo_health_security_syncer.RepoSecurityGateValidator") as mock_val_cls:
            mock_val_inst = MagicMock(spec=["validate_gate"])
            mock_val_cls.return_value = mock_val_inst

            with patch.dict(os.environ, {}, clear=True):
                result = syncer.synchronize(metric_payload=payload)

            self.assertTrue(result.get("success"))
            expected_file = os.path.join(target_dir, f"audit_{sync_id}.json")
            mock_val_inst.validate_gate.assert_called_once_with(expected_file)

    def test_synchronize_with_payload_validator_init_type_error_fallbacks(self):
        target_dir = self._create_temp_dir()
        syncer = RepoHealthSecuritySyncer(target_directory=target_dir)
        sync_id = f"fallback_{_rnd_str(6)}"

        payload = {
            "sync_id": sync_id,
            "health_score": random.randint(10, 90),
            "security_score": random.randint(10, 90),
            "vulnerabilities": []
        }

        call_args = []

        def side_effect(*args, **kwargs):
            call_args.append((args, kwargs))
            if len(call_args) == 1:
                raise TypeError("repo_path target dir unsupported")
            if len(call_args) == 2:
                raise TypeError("dirname unsupported")
            inst = MagicMock()
            return inst

        with patch("skills.repo_health_security_syncer.RepoSecurityGateValidator", side_effect=side_effect):
            with patch.dict(os.environ, {}, clear=True):
                result = syncer.synchronize(metric_payload=payload)

            self.assertTrue(result.get("success"))
            self.assertEqual(len(call_args), 3)
            self.assertEqual(call_args[0][1], {"repo_path": target_dir})
            self.assertEqual(call_args[1][1], {"repo_path": os.path.dirname(target_dir)})
            self.assertEqual(call_args[2], ((), {}))

    def test_synchronize_http_success(self):
        health_url = _rnd_url()
        security_url = _rnd_url()
        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)

        expected_health = {
            "metric_score": random.randint(50, 100),
            "marker": _rnd_str(10)
        }
        expected_security = {
            "sec_score": random.randint(40, 95),
            "cve_list": [_rnd_str(8)]
        }

        resp_health = MagicMock()
        resp_health.status_code = 200
        resp_health.json.return_value = expected_health

        resp_sec = MagicMock()
        resp_sec.status_code = 200
        resp_sec.json.return_value = expected_security

        def mock_get(url, *args, **kwargs):
            if url == health_url:
                return resp_health
            if url == security_url:
                return resp_sec
            raise ValueError(f"Unexpected url {url}")

        with patch("skills.repo_health_security_syncer.requests.get", side_effect=mock_get):
            result = syncer.synchronize()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("health_data"), expected_health)
        self.assertEqual(result.get("security_data"), expected_security)

    def test_synchronize_http_health_status_error(self):
        health_url = _rnd_url()
        security_url = _rnd_url()
        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)

        err_status = random.choice([400, 401, 404, 500, 502])
        err_msg = f"Health check failure: {_rnd_str(10)}"

        resp_health = MagicMock()
        resp_health.status_code = err_status
        resp_health.text = err_msg

        with patch("skills.repo_health_security_syncer.requests.get", return_value=resp_health) as mock_get:
            result = syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), err_status)
        self.assertEqual(result.get("error"), err_msg)
        mock_get.assert_called_once_with(health_url)

    def test_synchronize_http_security_status_error(self):
        health_url = _rnd_url()
        security_url = _rnd_url()
        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)

        resp_health = MagicMock()
        resp_health.status_code = 200
        resp_health.json.return_value = {"ok": True}

        err_status = random.choice([403, 404, 503])
        err_msg = f"Security check failure: {_rnd_str(10)}"

        resp_sec = MagicMock()
        resp_sec.status_code = err_status
        resp_sec.text = err_msg

        def mock_get(url, *args, **kwargs):
            if url == health_url:
                return resp_health
            return resp_sec

        with patch("skills.repo_health_security_syncer.requests.get", side_effect=mock_get):
            result = syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), err_status)
        self.assertEqual(result.get("error"), err_msg)

    def test_synchronize_http_exception(self):
        health_url = _rnd_url()
        security_url = _rnd_url()
        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
        exception_msg = f"Connection timeout: {_rnd_str(12)}"

        with patch("skills.repo_health_security_syncer.requests.get", side_effect=RuntimeError(exception_msg)):
            result = syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), 500)
        self.assertEqual(result.get("error"), exception_msg)

    def test_export_audit_stream_from_raw_stream(self):
        health_url = _rnd_url()
        syncer = RepoHealthSecuritySyncer(health_url=health_url)

        random_data = _rnd_bytes(40, 150)
        expected_hash = hashlib.sha256(random_data).hexdigest()
        expected_len = len(random_data)

        resp = MagicMock()
        resp.raw = io.BytesIO(random_data)

        with patch("skills.repo_health_security_syncer.requests.get", return_value=resp) as mock_get:
            result = syncer.export_audit_stream()

        mock_get.assert_called_once_with(health_url)
        self.assertEqual(result.get("stream_hash"), expected_hash)
        self.assertEqual(result.get("bytes_read"), expected_len)

    def test_export_audit_stream_from_content_fallback(self):
        health_url = _rnd_url()
        syncer = RepoHealthSecuritySyncer(health_url=health_url)

        random_data = _rnd_bytes(30, 80)
        expected_hash = hashlib.sha256(random_data).hexdigest()
        expected_len = len(random_data)

        resp = MagicMock()
        resp.raw = None
        resp.content = random_data

        with patch("skills.repo_health_security_syncer.requests.get", return_value=resp) as mock_get:
            result = syncer.export_audit_stream()

        mock_get.assert_called_once_with(health_url)
        self.assertEqual(result.get("stream_hash"), expected_hash)
        self.assertEqual(result.get("bytes_read"), expected_len)


class TestRepoSecurityGateValidatorCompatibility(unittest.TestCase):
    def test_validator_instantiation_requires_repo_path(self):
        test_path = f"/tmp/{_rnd_str(12)}"
        try:
            validator = RepoSecurityGateValidator(repo_path=test_path)
            self.assertTrue(hasattr(validator, "repo_path") or hasattr(validator, "validate") or hasattr(validator, "validate_gate"))
        except TypeError:
            pass


if __name__ == "__main__":
    unittest.main()