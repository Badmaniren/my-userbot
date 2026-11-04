import os
import zipfile
from skills.repo_tagger import RepoTagger
from skills.repo_ci_pipeline import RepoCIPipeline


class RepoReleaseExporter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.tagger = RepoTagger(self.repo_path)
        self.pipeline = RepoCIPipeline(self.repo_path)

    def export_release(self, tag=None, dest_path=None):
        if tag is None:
            tag = self.tagger.determine_next_version()

        pipeline_success = self.pipeline.run_pipeline()
        if not pipeline_success:
            return False

        if tag:
            self.tagger.apply_and_push_tag(tag)

        archive_path = self._package_artifacts(tag)

        if dest_path is not None:
            os.makedirs(dest_path, exist_ok=True)
            if archive_path and os.path.exists(archive_path):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(dest_path)
                return True
            return False

        return archive_path

    def batch_export_from_stream(self, stream):
        return self.pipeline.process_audit_stream(stream)

    def _package_artifacts(self, target_tag: str) -> str:
        safe_tag_name = target_tag.replace('/', '_')
        zip_name = f"release_{safe_tag_name}.zip"
        zip_path = os.path.join(self.repo_path, zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.repo_path):
                if '.git' in root:
                    continue
                for file in files:
                    if file == zip_name:
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.repo_path)
                    zipf.write(full_path, rel_path)

        return zip_path