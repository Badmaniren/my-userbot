import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
import logging

from skills.market_portfolio_stress_audit_telemetry_logger import (
    TelemetryLoggingError,
    StressAuditTelemetryLogger,
    market_portfolio_stress_audit_telemetry_logger
)

class TestMarketPortfolioStressAuditTelemetryLogger(unittest.TestCase):

    def setUp(self):
        self.logger_name = f"Logger_{uuid.uuid4().hex[:8]}"
        self.telemetry_logger = StressAuditTelemetryLogger(logger_name=self.logger_name)

    def test_serialize_payload_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 999)
        payload = {rand_key: rand_val}

        serialized = self.telemetry_logger._serialize_payload(payload)
        parsed = json.loads(serialized)

        self.assertIn(rand_key, parsed)
        self.assertEqual(parsed[rand_key], rand_val)

    def test_serialize_payload_failure(self):
        bad_payload = {"unserializable": set([random.randint(1, 10)])}
        with self.assertRaises(TelemetryLoggingError) as ctx:
            self.telemetry_logger._serialize_payload(bad_payload)
        self.assertIn("Serialization failed", str(ctx.exception))

    def test_log_telemetry_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        payload = {rand_key: rand_val}

        with patch.object(self.telemetry_logger.internal_logger, 'info') as mock_info:
            res = self.telemetry_logger.log_telemetry(payload)
            self.assertTrue(res)
            mock_info.assert_called_once()
            args, _ = mock_info.call_args
            self.assertIn(rand_key, args[0])
            self.assertIn(rand_val, args[0])

    def test_log_telemetry_invalid_payload(self):
        for invalid_payload in [{}, None, [], "not_a_dict"]:
            with self.assertRaises(TelemetryLoggingError):
                self.telemetry_logger.log_telemetry(invalid_payload) # type: ignore

    def test_log_telemetry_internal_exception(self):
        rand_key = uuid.uuid4().hex
        payload = {rand_key: random.randint(1, 50)}

        with patch.object(self.telemetry_logger.internal_logger, 'info', side_effect=RuntimeError("Stream exploded")):
            with self.assertRaises(TelemetryLoggingError) as ctx:
                self.telemetry_logger.log_telemetry(payload)
            self.assertIn("Failed to log telemetry", str(ctx.exception))

    def test_consume_telemetry_stream_success(self):
        rand_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(rand_bytes)

        content = self.telemetry_logger.consume_telemetry_stream(stream)
        self.assertEqual(content, rand_bytes)

    def test_consume_telemetry_stream_invalid_object(self):
        not_a_stream = {"data": uuid.uuid4().hex}
        with self.assertRaises(TelemetryLoggingError) as ctx:
            self.telemetry_logger.consume_telemetry_stream(not_a_stream) # type: ignore
        self.assertIn("not a valid stream", str(ctx.exception))

    def test_consume_telemetry_stream_non_bytes_return(self):
        mock_stream = MagicMock()
        mock_stream.read.return_value = uuid.uuid4().hex

        with self.assertRaises(TelemetryLoggingError) as ctx:
            self.telemetry_logger.consume_telemetry_stream(mock_stream)
        self.assertIn("Stream did not return bytes", str(ctx.exception))

    def test_dispatch_audit_telemetry_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(1000, 9999)
        audit_data = {rand_key: rand_val}

        dispatched = self.telemetry_logger.dispatch_audit_telemetry(audit_data)
        self.assertIn(rand_key, dispatched)
        self.assertEqual(dispatched[rand_key], rand_val)
        self.assertIn("timestamp", dispatched)
        self.assertIsInstance(dispatched["timestamp"], float)

    def test_dispatch_audit_telemetry_invalid_type(self):
        with self.assertRaises(TelemetryLoggingError) as ctx:
            self.telemetry_logger.dispatch_audit_telemetry([1, 2, 3]) # type: ignore
        self.assertIn("Audit data must be a dictionary", str(ctx.exception))

    def test_functional_market_portfolio_stress_audit_telemetry_logger(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:6]}"
        rand_audit_id = f"aud_{uuid.uuid4().hex[:6]}"
        collector_data = {uuid.uuid4().hex: random.randint(10, 100)}
        pipeline_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_meta = {"audit_id": rand_audit_id, uuid.uuid4().hex: True}

        with patch("skills.market_portfolio_stress_audit_telemetry_logger.db_storage") as mock_db:
            res = market_portfolio_stress_audit_telemetry_logger(
                portfolio_id=rand_portfolio_id,
                collector_data=collector_data,
                pipeline_data=pipeline_data,
                telemetry_meta=telemetry_meta
            )

            self.assertEqual(res["status"], "logged")
            self.assertEqual(res["portfolio_id"], rand_portfolio_id)
            self.assertEqual(res["audit_id"], rand_audit_id)

            mock_db.assert_called_once()
            _, kwargs = mock_db.call_args
            self.assertEqual(kwargs.get("query_type"), "save_telemetry")
            self.assertEqual(kwargs.get("portfolio_id"), rand_portfolio_id)

            record = kwargs.get("record")
            self.assertIsNotNone(record)
            self.assertEqual(record["portfolio_id"], rand_portfolio_id)
            self.assertEqual(record["audit_id"], rand_audit_id)
            self.assertEqual(record["collector_data"], collector_data)
            self.assertEqual(record["pipeline_data"], pipeline_data)
            self.assertEqual(record["telemetry_meta"], telemetry_meta)
            self.assertIn("timestamp", record)

if __name__ == '__main__':
    unittest.main()
