import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.release_changelog_integrator import ReleaseChangelogIntegrator

class TestReleaseChangelogIntegrator(unittest.TestCase):

    def setUp(self):
        self.integrator = ReleaseChangelogIntegrator()

    def test_integration_flow_integrity(self):
        # Генерируем хаотичные данные для проверки
        random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        random_changelog_content = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
        random_hub_id = uuid.uuid4().hex
        
        # Инициализируем реальные зависимости (честный импорт)
        # Используем with patch внутри метода для контроля потоков данных
        with patch('skills.release_changelog_integrator.release_notes_composer') as mock_composer, \
             patch('skills.release_changelog_integrator.release_automation_hub') as mock_hub:
            
            mock_composer.compose.return_value = random_changelog_content
            mock_hub.push_release.return_value = random_hub_id
            
            result = self.integrator.integrate(random_version)
            
            # Проверка логики: интегратор должен вернуть ID, полученный от хаба
            self.assertEqual(result, random_hub_id)
            mock_composer.compose.assert_called_once_with(random_version)
            mock_hub.push_release.assert_called_once_with(random_changelog_content)

    def test_changelog_parsing_with_random_payload(self):
        # Генерируем случайный поток байтов для эмуляции чтения файла
        random_data = uuid.uuid4().bytes + b'\n' + uuid.uuid4().hex.encode()
        mock_file_stream = io.BytesIO(random_data)
        
        with patch('builtins.open', return_value=mock_file_stream):
            # Проверяем, что парсер корректно извлекает данные из случайного потока
            parsed_data = self.integrator.parse_changelog_file(f"/{uuid.uuid4().hex}.md")
            
            self.assertIn(random_data.decode(errors='ignore'), parsed_data)

    def test_sync_failure_handling(self):
        # Проверка устойчивости к сбоям при случайных URL
        random_url = f"https://{uuid.uuid4().hex}.com/api/v1/sync"
        
        with patch('skills.release_changelog_integrator.dependency_audit_sync') as mock_sync:
            mock_sync.sync.side_effect = Exception("Connection lost")
            
            # Проверяем, что интегратор корректно пробрасывает или обрабатывает исключение
            with self.assertRaises(Exception):
                self.integrator.sync_with_hub(random_url)
            
            mock_sync.sync.assert_called_once_with(random_url)

    def test_audit_pipeline_execution(self):
        # Проверка передачи случайных параметров в пайплайн аудита
        random_audit_id = uuid.uuid4().hex
        random_threshold = random.random()
        
        with patch('skills.release_changelog_integrator.dependency_audit_pipeline') as mock_pipeline:
            mock_pipeline.run.return_value = True
            
            status = self.integrator.run_audit(random_audit_id, random_threshold)
            
            self.assertTrue(status)
            mock_pipeline.run.assert_called_once_with(
                audit_id=random_audit_id, 
                threshold=random_threshold
            )

    def test_repo_health_integration(self):
        # Проверка взаимодействия с health-системой
        random_repo_name = uuid.uuid4().hex
        random_score = random.randint(0, 100)
        
        with patch('skills.release_changelog_integrator.repo_health_automator') as mock_health:
            mock_health.get_score.return_value = random_score
            
            score = self.integrator.get_repo_health(random_repo_name)
            
            self.assertEqual(score, random_score)
            mock_health.get_score.assert_called_once_with(random_repo_name)

if __name__ == '__main__':
    unittest.main()