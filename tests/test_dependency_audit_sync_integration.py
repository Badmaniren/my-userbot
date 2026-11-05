import unittest
import os
import shutil
import uuid
import random
import tempfile
from skills.dependency_audit_sync import DependencyAuditSync
from skills import dependency_audit_aggregator
from skills import repo_sync

class TestDependencyAuditSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, f"repo_{uuid.uuid4().hex}")
        os.makedirs(self.repo_path)
        
        # Инициализация случайных параметров для теста
        self.branch = f"feature/{uuid.uuid4().hex[:8]}"
        self.stream_source = f"https://registry.example.org/{random.randint(1000, 9999)}"
        self.report_name = f"audit_report_{uuid.uuid4().hex[:6]}.json"
        self.cve_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        self.target_version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        self.sync_module = DependencyAuditSync(self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_audit_and_sync_cycle(self):
        # 1. Запуск аудита через агрегатор (внутри модуля)
        audit_result = dependency_audit_aggregator.start_new(
            self.repo_path, 
            self.branch, 
            self.stream_source
        )
        self.assertIsNotNone(audit_result, "Агрегатор не вернул результат аудита")

        # 2. Выполнение синхронизации через repo_sync
        sync_engine = repo_sync.RepoSync(self.repo_path)
        sync_status = sync_engine.synchronize()
        self.assertTrue(sync_status, "Синхронизация репозитория завершилась с ошибкой")

        # 3. Вызов целевого модуля для комбинированной операции
        # Проверяем, что модуль корректно использует оба навыка
        final_status = self.sync_module.run_audit_and_sync(
            self.report_name, 
            self.cve_id, 
            self.target_version
        )
        
        self.assertTrue(final_status, "Модуль DependencyAuditSync не смог завершить цикл")

        # 4. Проверка реальных изменений (наличие отчета)
        report_path = os.path.join(self.repo_path, self.report_name)
        self.assertTrue(os.path.exists(report_path), "Отчет аудита не был создан в файловой системе")

        # 5. Проверка логирования через repo_sync.RepoLogger
        logger = repo_sync.RepoLogger(self.repo_path)
        log_success = logger.log_event("INTEGRATION_TEST_SUCCESS", {"uuid": str(uuid.uuid4())})
        self.assertTrue(log_success, "Не удалось записать лог события после интеграции")

    def test_repo_monitor_status_after_sync(self):
        # Проверка состояния репозитория после интеграции
        monitor = repo_sync.RepoMonitor(self.repo_path)
        status = monitor.check_status()
        self.assertIsInstance(status, str)
        self.assertNotEqual(status, "", "Статус репозитория пуст после синхронизации")

if __name__ == '__main__':
    unittest.main()