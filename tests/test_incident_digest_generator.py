import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

# Импорт тестируемого класса
from skills.incident_digest_generator import IncidentDigestGenerator

class TestIncidentDigestGenerator(unittest.TestCase):
    def setUp(self):
        self.random_module = f"module_{uuid.uuid4().hex}"
        self.random_template = f"template_{uuid.uuid4().hex}"
        self.random_file_path = f"/{uuid.uuid4().hex}/digest_{uuid.uuid4().hex}.txt"
        
    def generate_random_incidents(self, count=3):
        incidents = []
        for _ in range(count):
            incidents.append({
                "incident_id": f"id_{uuid.uuid4().hex}",
                "exception": f"Exception_{uuid.uuid4().hex}",
                "traceback_str": f"Traceback_{uuid.uuid4().hex}",
                "resolved": random.choice([True, False]),
                "patch_applied": random.choice([True, False])
            })
        return incidents

    def test_generator_initialization(self):
        """Проверка инициализации генератора с дефолтными и кастомными зависимостями."""
        with patch('skills.incident_digest_generator.IncidentAggregator') as mock_agg_class, \
             patch('skills.incident_digest_generator.NotificationTemplateEngine') as mock_engine_class:
            
            mock_agg = mock_agg_class.return_value
            mock_engine = mock_engine_class.return_value
            
            generator = IncidentDigestGenerator()
            self.assertIsNotNone(generator)
            
            custom_agg = MagicMock()
            custom_engine = MagicMock()
            generator_custom = IncidentDigestGenerator(aggregator=custom_agg, template_engine=custom_engine)
            self.assertEqual(generator_custom.aggregator, custom_agg)
            self.assertEqual(generator_custom.template_engine, custom_engine)

    def test_generate_digest_success(self):
        """Проверка успешной генерации дайджеста с агрегацией инцидентов и рендерингом."""
        mock_agg = MagicMock()
        mock_engine = MagicMock()
        
        generator = IncidentDigestGenerator(aggregator=mock_agg, template_engine=mock_engine)
        
        incidents = self.generate_random_incidents(random.randint(2, 5))
        expected_render_output = f"Rendered_Digest_{uuid.uuid4().hex}"
        
        mock_engine.render_template.return_value = expected_render_output
        digest_format = random.choice(['text', 'html'])
        
        result = generator.generate_digest(
            module_name=self.random_module,
            incidents=incidents,
            template_name=self.random_template,
            format=digest_format
        )
        
        # Проверяем, что агрегатор обработал каждый инцидент
        for incident in incidents:
            mock_agg.process_and_aggregate.assert_any_call(
                self.random_module,
                incident["exception"],
                incident["traceback_str"],
                incident["incident_id"]
            )
            
        # Проверяем вызов рендеринга шаблонизатора с правильными параметрами
        mock_engine.render_template.assert_called_once()
        called_args, called_kwargs = mock_engine.render_template.call_args
        
        template_name_passed = called_kwargs.get('template_name') or called_args[0]
        format_passed = called_kwargs.get('format') or called_args[2]
        context_passed = called_kwargs.get('context') or called_args[1]
        
        self.assertEqual(template_name_passed, self.random_template)
        self.assertEqual(format_passed, digest_format)
        self.assertEqual(context_passed['module_name'], self.random_module)
        self.assertEqual(len(context_passed['incidents']), len(incidents))
        self.assertEqual(result, expected_render_output)

    def test_generate_and_export_digest_success(self):
        """Проверка генерации дайджеста и его последующего экспорта в файл."""
        mock_agg = MagicMock()
        mock_engine = MagicMock()
        
        generator = IncidentDigestGenerator(aggregator=mock_agg, template_engine=mock_engine)
        
        incidents = self.generate_random_incidents(1)
        expected_render_output = f"Rendered_Digest_{uuid.uuid4().hex}"
        
        mock_engine.render_template.return_value = expected_render_output
        mock_engine.export_notification_file.return_value = True
        
        digest_format = random.choice(['text', 'html'])
        
        success = generator.generate_and_export_digest(
            module_name=self.random_module,
            incidents=incidents,
            template_name=self.random_template,
            file_path=self.random_file_path,
            format=digest_format
        )
        
        self.assertTrue(success)
        mock_engine.render_template.assert_called_once()
        mock_engine.export_notification_file.assert_called_once()
        
        export_args, export_kwargs = mock_engine.export_notification_file.call_args
        context_passed = export_kwargs.get('context') or export_args[0]
        file_path_passed = export_kwargs.get('file_path') or export_args[1]
        
        self.assertEqual(file_path_passed, self.random_file_path)
        self.assertEqual(context_passed['digest_content'], expected_render_output)

    def test_generate_digest_empty_incidents(self):
        """Проверка генерации дайджеста при пустом списке инцидентов."""
        mock_agg = MagicMock()
        mock_engine = MagicMock()
        
        generator = IncidentDigestGenerator(aggregator=mock_agg, template_engine=mock_engine)
        
        expected_render_output = f"Empty_Digest_{uuid.uuid4().hex}"
        mock_engine.render_template.return_value = expected_render_output
        
        result = generator.generate_digest(
            module_name=self.random_module,
            incidents=[],
            template_name=self.random_template,
            format='text'
        )
        
        mock_agg.process_and_aggregate.assert_not_called()
        mock_engine.render_template.assert_called_once()
        self.assertEqual(result, expected_render_output)

    def test_aggregator_exception_propagation(self):
        """Проверка корректного проброса исключений при сбое агрегации."""
        mock_agg = MagicMock()
        mock_engine = MagicMock()
        
        generator = IncidentDigestGenerator(aggregator=mock_agg, template_engine=mock_engine)
        
        incidents = self.generate_random_incidents(1)
        random_error_msg = f"Aggregator_Failure_{uuid.uuid4().hex}"
        mock_agg.process_and_aggregate.side_effect = Exception(random_error_msg)
        
        with self.assertRaises(Exception) as context:
            generator.generate_digest(
                module_name=self.random_module,
                incidents=incidents,
                template_name=self.random_template,
                format='text'
            )
        self.assertIn(random_error_msg, str(context.exception))

    def test_export_failure_handling(self):
        """Проверка возврата False при неудачном экспорте файла шаблонизатором."""
        mock_agg = MagicMock()
        mock_engine = MagicMock()
        
        generator = IncidentDigestGenerator(aggregator=mock_agg, template_engine=mock_engine)
        
        incidents = self.generate_random_incidents(1)
        mock_engine.render_template.return_value = f"Digest_{uuid.uuid4().hex}"
        mock_engine.export_notification_file.return_value = False
        
        success = generator.generate_and_export_digest(
            module_name=self.random_module,
            incidents=incidents,
            template_name=self.random_template,
            file_path=self.random_file_path,
            format='text'
        )
        
        self.assertFalse(success)

    def test_generate_digest_from_stream(self):
        """Проверка генерации дайджеста на основе входящего потока данных (Stream)."""
        mock_agg = MagicMock()
        mock_engine = MagicMock()
        
        generator = IncidentDigestGenerator(aggregator=mock_agg, template_engine=mock_engine)
        
        # Использование io.BytesIO со случайным мусором для симуляции потока
        random_stream_bytes = f"stream_garbage_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_bytes)
        
        parsed_incidents = self.generate_random_incidents(2)
        parsed_payload = {
            "module_name": self.random_module,
            "incidents": parsed_incidents
        }
        
        mock_engine.parse_stream_data.return_value = parsed_payload
        expected_digest = f"Digest_From_Stream_{uuid.uuid4().hex}"
        mock_engine.render_template.return_value = expected_digest
        
        result = generator.generate_digest_from_stream(
            stream=mock_stream,
            template_name=self.random_template,
            format='html'
        )
        
        mock_engine.parse_stream_data.assert_called_once_with(mock_stream)
        
        # Проверяем, что инциденты из распарсенного потока были агрегированы
        for incident in parsed_incidents:
            mock_agg.process_and_aggregate.assert_any_call(
                self.random_module,
                incident["exception"],
                incident["traceback_str"],
                incident["incident_id"]
            )
            
        self.assertEqual(result, expected_digest)

if __name__ == '__main__':
    unittest.main()