import json
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser, LessonParserError


class HypothesisGeneratorError(Exception):
    pass


class HypothesisGenerator:
    def __init__(self, lesson_parser=None, git_inspector=None, repo_path=None):
        if git_inspector is not None:
            self.git_inspector = git_inspector
        elif repo_path is not None:
            self.git_inspector = GitInspector(repo_path)
        else:
            self.git_inspector = None

        if lesson_parser is not None:
            self.lesson_parser = lesson_parser
        elif self.git_inspector is not None:
            self.lesson_parser = LessonParser(self.git_inspector)
        elif repo_path is not None:
            self.lesson_parser = LessonParser(GitInspector(repo_path))
        else:
            self.lesson_parser = None

    def _normalize_lesson(self, lesson):
        if not isinstance(lesson, dict):
            return None

        norm = dict(lesson)

        text_sources = [
            norm.get("content"),
            norm.get("description"),
            norm.get("message"),
        ]
        text = "\n".join([str(s) for s in text_sources if s])

        if text:
            for line in text.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip().lower()
                    val = val.strip()
                    if not val:
                        continue
                    if key in ("failure_signature", "pattern_id", "failure_pattern", "pattern") and not norm.get("failure_signature"):
                        norm["failure_signature"] = val
                    elif key == "component" and not norm.get("component"):
                        norm["component"] = val
                    elif key in ("root_cause", "cause") and not norm.get("root_cause"):
                        norm["root_cause"] = val
                    elif key in ("lesson", "fix", "action") and not norm.get("lesson"):
                        norm["lesson"] = val

        has_lesson_meta = any([
            norm.get("failure_signature"),
            norm.get("pattern_id"),
            norm.get("failure_pattern"),
            norm.get("pattern"),
            norm.get("id"),
            norm.get("error_message"),
            norm.get("component"),
            norm.get("root_cause"),
            norm.get("lesson"),
            norm.get("fix"),
            norm.get("action"),
        ])

        if not has_lesson_meta:
            return None

        return norm

    def _get_lessons(self, lessons=None, max_commits=None):
        if lessons is not None:
            raw_lessons = lessons
        elif self.lesson_parser is not None:
            try:
                if hasattr(self.lesson_parser, "extract_lessons"):
                    if max_commits is not None:
                        raw_lessons = self.lesson_parser.extract_lessons(max_commits)
                    else:
                        raw_lessons = self.lesson_parser.extract_lessons()
                elif hasattr(self.lesson_parser, "parse_lessons"):
                    raw_lessons = self.lesson_parser.parse_lessons()
                else:
                    raw_lessons = []
            except LessonParserError as e:
                raise HypothesisGeneratorError(str(e)) from e
        else:
            raw_lessons = []

        normalized_lessons = []
        for item in raw_lessons:
            norm = self._normalize_lesson(item)
            if norm is not None:
                normalized_lessons.append(norm)

        return normalized_lessons

    def analyze_failure_patterns(self, lessons=None):
        items = self._get_lessons(lessons)
        patterns = {}
        for lesson in items:
            sig = (
                lesson.get("failure_signature")
                or lesson.get("pattern_id")
                or lesson.get("failure_pattern")
                or lesson.get("pattern")
                or lesson.get("id")
                or "unknown_signature"
            )

            comp = lesson.get("component") or "unknown_component"

            if sig not in patterns:
                patterns[sig] = {
                    "pattern_id": sig,
                    "component": comp,
                    "count": 0,
                    "lessons": [],
                    "root_causes": [],
                }
            patterns[sig]["count"] += 1
            patterns[sig]["lessons"].append(lesson)
            root_cause = lesson.get("root_cause")
            if root_cause:
                patterns[sig]["root_causes"].append(root_cause)

        return patterns

    def generate_hypotheses(self, lessons=None):
        items = self._get_lessons(lessons)
        if not items:
            return []

        patterns = self.analyze_failure_patterns(items)
        if not patterns:
            return []

        total_occurrences = sum(p["count"] for p in patterns.values()) or 1
        hypotheses = []

        for sig, data in patterns.items():
            count = data["count"]
            confidence = round(count / total_occurrences, 4)
            description = (
                f"Failure pattern '{sig}' detected {count} time(s) "
                f"in component '{data['component']}'."
            )
            hypotheses.append({
                "pattern_id": sig,
                "description": description,
                "confidence": confidence,
                "count": count,
                "component": data["component"],
                "root_causes": data["root_causes"],
            })

        hypotheses.sort(key=lambda h: (h["confidence"], h["count"]), reverse=True)
        return hypotheses

    def generate_recommendations(self, lessons=None):
        items = self._get_lessons(lessons)
        recommendations = []
        for lesson in items:
            sig = lesson.get("failure_signature") or ""
            comp = lesson.get("component") or ""
            root_cause = lesson.get("root_cause") or ""
            lesson_text = lesson.get("lesson") or ""

            rec = (
                f"Address failure signature [{sig}] in component [{comp}]. "
                f"Root cause: {root_cause}. Action: {lesson_text}"
            )
            recommendations.append(rec)
        return recommendations

    def run_cycle_analysis(self, max_commits=None):
        lessons = self._get_lessons(max_commits=max_commits)

        patterns = self.analyze_failure_patterns(lessons)
        hypotheses = self.generate_hypotheses(lessons)
        recommendations = self.generate_recommendations(lessons)

        return {
            "patterns": patterns,
            "hypotheses": hypotheses,
            "recommendations": recommendations,
        }

    def load_metrics_stream(self, stream):
        data = stream.read()
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)

    def enrich_failure_context(self, commit_hash):
        context = {"commit_hash": commit_hash}
        if self.git_inspector is not None and hasattr(self.git_inspector, "get_file_diff"):
            context["diff"] = self.git_inspector.get_file_diff(commit_hash)
        return context