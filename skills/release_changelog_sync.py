import requests


class ReleaseChangelogSync:
    def __init__(self, repo_sync=None, release_notes_publisher=None):
        self.repo_sync = repo_sync
        self.release_notes_publisher = release_notes_publisher

    def sync_changelog(self, repo_path, changelog_content, external_system_url):
        if not repo_path or not changelog_content:
            raise ValueError("Invalid parameters")

        if self.repo_sync and hasattr(self.repo_sync, 'push'):
            self.repo_sync.push(repo_path)

        if self.release_notes_publisher and hasattr(self.release_notes_publisher, 'publish'):
            self.release_notes_publisher.publish(changelog_content)

        response = requests.post(
            external_system_url,
            json={"changelog": changelog_content, "repo_path": repo_path}
        )

        data = response.json()
        
        if "sync_id" in data:
            return data["sync_id"]
        
        return True


def sync_release_changelog(payload):
    version = payload.get("version")
    notes = payload.get("notes")
    sync_id = payload.get("sync_id", "")

    return {
        "status": "synced",
        "version": version,
        "sync_id": sync_id,
        "notes": notes
    }