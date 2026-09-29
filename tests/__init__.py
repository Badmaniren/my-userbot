# unga tests package
import os
import sys

_skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if _skills_dir not in sys.path:
    sys.path.insert(0, _skills_dir)
