from skills.repo_monitor import RepoMonitor
from skills.repo_summarizer import RepoSummarizer
from skills.git_committer import GitCommitter


class RepoAutoCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.monitor = RepoMonitor(repo_path)
        self.summarizer = RepoSummarizer(repo_path)
        self.committer = GitCommitter(repo_path)

    def run(self) -> bool:
        """
        Проверяет изменения репозитория с помощью RepoMonitor,
        формирует сводку через RepoSummarizer и выполняет коммит через GitCommitter.commit.
        """
        # Проверяем статус изменений через монитор
        changes = self.monitor.check_status()
        if not changes or not str(changes).strip():
            return False

        # Генерируем сводку изменений
        summary = self.summarizer.generate_summary()

        # Выполняем индексацию и коммит изменений через committer.commit
        success = self.committer.commit(summary)
        return bool(success)

    def process_and_commit(self) -> bool:
        # Алиас метода, используемый в интеграционных тестах
        return self.run()