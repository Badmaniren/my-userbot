import unittest
import uuid
import random
import os
from skills.incident_digest_generator import IncidentDigestGenerator
from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine

class TestIncidentDigestGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.template_engine = NotificationTemplateEngine()
        self.digest_generator = IncidentDigestGenerator(self.aggregator, self.template_engine)

        self.test_module = f"module_{random.randint(1000, 9999)}"
        self.incident_id = str(uuid.uuid4())
        self.exception_msg = f"Critical failure in {self.test_module}"
        self.traceback = "Traceback (most recent call last): File 'main.py', line 1"

    def test_full_digest_generation_cycle(self):
        # 1. Агрегируем инцидент через реальный модуль
        self.aggregator.process_and_aggregate(
            module_name=self.test_module,
            exception=self.exception_msg,
            traceback_str=self.traceback,
            incident_id=self.incident_id
        )

        # 2. Генерируем дайджест, используя композицию навыков
        # Ожидаем, что генератор вызовет агрегатор для получения данных
        # и шаблонизатор для формирования контента
        digest_output = self.digest_generator.generate_digest(
            module_name=self.test_module,
            template_name="incident_summary_template"
        )

        # 3. Проверка: Дайджест не пуст и содержит ID инцидента
        self.assertIsInstance(digest_output, str)
        self.assertIn(self.incident_id, digest_output)
        self.assertIn(self.test_module, digest_output)

    def test_digest_export_to_file(self):
        # Проверка интеграции с файловой системой через шаблонизатор
        file_path = f"digest_{uuid.uuid4()}.txt"

        # Подготовка данных
        context = {
            "incident_id": self.incident_id,
            "module": self.test_module,
            "status": "resolved"
        }

        # Вызов через генератор, который использует template_engine для экспорта
        success = self.digest_generator.export_digest(
            context=context,
            file_path=file_path
        )

        # Проверка: Файл реально создан
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))

        # Чтение и проверка содержимого
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertIn(self.incident_id, content)

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_template_rendering_integration(self):
        # Проверка, что генератор корректно передает данные в движок шаблонов
        raw_data = {"error": self.exception_msg, "id": self.incident_id}

        # Генерация полезной нагрузки через движок
        payload = self.template_engine.generate_notification_payload(
            severity="CRITICAL",
            incident_id=self.incident_id,
            raw_data=raw_data
        )

        # Рендеринг текста
        rendered = self.template_engine.render_text("incident_summary_template", payload)

        self.assertIn("CRITICAL", rendered)
        self.assertIn(self.incident_id, rendered)

if __name__ == '__main__':
    unittest.main()