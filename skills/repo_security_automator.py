from skills.repo_security_gateway import RepoSecurityGateway
from skills.repo_auto_committer import RepoAutoCommitter


class RepoSecurityAutomator:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.gateway = RepoSecurityGateway(repo_path)
        self.committer = RepoAutoCommitter(repo_path)

    def run(self):
        gateway_res = self.gateway.run()
        committer_res = self.committer.run()
        if isinstance(gateway_res, dict):
            res = dict(gateway_res)
            res["committer"] = committer_res
            return res
        return {"gateway": gateway_res, "committer": committer_res}

    def process_stream(self, stream_data=None):
        gateway_res = self.gateway.run()
        if hasattr(self.committer, "process_and_commit"):
            committer_res = self.committer.process_and_commit(stream_data)
        elif hasattr(self.committer, "run"):
            committer_res = self.committer.run()
        else:
            committer_res = None

        if isinstance(gateway_res, dict):
            res = dict(gateway_res)
            res["committer"] = committer_res
            return res
        return {"gateway": gateway_res, "committer": committer_res}