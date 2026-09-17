import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
import string

# Импортируем тестируемый модуль
# Предполагается, что модуль реализует логику композиции указанных навыков
import skills.telemetry_health_pipeline as thp

class TestTelemetryHealthPipeline(unittest.TestCase):
    """Архитектор-Инквизитор проводит инспекцию жизненного цикла телеметрии."""

    def setUp(self):
        """Генерация хаотичных входных данных для предотвращения хардкода."""
        self.rand_str = lambda: "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 20)))
        self.rand_path = lambda ext: f"/{self.rand_str()}/{uuid.uuid4().hex}.{ext}"
        self.rand_hex = lambda: uuid.uuid4().hex

    def test_full_telemetry_lifecycle_execution(self):
        """Проверка полной цепочки: Streamer -> Processor -> Gateway."""

        # Исходные случайные данные
        source_path = self.rand_path("raw")
        module_name = f"MODULE_{self.rand_hex()}"
        report_path = self.rand_path("json")
        dashboard_path = self.rand_path("html")

        # Генерируем случайный пакет данных
        raw_packet_id = self.rand_hex()
        raw_telemetry_data = [
            {"id": raw_packet_id, "payload": self.rand_str(), "timestamp": random.random()}
        ]

        # Ожидаемые обработанные данные
        processed_data = [
            {"id": raw_packet_id, "status": "CONSISTENT", "verified": True}
        ]

        # Ожидаемые метрики и сводки
        audit_summary = {"audit_id": self.rand_hex(), "total": random.randint(1, 100)}
        metrics = {"latency": random.uniform(0.1, 5.0), "throughput": random.randint(100, 1000)}

        with patch('skills.telemetry_health_pipeline.TelemetryStreamer') as mock_streamer_cls, \
             patch('skills.telemetry_health_pipeline.TelemetryProcessor') as mock_processor_cls, \
             patch('skills.telemetry_health_pipeline.SystemHealthMonitoringGateway') as mock_gateway_cls:

            # Настройка моков
            streamer_inst = mock_streamer_cls.return_value
            processor_inst = mock_processor_cls.return_value
            gateway_inst = mock_gateway_cls.return_value

            streamer_inst.read_from_source.return_value = raw_telemetry_data
            processor_inst.process_batch.return_value = processed_data

            # Вызов основного метода композиции (предполагаемое имя метода в модуле)
            thp.run_telemetry_health_pipeline(
                source_path=source_path,
                module_name=module_name,
                report_path=report_path,
                dashboard_path=dashboard_path,
                audit_summary=audit_summary,
                metrics=metrics
            )

            # Проверка вызовов: Данные должны передаваться по цепочке
            streamer_inst.read_from_source.assert_called_once_with(source_path)
            processor_inst.process_batch.assert_called_once_with(raw_telemetry_data)

            # Проверка финального звена - Gateway
            # Сигнатура: execute_monitoring_and_reporting_pipeline(self, module_name, incident_data, audit_summary, metrics,
            # dashboard_format, incidents_list, patches_list, report_path, dashboard_path)
            gateway_inst.execute_monitoring_and_reporting_pipeline.assert_called_once()

            args, kwargs = gateway_inst.execute_monitoring_and_reporting_pipeline.call_args

            # Смысловые ассерты на соответствие переданных данных
            self.assertEqual(kwargs.get('module_name'), module_name)
            self.assertEqual(kwargs.get('incidents_list'), processed_data)
            self.assertEqual(kwargs.get('report_path'), report_path)
            self.assertEqual(kwargs.get('dashboard_path'), dashboard_path)
            self.assertEqual(kwargs.get('audit_summary'), audit_summary)
            self.assertEqual(kwargs.get('metrics'), metrics)

    def test_gateway_stream_parsing_with_random_bytes(self):
        """Проверка парсинга потока данных через BytesIO с мусорным наполнением."""

        random_payload = f"RAW_STREAM_{self.rand_hex()}_{self.rand_str()}".encode('utf-8')
        mock_stream = io.BytesIO(random_payload)
        stream_path = self.rand_path("stream")

        with patch('skills.telemetry_health_pipeline.SystemHealthMonitoringGateway') as mock_gateway_cls:
            gateway_inst = mock_gateway_cls.return_value

            # Имитируем логику парсера: он должен вернуть структуру, содержащую наш случайный payload
            expected_struct = {"raw_content": random_payload.decode('utf-8'), "size": len(random_payload)}
            gateway_inst.parse_gateway_stream_data.return_value = expected_struct

            # Выполняем метод
            result = gateway_inst.parse_gateway_stream_data(mock_stream)

            # Проверяем, что парсер вызывался именно с нашим BytesIO объектом
            gateway_inst.parse_gateway_stream_data.assert_called_once_with(mock_stream)
            self.assertEqual(result["raw_content"], random_payload.decode('utf-8'))

    def test_incident_registration_during_processing(self):
        """Проверка регистрации инцидента при обнаружении аномалии в процессоре."""

        anomaly_packet = {
            "type": "ANOMALY",
            "severity": random.choice(["CRITICAL", "WARNING"]),
            "trace_id": self.rand_hex()
        }

        with patch('skills.telemetry_health_pipeline.IncidentAggregator') as mock_agg_cls:
            agg_inst = mock_agg_cls.return_value

            # Создаем процессор и имитируем обнаружение инцидента
            from skills.telemetry_health_pipeline import TelemetryProcessor
            processor = TelemetryProcessor()

            # Внедряем мок агрегатора в процессор (если он используется как зависимость)
            with patch.object(processor, 'process_and_dispatch') as mock_dispatch:
                processor.process_and_dispatch(anomaly_packet)

                # Проверяем, что диспетчер вызван с нашими случайными данными
                mock_dispatch.assert_called_once_with(anomaly_packet)

    def test_telemetry_streamer_push_logic(self):
        """Проверка корректности проталкивания данных стримером."""

        test_payload = {"telemetry_node": self.rand_str(), "value": random.randint(0, 1000)}

        with patch('skills.telemetry_health_pipeline.TelemetryStreamer') as mock_streamer_cls:
            streamer_inst = mock_streamer_cls.return_value

            # Вызов метода
            streamer_inst.push_telemetry(test_payload)

            # Проверка, что метод push получил именно наш сгенерированный словарь
            streamer_inst.push_telemetry.assert_called_with(test_payload)

    def test_pipeline_error_recovery_flow(self):
        """Проверка устойчивости конвейера при пустых данных из источника."""

        with patch('skills.telemetry_health_pipeline.TelemetryStreamer') as mock_streamer_cls, \
             patch('skills.telemetry_health_pipeline.TelemetryProcessor') as mock_processor_cls:

            streamer_inst = mock_streamer_cls.return_value
            processor_inst = mock_processor_cls.return_value

            # Стример возвращает пустой список (имитация сбоя или отсутствия данных)
            streamer_inst.read_from_source.return_value = []

            # Запуск
            thp.run_telemetry_health_pipeline(
                source_path=self.rand_path("empty"),
                module_name=self.rand_str(),
                report_path=self.rand_path("rep"),
                dashboard_path=self.rand_path("dash")
            )

            # Процессор должен получить пустой список и вернуть пустой список, не упав
            processor_inst.process_batch.assert_called_once_with([])

if __name__ == '__main__':
    unittest.main()