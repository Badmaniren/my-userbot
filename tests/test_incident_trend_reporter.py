import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.incident_trend_reporter import IncidentTrendReporter

class TestIncidentTrendReporter(unittest.TestCase):

    def setUp(self):
        self.reporter = IncidentTrendReporter()

    def test_generate_trend_report_valid_data(self):
        random_id = uuid.uuid4().hex
        random_title = ''.join(random.choices(string.ascii_letters, k=10))
        random_severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        random_count = random.randint(1, 1000)

        raw_data = f"ID:{random_id},Title:{random_title},Severity:{random_severity},Count:{random_count}\n"
        mock_stream = io.BytesIO(raw_data.encode('utf-8'))

        with patch('skills.incident_trend_reporter.open', return_value=mock_stream, create=True):
            random_filepath = f"/var/log/incidents/{uuid.uuid4().hex}.log"
            report = self.reporter.generate_report(random_filepath)

        self.assertIsInstance(report, dict)
        self.assertIn("trends", report)
        self.assertEqual(report["trends"][0]["id"], random_id)
        self.assertEqual(report["trends"][0]["title"], random_title)
        self.assertEqual(report["trends"][0]["severity"], random_severity)
        self.assertEqual(report["trends"][0]["count"], random_count)

    def test_generate_trend_report_empty_stream(self):
        mock_stream = io.BytesIO(b"")

        with patch('skills.incident_trend_reporter.open', return_value=mock_stream, create=True):
            random_filepath = f"/tmp/{uuid.uuid4().hex}.csv"
            report = self.reporter.generate_report(random_filepath)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("trends"), [])
        self.assertEqual(report.get("total_incidents"), 0)

    def test_trend_aggregator_logic(self):
        severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        generated_items = []
        raw_lines = []

        for _ in range(5):
            item_id = uuid.uuid4().hex
            severity = random.choice(severities)
            count = random.randint(10, 500)
            generated_items.append((item_id, severity, count))
            raw_lines.append(f"{item_id},{severity},{count}\n")

        full_content = "".join(raw_lines).encode('utf-8')
        mock_stream = io.BytesIO(full_content)

        with patch('skills.incident_trend_reporter.open', return_value=mock_stream, create=True):
            filepath = f"/opt/data/{uuid.uuid4().hex}.dat"
            result = self.reporter.aggregate_trends(filepath)

        self.assertIn("summary", result)
        self.assertEqual(result["total_entries"], 5)
        
        for entry in result["parsed_entries"]:
            self.assertTrue(any(entry["id"] == item[0] for item in generated_items))

    def test_malformed_data_handling(self):
        garbage_data = ''.join(random.choices(string.printable, k=150)).encode('utf-8')
        mock_stream = io.BytesIO(garbage_data)

        with patch('skills.incident_trend_reporter.open', return_value=mock_stream, create=True):
            filepath = f"/var/crash/{uuid.uuid4().hex}.err"
            report = self.reporter.generate_report(filepath)

        self.assertIsInstance(report, dict)
        self.assertIn("errors", report)
        self.assertGreater(len(report["errors"]), 0)

    def test_export_trend_report_payload(self):
        random_dest = f"https://api.incident-engine.internal/v1/reports/{uuid.uuid4().hex}"
        random_token = uuid.uuid4().hex
        
        test_payload = {
            "report_id": uuid.uuid4().hex,
            "metric": random.randint(50, 9999)
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "accepted", "token": random_token}

        with patch('requests.post', return_value=mock_response) as mock_post:
            response = self.reporter.export_report(random_dest, test_payload)
            
            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            called_json = mock_post.call_args[1]["json"]

            self.assertEqual(called_url, random_dest)
            self.assertEqual(called_json["report_id"], test_payload["report_id"])
            self.assertEqual(response["token"], random_token)