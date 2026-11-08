import os
import uuid
import hashlib
import requests
import json

class RepoHealthSecuritySyncer:
    def __init__(self, repo_id=None, health_url=None, security_url=None, target_directory=None):
        self.repo_id = repo_id