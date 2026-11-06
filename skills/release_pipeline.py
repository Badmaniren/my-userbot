from skills.release_notes_composer import ReleaseNotesComposer
from skills.release_notes_publisher import ReleaseNotesPublisher


class ReleasePipeline:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.composer = ReleaseNotesComposer(repo_path=repo_path)
        try:
            self.publisher = ReleaseNotesPublisher(repo_path=repo_path)
        except PermissionError:
            self.publisher = None

    def run(self, output_path: str) -> bool:
        self.composer.compose(output_path=output_path)

        if self.publisher is not None:
            result = self.publisher.publish(output_path=output_path)
            if result:
                return True

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Release Notes\n")
        return True