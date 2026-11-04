from skills.release_notes_composer import ReleaseNotesComposer
from skills.repo_notifier import RepoNotifier


class ReleaseNotesPublisher:
    """Модуль публикации релизных заметок, комбинирующий генератор релизных заметок

    и репо-нотификатор для рассылки дайджестов.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.composer = ReleaseNotesComposer(self.repo_path)
        self.notifier = RepoNotifier(self.repo_path)

    def publish(self, output_path: str) -> bool:
        self.composer.compose(output_path)
        return self.notifier.notify(output_path)

    def run(self) -> bool:
        self.composer.run()
        return self.notifier.notify_and_commit()

    def generate_and_notify(self, output_path: str) -> bool:
        self.composer.generate(output_path)
        return self.notifier.notify(output_path)

    def compose_and_notify(self, output_path: str) -> bool:
        return self.publish(output_path)