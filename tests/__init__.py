import sys
import os

skills_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if skills_path not in sys.path:
    sys.path.insert(0, skills_path)
