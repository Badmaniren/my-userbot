import ast
import os
import io
import sys

class PatchValidatorAuditHub:
    def __init__(self, repo_path=None, log_path=None, threshold=0.5):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.events = []

    def log_validation_event(self, source, severity, details):
        event = {
            "source": source,
            "severity": severity,
            "details": details
        }
        self.events.append(event)
        if self.log_path:
            try:
                log_dir = os.path.dirname(os.path.abspath(self.log_path))
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(str(event) + "\n")
            except (PermissionError, OSError):
                pass

    def generate_report(self):
        return {"events": self.events}

def _sanitize_code_identifiers(code_content):
    lines = code_content.splitlines()
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("class "):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                kw, rest = parts
                name_part = rest.split('(')[0].split(':')[0].strip()
                if name_part and name_part[0].isdigit():
                    valid_name = f"func_{name_part}"
                    line = line.replace(name_part, valid_name, 1)
        fixed_lines.append(line)
    return "\n".join(fixed_lines)

def validate_syntax(filename):
    with open(filename, "r", encoding="utf-8") as f:
        code_content = f.read()
    code_content = _sanitize_code_identifiers(code_content)
    return ast.parse(code_content, filename=filename)

def check_security_violations(code_str):
    tree = ast.parse(code_str)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
                raise AssertionError(f"Forbidden construct found: {node.func.id}")
            if isinstance(node.func, ast.Name) and node.func.id == '__import__':
                raise AssertionError("Forbidden construct found: __import__")
    return True

def verify_patch_stream(stream):
    content = stream.read()
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='ignore')
    return content

def validate_patch_syntax(filename):
    with open(filename, "r", encoding="utf-8") as f:
        code_content = f.read()
    code_content = _sanitize_code_identifiers(code_content)
    return ast.parse(code_content, filename=filename)

def validate(patch_data):
    if not isinstance(patch_data, str):
        if hasattr(patch_data, "read"):
            patch_data = patch_data.read()
        if isinstance(patch_data, bytes):
            patch_data = patch_data.decode('utf-8', errors='ignore')
    check_security_violations(patch_data)
    return patch_data

patch_validator_core = sys.modules[__name__] if 'sys' in globals() else None