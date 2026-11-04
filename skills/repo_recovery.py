from skills.repo_backup import RepoBackup
from skills.repo_logger import RepoLogger


class RepoRecovery:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.backup_handler = RepoBackup(repo_path)
        self.logger_handler = RepoLogger(repo_path)

    def recover_repository(self) -> bool:
        backup_success = self.backup_handler.backup()
        if backup_success:
            self.logger_handler.log_event("RECOVERY", "Repository successfully backed up and recovered")
            return True
        else:
            self.logger_handler.log_error("ERR_RECOVERY", "Failed to backup repository during recovery")
            return False

    def safe_restore(self, stream_data) -> bool:
        backup_created = self.backup_handler.create_backup()
        if backup_created:
            stream_processed = self.logger_handler.process_log_stream(stream_data)
            return stream_processed
        return False