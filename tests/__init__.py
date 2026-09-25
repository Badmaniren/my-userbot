# unga tests package
import sys
import os

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
skills_dir = os.path.join(repo_root, "skills")
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)
