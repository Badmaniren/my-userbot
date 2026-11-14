from skills.repo_health_incident_tracker import RepoHealthIncidentTracker
from skills.repo_health_restorer import RepoHealthRestorer


class RepoIncidentResolver:
    def __init__(self, repo_path=None, tracker=None, restorer=None):
        self.repo_path = repo_path
        self.tracker = tracker if tracker is not None else RepoHealthIncidentTracker()
        self.restorer_factory = restorer

    def _get_restorer(self, repo_path):
        if self.restorer_factory is not None:
            return self.restorer_factory
        return RepoHealthRestorer(repo_path=repo_path)

    def resolve_incident(
        self,
        incident_id,
        repo_path=None,
        resolver=None,
        resolution_notes=None
    ):
        path = repo_path or self.repo_path
        restorer = self._get_restorer(path)

        try:
            routine_success = restorer.execute_restoration_routine()
            if routine_success is False:
                try:
                    restorer.restore_and_protect(repo_path=path)
                except TypeError:
                    restorer.restore_and_protect()
                return {
                    "success": False,
                    "incident_id": incident_id,
                    "error": "Restoration routine failed"
                }

            try:
                restoration_metrics = restorer.restore_and_protect(repo_path=path)
            except TypeError:
                restoration_metrics = restorer.restore_and_protect()

            resolve_kwargs = {"incident_id": incident_id}
            if resolver is not None:
                resolve_kwargs["resolver"] = resolver
            if resolution_notes is not None:
                resolve_kwargs["resolution_notes"] = resolution_notes

            tracker_result = self.tracker.resolve_incident(**resolve_kwargs)

            return {
                "success": True,
                "incident_id": incident_id,
                "restoration_metrics": restoration_metrics,
                "tracker_result": tracker_result
            }
        except Exception as e:
            return {
                "success": False,
                "incident_id": incident_id,
                "error": str(e)
            }

    def resolve_with_stream(
        self,
        incident_id,
        repo_path=None,
        stream=None,
        resolver=None,
        resolution_notes=None
    ):
        path = repo_path or self.repo_path
        restorer = self._get_restorer(path)

        try:
            restore_details = restorer.comprehensive_health_restoration(stream)

            resolve_kwargs = {"incident_id": incident_id}
            if resolver is not None:
                resolve_kwargs["resolver"] = resolver
            if resolution_notes is not None:
                resolve_kwargs["resolution_notes"] = resolution_notes

            tracker_result = self.tracker.resolve_incident(**resolve_kwargs)

            return {
                "success": True,
                "incident_id": incident_id,
                "restoration_result": restore_details,
                "tracker_result": tracker_result
            }
        except Exception as e:
            return {
                "success": False,
                "incident_id": incident_id,
                "error": str(e)
            }

    def resolve_repo_incidents(
        self,
        repo_id,
        repo_path=None,
        resolver=None,
        resolution_notes=None
    ):
        path = repo_path or self.repo_path
        incidents = self.tracker.list_incidents_by_repo(repo_id)
        if not incidents:
            return {
                "total_resolved": 0,
                "resolved_incidents": []
            }

        resolved_incidents = []
        for incident in incidents:
            status = str(incident.get("status", "")).upper()
            if status in ("OPEN", "INVESTIGATING", "PENDING", ""):
                inc_id = incident.get("id") or incident.get("incident_id")
                if inc_id:
                    res = self.resolve_incident(
                        incident_id=inc_id,
                        repo_path=path,
                        resolver=resolver,
                        resolution_notes=resolution_notes
                    )
                    if res.get("success", False):
                        resolved_incidents.append(inc_id)

        return {
            "total_resolved": len(resolved_incidents),
            "resolved_incidents": resolved_incidents
        }

    def resolve_all_for_repo(
        self,
        repo_id,
        repo_path=None,
        resolver=None,
        resolution_notes=None
    ):
        summary = self.resolve_repo_incidents(
            repo_id=repo_id,
            repo_path=repo_path,
            resolver=resolver,
            resolution_notes=resolution_notes
        )
        return summary.get("resolved_incidents", [])