import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.system_health_aggregator import SystemHealthAggregator

class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.random_id = uuid.uuid4().hex
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_error = ''.join(random.choices(string.ascii_letters, k=20))

    def test_aggregate_system_health_logic(self):
        """Проверка агрегации метрик: индекс стабильности должен коррелировать с количеством инцидентов."""
        mock_incident_data = {
            "incident_id": self.random_id,
            "severity": random.choice(["CRITICAL", "WARNING", "INFO"]),
            "module": self.random_module
        }
        
        with patch('skills.incident_aggregator.IncidentAggregator.process_and_aggregate') as mock_agg:
            mock_agg.return_value = mock_incident_data
            
            with patch('skills.recovery_dashboard_generator.RecoveryDashboardGenerator.aggregate_system_health') as mock_health:
                expected_score = random.uniform(0.0, 1.0)
                mock_health.return_value = {"stability_index": expected_score, "status": "nominal"}
                
                result = self.aggregator.calculate_health_index(self.random_module)
                
                self.assertEqual(result['stability_index'], expected_score)
                self.assertIn('status', result)
                mock_agg.assert_called_once()

    def test_stream_processing_integrity(self):
        """Проверка обработки потока данных: парсинг случайного байтового мусора."""
        random_stream = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        
        with patch('skills.recovery_dashboard_generator.RecoveryDashboardGenerator.parse_stream_data') as mock_parser:
            expected_dict = {"stream_id": self.random_id, "payload": random.randint(1, 1000)}
            mock_parser.return_value = expected_dict
            
            result = self.aggregator.process_incoming_stream(random_stream)
            
            self.assertEqual(result['stream_id'], self.random_id)
            self.assertEqual(result['payload'], expected_dict['payload'])
            mock_parser.assert_called_with(random_stream)

    def test_comprehensive_report_generation(self):
        """Проверка генерации отчета: интеграция данных аудита и инцидентов."""
        audit_data = {"pkg": "lib-" + self.random_id, "version": "1.0." + str(random.randint(1, 9))}
        
        with patch('skills.recovery_report_exporter.RecoveryReportExporter.generate_comprehensive_report') as mock_report:
            expected_report_str = f"Report-{uuid.uuid4().hex}"
            mock_report.return_value = expected_report_str
            
            result = self.aggregator.generate_full_report(
                self.random_module, 
                self.random_error, 
                self.random_id, 
                audit_data
            )
            
            self.assertEqual(result, expected_report_str)
            mock_report.assert_called_once_with(
                self.random_module, 
                self.random_error, 
                unittest.mock.ANY, 
                self.random_id, 
                audit_data
            )

    def test_notification_dispatch_failure_handling(self):
        """Проверка диспетчеризации: обработка отказа канала уведомлений."""
        random_channel = "channel_" + uuid.uuid4().hex[:5]
        payload = {"msg": uuid.uuid4().hex}
        
        with patch('skills.notification_channel_dispatcher.NotificationChannelDispatcher.dispatch') as mock_dispatch:
            mock_dispatch.return_value = False
            
            status = self.aggregator.notify_stakeholders(random_channel, payload)
            
            self.assertFalse(status)
            mock_dispatch.assert_called_once_with(random_channel, payload)

    def test_patch_scheduler_coordination(self):
        """Проверка координации патчей: передача данных в хаб восстановления."""
        patch_payload = {"diff": uuid.uuid4().hex, "target": self.random_module}
        
        with patch('skills.patch_scheduler.PatchScheduler.coordinate_and_schedule') as mock_coord:
            mock_coord.return_value = True
            
            success = self.aggregator.execute_recovery_sequence(
                self.random_id, 
                patch_payload, 
                MagicMock()
            )
            
            self.assertTrue(success)
            mock_coord.assert_called_once()

if __name__ == '__main__':
    unittest.main()