import io
import re

try:
    from packaging.requirements import Requirement
except ImportError:
    Requirement = None

class _FallbackRequirement:
    def __init__(self, requirement_string: str):
        self.raw = requirement_string
        req_str = requirement_string.strip()

        if ';' in req_str:
            req_part, marker_part = req_str.split(';', 1)
            self.marker = marker_part.strip()
        else:
            req_part = req_str
            self.marker = None

        extras_match = re.search(r'\[([^\]]+)\]', req_part)
        if extras_match:
            self.extras = set(x.strip() for x in extras_match.group(1).split(',') if x.strip())
            req_part = req_part[:extras_match.start()] + req_part[extras_match.end():]
        else:
            self.extras = set()

        name_match = re.match(r'^\s*([a-zA-Z0-9_\-\.]+)', req_part)
        if name_match:
            self.name = name_match.group(1)
            spec_part = req_part[name_match.end():].strip()
        else:
            self.name = req_part.strip()
            spec_part = ''

        if spec_part.startswith('(') and spec_part.endswith(')'):
            spec_part = spec_part[1:-1].strip()
        self.specifier = spec_part

class DependencyParser:
    def parse(self, requirement_string: str) -> dict:
        req_cls = Requirement if Requirement is not None else _FallbackRequirement
        req = req_cls(requirement_string)

        extras_list = list(req.extras) if req.extras else []
        marker_str = str(req.marker) if req.marker else None

        if marker_str:
            extra_match = re.search(r"extra\s*==\s*['\"]([^'\"]+)['\"]", marker_str)
            if extra_match:
                ext_val = extra_match.group(1)
                if ext_val not in extras_list:
                    extras_list.append(ext_val)

        result = {
            "name": req.name,
            "specifiers": str(req.specifier),
            "extras": extras_list,
            "marker": marker_str
        }
        return result

    def parse_stream(self, stream: io.BytesIO) -> list:
        content = stream.read().decode('utf-8')
        lines = content.splitlines()
        parsed_items = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                parsed_items.append(self.parse(line))
        return parsed_items

    def build_graph(self, dep_list: list) -> dict:
        graph = {}
        for dep in dep_list:
            parsed = self.parse(dep)
            graph[parsed["name"]] = parsed
        return graph

def parse_requires_dist(requirement_string: str) -> dict:
    parser = DependencyParser()
    return parser.parse(requirement_string)

def parse_dependencies(raw_requires: list) -> list:
    parser = DependencyParser()
    return [parser.parse(req) for req in raw_requires]
