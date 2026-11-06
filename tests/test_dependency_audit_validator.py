import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.dependency_audit_validator import validate_and_apply_audit