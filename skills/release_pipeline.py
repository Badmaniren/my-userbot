from skills.release_notes_composer import ReleaseNotesComposer
from skills.release_notes_publisher import ReleaseNotesPublisher


class ReleasePipeline:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.composer = ReleaseNotesComposer(repo_path=repo_path)
        self.publisher = ReleaseNotesPublisher(repo_path=repo_path)

    def run(self, output_path: str) -> bool:
        self.composer.compose(output_path=output_path)
        publish_result = self.publisher.publish(output_path=output_path)
        return bool(publish_result)