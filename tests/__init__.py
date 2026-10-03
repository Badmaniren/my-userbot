import sys
import os

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)
