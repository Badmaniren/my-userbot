# unga package
import os
import sys

skills_dir = os.path.dirname(os.path.abspath(__file__))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)
