import unittest
import io
import os
import tempfile
import uuid
import random
from typing import Any, Dict

from skills.telemetry_health_pipeline import TelemetryHealthPipeline, TelemetryHealthPipelineException


class TestTelemetryHealthPipelineIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.pipeline = TelemetryHealthPipeline()
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_full_pipeline_and_export_integration(self) -> None:
        # Генерируем уникальные случайные данные для исключения хардкода
        unique_id = str(uuid.uuid4())
        module_name = f"test_module_{unique_id[:8]}"

        incident_data = {
            "incident_id": unique_id,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": f"Auto-generated integration test incident {random.randint(1000, 9999)}"
        }

        audit_summary = {
            "status": "PASSED",
            "score": round(random.uniform(85.0, 100.0), 2)
        }

        metrics = {
            "cpu_usage": round(random.uniform(10.0, 90.0), 2),
            "memory_usage": round(random.uniform(20.0, 95.0), 2),
            "response_time_ms": round(random.uniform(50.0, 500.0), 2)
        }

        dashboard_format = random.choice(["json", "html", "summary"])
        incidents_list = [incident_data]
        patches_list = [{"patch_id": f"patch_{str(uuid.uuid4())[:8]}", "applied": True}]

        report_filename = f"report_{unique_id}.json"
        dashboard_filename = f"dashboard_{unique_id}.json"

        report_path = os.path.join(self.test_dir.name, report_filename)
        dashboard_path = os.path.join(self.test_dir.name, dashboard_filename)

        # Вызов полного конвейера без моков
        pipeline_result = self.pipeline.run_full_pipeline(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=report_path,
            dashboard_path=dashboard_path
        )

        # Проверяем реальный результат выполнения конвейера
        self.assertIsInstance(pipeline_result, dict)
        self.assertTrue(os.path.exists(report_path), "Report file should be created by the pipeline.")
        self.assertTrue(os.path.exists(dashboard_path), "Dashboard file should be created by the pipeline.")

        # Проверяем экспорт отчета
        export_filename = f"export_{unique_id}.json"
        export_path = os.path.join(self.test_dir.name, export_filename)

        self.pipeline.export_report(pipeline_result, export_path)
        self.assertTrue(os.path.exists(export_path), "Export comprehensive report file must exist.")

    def test_stream_pipeline_integration(self) -> None:
        unique_id = str(uuid.uuid4())
        output_filename = f"stream_output_{unique_id}.json"
        output_path = os.path.join(self.test_dir.name, output_filename)

        # Подготовка бинарного потока с валидными данными телеметрии
        raw_stream_data = f'{{"metric": "network_latency", "value": {random.randint(10, 150)}, "uuid": "{unique_id}"}}'.encode('utf-8')
        stream = io.BytesIO(raw_stream_data)

        stream_result = self.pipeline.execute_stream_pipeline(stream, output_path)

        self.assertIsInstance(stream_result, dict)
        self.assertTrue(os.path.exists(output_path), "Stream output file should be generated.")

    def test_invalid_stream_type_raises_exception(self) -> None:
        invalid_stream = f"not_a_binary_stream_{uuid.uuid4()}"
        output_path = os.path.join(self.test_dir.name, "should_not_exist.json")

        with self.assertRaises(TelemetryHealthPipelineException):
            self.pipeline.execute_stream_pipeline(invalid_stream, output_path)


if __name__ == "__main__":
    unittest.main()