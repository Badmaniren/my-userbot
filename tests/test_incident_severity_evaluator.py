import unittest
from unittest.mock import patch, mock_open
import os
import json
import random
import uuid
import requests
from skills.incident_severity_evaluator import IncidentSeverityEvaluator, evaluate_incident_severity

class TestIncidentSeverityEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = IncidentSeverityEvaluator()
        self.rnd_str = uuid.uuid4().hex
        self.rnd_score = round(random.uniform(1.0, 10.0), 2)
        self.rnd_unauth = random.randint(10, 1000)
        self.rnd_error_rate = round(random.uniform(0.01, 1.0), 2)

    def test_evaluate_critical_severity_by_vulnerability(self):
        vuln_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        vulnerabilities = [
            {
                "id": vuln_id,
                "severity": "CRITICAL",
                "exploit_available": True
            }
        ]
        telemetry = {
            "cvss_score": self.rnd_score,
            "active_exploits": False,
            "custom_field": self.rnd_str
        }
        
        result = self.evaluator.evaluate(telemetry, vulnerabilities)
        self.assertEqual(result["severity_level"], "CRITICAL")
        self.assertEqual(result["vulnerabilities"][0]["id"], vuln_id)
        self.assertEqual(result["telemetry"]["custom_field"], self.rnd_str)

    def test_evaluate_critical_severity_by_telemetry(self):
        vulnerabilities = [
            {
                "id": f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}",
                "severity": "HIGH",
                "exploit_available": False
            }
        ]
        telemetry = {
            "cvss_score": 9.5,
            "active_exploits": True,
            "marker": self.rnd_str
        }
        
        result = self.evaluator.evaluate(telemetry, vulnerabilities)
        self.assertEqual(result["severity_level"], "CRITICAL")
        self.assertEqual(result["score"], 9.5)
        self.assertEqual(result["telemetry"]["marker"], self.rnd_str)

    def test_evaluate_low_severity(self):
        vulnerabilities = [
            {
                "id": f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}",
                "severity": "MEDIUM",
                "exploit_available": False
            }
        ]
        telemetry = {
            "cvss_score": 4.5,
            "active_exploits": False,
            "note": self.rnd_str
        }
        
        result = self.evaluator.evaluate(telemetry, vulnerabilities)
        self.assertEqual(result["severity_level"], "LOW")
        self.assertEqual(result["score"], 4.5)
        self.assertEqual(result["telemetry"]["note"], self.rnd_str)

    def test_evaluate_default_score(self):
        vulnerabilities = []
        telemetry = {
            "cvss_score": 0.0,
            "active_exploits": False,
            "token": self.rnd_str
        }
        
        result = self.evaluator.evaluate(telemetry, vulnerabilities)
        self.assertEqual(result["score"], 2.5)
        self.assertEqual(result["severity_level"], "LOW")
        self.assertEqual(result["telemetry"]["token"], self.rnd_str)

    def test_calculate_risk_factor(self):
        payload = {
            "error_rate": self.rnd_error_rate,
            "unauthorized_access_attempts": self.rnd_unauth
        }
        risk = self.evaluator.calculate_risk_factor(payload)
        expected = float(max(0.0, min(100.0, (self.rnd_error_rate * 50.0) + (min(self.rnd_unauth, 500) / 10.0))))
        self.assertEqual(risk, expected)

    def test_evaluate_with_remote_telemetry_success(self):
        url = f"http://{uuid.uuid4().hex}.test/api"
        payload = {"endpoint": url}
        
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None
            
            res = self.evaluator.evaluate_with_remote_telemetry(payload)
            self.assertTrue(res.get("remote_verified"))
            mock_get.assert_called_once_with(url, timeout=5)

    def test_evaluate_with_remote_telemetry_failure(self):
        url = f"http://{uuid.uuid4().hex}.test/api"
        payload = {"endpoint": url}
        err_msg = f"Error-{uuid.uuid4().hex}"
        
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException(err_msg)
            
            res = self.evaluator.evaluate_with_remote_telemetry(payload)
            self.assertFalse(res.get("remote_verified"))
            self.assertIn(err_msg, res.get("error"))

class TestIncidentSeverityEvaluatorIntegration(unittest.TestCase):
    def test_evaluate_incident_severity_with_file_output(self):
        incident_id = uuid.uuid4().hex
        vuln_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        output_dir = f"temp_dir_{uuid.uuid4().hex}"
        
        incident_data = {
            "incident_id": incident_id,
            "telemetry": {
                "cvss_score": 9.1,
                "active_exploits": True,
                "custom_key": self.id()
            },
            "vulnerabilities": [
                {
                    "id": vuln_id,
                    "severity": "CRITICAL",
                    "exploit_available": True
                }
            ]
        }
        
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("json.dump") as mock_json_dump:
            
            report = evaluate_incident_severity(incident_data, output_path=output_dir)
            
            self.assertEqual(report["incident_id"], incident_id)
            self.assertEqual(report["severity_level"], "CRITICAL")
            self.assertEqual(report["details"]["vulnerabilities"][0]["id"], vuln_id)
            mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()

    def test_evaluate_incident_severity_without_output(self):
        incident_id = uuid.uuid4().hex
        incident_data = {
            "incident_id": incident_id,
            "telemetry": {
                "cvss_score": 3.0,
                "active_exploits": False
            },
            "vulnerabilities": []
        }
        
        report = evaluate_incident_severity(incident_data, output_path=None)
        self.assertEqual(report["incident_id"], incident_id)
        self.assertEqual(report["severity_level"], "LOW")
        self.assertEqual(report["score"], 3.0)

if __name__ == "__main__":
    unittest.main()