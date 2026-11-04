import os
import re
import ast
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


class DependencyScanner:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def find_dependency_files(self):
        found = []
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file in ("requirements.txt", "setup.py", "pyproject.toml"):
                    found.append(os.path.join(root, file))
        return found

    def normalize_name(self, name: str) -> str:
        return name.lower().replace("_", "-").replace(".", "-")

    def parse_requirements_stream(self, stream):
        if hasattr(stream, "read"):
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
        else:
            content = str(stream)
        
        dependencies = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#")[0].strip()
            if not line:
                continue

            match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", line)
            if match:
                pkg = match.group(1).strip()
                spec = match.group(2).strip()
                if not spec:
                    spec = "*"
                dependencies[pkg] = spec
        return dependencies

    def parse_requirements(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            return self.parse_requirements_stream(f)

    def parse_setup_py(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        dependencies = {}
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "setup":
                    for keyword in node.keywords:
                        if keyword.arg == "install_requires":
                            if isinstance(keyword.value, ast.List):
                                for elt in keyword.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        req_str = elt.value
                                        match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", req_str)
                                        if match:
                                            pkg = match.group(1).strip()
                                            spec = match.group(2).strip()
                                            if not spec:
                                                spec = "*"
                                            dependencies[pkg] = spec
        return dependencies

    def parse_pyproject_toml(self, file_path: str):
        dependencies = {}
        if tomllib is not None:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
            proj = data.get("project", {})
            deps = proj.get("dependencies", [])
            for req_str in deps:
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", req_str)
                if match:
                    pkg = match.group(1).strip()
                    spec = match.group(2).strip()
                    if not spec:
                        spec = "*"
                    dependencies[pkg] = spec
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            in_project = False
            in_deps = False
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("[project]"):
                    in_project = True
                    continue
                elif stripped.startswith("[") and stripped.endswith("]"):
                    in_project = False
                    in_deps = False
                    continue
                
                if in_project:
                    if "dependencies" in stripped and "=" in stripped:
                        in_deps = True
                        if "[" in stripped and "]" in stripped:
                            inner = stripped[stripped.index("[")+1:stripped.rindex("]")]
                            for item in inner.split(","):
                                item = item.strip().strip('"').strip("'")
                                if item:
                                    match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", item)
                                    if match:
                                        pkg = match.group(1).strip()
                                        spec = match.group(2).strip()
                                        if not spec:
                                            spec = "*"
                                        dependencies[pkg] = spec
                            in_deps = False
                        continue
                    elif in_deps:
                        if "]" in stripped:
                            in_deps = False
                        item = stripped.strip(",").strip('"').strip("'").strip()
                        if item:
                            match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", item)
                            if match:
                                pkg = match.group(1).strip()
                                spec = match.group(2).strip()
                                if not spec:
                                    spec = "*"
                                dependencies[pkg] = spec
        return dependencies

    def scan(self):
        aggregated = {}
        files = self.find_dependency_files()
        for file_path in files:
            parsed = {}
            if file_path.endswith("requirements.txt"):
                parsed = self.parse_requirements(file_path)
            elif file_path.endswith("setup.py"):
                parsed = self.parse_setup_py(file_path)
            elif file_path.endswith("pyproject.toml"):
                parsed = self.parse_pyproject_toml(file_path)
            
            for pkg, ver in parsed.items():
                norm_pkg = self.normalize_name(pkg)
                aggregated[norm_pkg] = ver
        return aggregated

    def parse_dependencies(self):
        return self.scan()

    def detect_dependencies(self):
        return self.scan()

    def run(self):
        return self.scan()

    def process_dependencies(self):
        return self.scan()

    def __call__(self):
        return self.scan()