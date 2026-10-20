import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.audit_pipeline_bridge import AuditPipelineBridge, AuditPipelineBridgeError

class TestAuditPipelineBridge(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        with patch("skills.audit_pipeline_bridge.AnomalyAuditHub") as mock_hub, \
             patch("skills.audit_pipeline_bridge.AnomalyPipeline") as mock_pipeline:

            self.bridge = AuditPipelineBridge(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_initialization_composes_modules(self):
        rand_repo = f"/var/repos/{uuid.uuid4().hex}"
        rand_log = f"/var/logs/{uuid.uuid4().hex}.log"
        rand_thresh = round(random.uniform(0.01, 0.99), 4)

        with patch("skills.audit_pipeline_bridge.AnomalyAuditHub") as mock_hub_cls, \
             patch("skills.audit_pipeline_bridge.AnomalyPipeline") as mock_pipeline_cls:

            bridge = AuditPipelineBridge(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_thresh
            )

            mock_hub_cls.assert_called_once_with(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_thresh
            )
            mock_pipeline_cls.assert_called_once_with(
                repo_path=rand_repo,
                threshold=rand_thresh
            )
            self.assertEqual(bridge.repo_path, rand_repo)
            self.assertEqual(bridge.log_path, rand_log)
            self.assertEqual(bridge.threshold, rand_thresh)

    def test_run_audit_pipeline_success(self):
        raw_input_data = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        pipeline_output = {"status": "secure", "score": random.randint(100, 500)}

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = random.randint(1, 100)

        with patch.object(self.bridge.pipeline, "run", return_value=pipeline_output) as mock_run, \
             patch.object(self.bridge.hub, "aggregate_and_report", return_value=metric_val) as mock_agg:

            result = self.bridge.run_audit_pipeline(raw_input_data)

            mock_run.assert_called_once_with(raw_input_data)
            mock_agg.assert_called()
            self.assertEqual(result, pipeline_output)

    def test_run_audit_pipeline_failure_raises_custom_error(self):
        raw_input_data = "".join(random.choices(string.ascii_letters, k=16))
        exception_msg = f"Pipeline failure: {uuid.uuid4().hex}"

        with patch.object(self.bridge.pipeline, "run", side_effect=Exception(exception_msg)) as mock_run:
            with self.assertRaises(AuditPipelineBridgeError) as ctx:
                self.bridge.run_audit_pipeline(raw_input_data)

            mock_run.assert_called_once_with(raw_input_data)
            self.assertIn(exception_msg, str(ctx.exception))

    def test_execute_batch_audit_success(self):
        batch_size = random.randint(2, 5)
        raw_batch = ["".join(random.choices(string.ascii_lowercase, k=10)) for _ in range(batch_size)]
        batch_results = [{"id": uuid.uuid4().hex} for _ in range(batch_size)]

        with patch.object(self.bridge.pipeline, "run_batch", return_value=batch_results) as mock_run_batch, \
             patch.object(self.bridge.hub, "generate_final_report", return_value={"report": uuid.uuid4().hex}) as mock_gen_rep:

            res = self.bridge.execute_batch_audit(raw_batch)

            mock_run_batch.assert_called_once_with(raw_batch)
            mock_gen_rep.assert_called_once()
            self.assertEqual(res, batch_results)

    def test_execute_batch_audit_handles_exception(self):
        raw_batch = [uuid.uuid4().hex, uuid.uuid4().hex]
        err_msg = f"Batch error {uuid.uuid4().hex[:8]}"

        with patch.object(self.bridge.pipeline, "run_batch", side_effect=ValueError(err_msg)) as mock_run_batch:
            with self.assertRaises(AuditPipelineBridgeError):
                self.bridge.execute_batch_audit(raw_batch)
            mock_run_batch.assert_called_once_with(raw_batch)

    def test_log_external_anomaly_delegates_to_hub(self):
        source = f"src_{uuid.uuid4().hex[:4]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"info": uuid.uuid4().hex}
        telemetry = {"cpu": random.random()}

        with patch.object(self.bridge.hub, "log_anomaly") as mock_log:
            self.bridge.log_external_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )

            mock_log.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )

    def test_end_to_end_verification_flow(self):
        execution_id = uuid.uuid4().hex
        metrics_payload = {uuid.uuid4().hex: random.randint(10, 1000)}
        expected_output = {"execution_id": execution_id, "status": "completed"}

        with patch.object(self.bridge.pipeline, "run_end_to_end", return_value=expected_output) as mock_e2e, \
             patch.object(self.bridge.hub, "generate_final_report", return_value={"final": True}) as mock_final:

            res = self.bridge.run_full_security_cycle(execution_id, metrics_payload)

            mock_e2e.assert_called_once_with(execution_id, metrics_payload)
            mock_final.assert_called_once()
            self.assertEqual(res, expected_output)

    def test_stream_telemetry_and_process_pipeline(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        processed_data = {"processed": uuid.uuid4().hex}

        with patch.object(self.bridge.pipeline, "process_pipeline", return_value=processed_data) as mock_proc:
            res = self.bridge.process_stream_data(stream_data)

            mock_proc.assert_called_once_with(stream_data)
            self.assertEqual(res, processed_data)

    def test_log_external_anomaly_failure_raises_custom_error(self):
        with patch.object(self.bridge.hub, "log_anomaly", side_effect=RuntimeError("Hub error")):
            with self.assertRaises(AuditPipelineBridgeError) as ctx:
                self.bridge.log_external_anomaly("src", "HIGH", {}, {})
            self.assertIn("Log external anomaly failure", str(ctx.exception))

    def test_run_full_security_cycle_failure_raises_custom_error(self):
        with patch.object(self.bridge.pipeline, "run_end_to_end", side_effect=RuntimeError("Pipeline error")):
            with self.assertRaises(AuditPipelineBridgeError) as ctx:
                self.bridge.run_full_security_cycle("exec1", {})
            self.assertIn("Full security cycle failure", str(ctx.exception))

    def test_process_stream_data_failure_raises_custom_error(self):
        with patch.object(self.bridge.pipeline, "process_pipeline", side_effect=RuntimeError("Stream error")):
            with self.assertRaises(AuditPipelineBridgeError) as ctx:
                self.bridge.process_stream_data(io.BytesIO(b"data"))
            self.assertIn("Stream data processing failure", str(ctx.exception))

    def test_run_security_audit_pipeline_failure_raises_custom_error(self):
        with patch.object(self.bridge.pipeline, "run_end_to_end", side_effect=RuntimeError("E2E error")):
            with self.assertRaises(AuditPipelineBridgeError) as ctx:
                self.bridge.run_security_audit_pipeline("exec1", {}, {"source": "test"})
            self.assertIn("Security audit pipeline failure", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()