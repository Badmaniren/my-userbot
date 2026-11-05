from skills import dependency_audit_aggregator
from skills import repo_sync

class DependencyAuditSync:
    """
    Модуль для комбинирования аудита зависимостей и синхронизации репозитория.
    """

    def __init__(self, repo_path):
        self.repo_path = repo_path

    def run_full_cycle(self, branch, stream_source, report_name, cve_id, target_ver):
        """
        Выполняет полный цикл: аудит и синхронизация.
        """
        # Инициализация аудита
        audit_info = dependency_audit_aggregator.start_new(self.repo_path, branch, stream_source)
        if not audit_info:
            return False
        
        # Агрегация данных
        audit_result = dependency_audit_aggregator.aggregate_dependencies(
            self.repo_path, report_name, cve_id, target_ver
        )
        
        # Синхронизация
        sync_engine = repo_sync.RepoSync(self.repo_path)
        return sync_engine.synchronize()

    def get_repo_health(self):
        """
        Возвращает статус здоровья репозитория.
        """
        monitor = repo_sync.RepoMonitor(self.repo_path)
        return monitor.check_status()

    def attempt_commit(self, event_id):
        """
        Попытка фиксации изменений с логированием результата.
        """
        committer = repo_sync.RepoAutoCommitter(self.repo_path)
        success = committer.process_and_commit(event_id)
        
        if not success:
            logger = repo_sync.RepoLogger(self.repo_path)
            logger.log_event("commit_failed", event_id)
            
        return success

    def save_audit_report(self, report_path, content):
        """
        Сохранение отчета аудита.
        """
        reporter = repo_sync.RepoReporter(self.repo_path)
        return reporter.save_report(report_path, content)

    def synchronize_now(self):
        """
        Принудительная синхронизация.
        """
        sync_engine = repo_sync.RepoSync(self.repo_path)
        return sync_engine.synchronize()

    def run_audit_and_sync(self, report_name, cve_id, target_version):
        """
        Метод для интеграционного теста, объединяющий логику.
        """
        # Агрегация
        dependency_audit_aggregator.aggregate_dependencies(
            self.repo_path, report_name, cve_id, target_version
        )
        
        # Синхронизация
        sync_engine = repo_sync.RepoSync(self.repo_path)
        return sync_engine.synchronize()