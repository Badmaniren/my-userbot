import unittest
from unittest.mock import MagicMock, patch
import io
import json
import uuid
import random
import string

from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError
from skills.lesson_parser import LessonParserError


class TestHypothesisGenerator(unittest.TestCase):
    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.repo_path = f"/tmp/repo_{self.rand_suffix}"

    def test_init_with_git_inspector(self):
        mock_inspector = MagicMock()
        hg = HypothesisGenerator(git_inspector=mock_inspector)
        self.assertEqual(hg.git_inspector, mock_inspector)
        self.assertIsNotNone(hg.lesson_parser)

    def test_init_with_repo_path(self):
        hg = HypothesisGenerator(repo_path=self.repo_path)
        self.assertIsNotNone(hg.git_inspector)
        self.assertIsNotNone(hg.lesson_parser)

    def test_init_empty(self):
        hg = HypothesisGenerator()
        self.assertIsNone(hg.git_inspector)
        self.assertIsNone(hg.lesson_parser)

    def test_get_lessons_explicit(self):
        hg = HypothesisGenerator()
        sig = f"err_{uuid.uuid4().hex[:6]}"
        lessons = [{"failure_signature": sig}]
        result = hg._get_lessons(lessons=lessons)
        self.assertEqual(result, lessons)

    def test_get_lessons_from_parser_extract(self):
        mock_parser = MagicMock()
        sig = f"sig_{uuid.uuid4().hex[:6]}"
        mock_parser.extract_lessons.return_value = [{"failure_signature": sig}]
        hg = HypothesisGenerator(lesson_parser=mock_parser)

        max_c = random.randint(1, 100)
        res = hg._get_lessons(max_commits=max_c)
        mock_parser.extract_lessons.assert_called_once_with(max_c)
        self.assertEqual(res[0]["failure_signature"], sig)

    def test_get_lessons_from_parser_parse(self):
        mock_parser = MagicMock()
        del mock_parser.extract_lessons
        sig = f"sig_{uuid.uuid4().hex[:6]}"
        mock_parser.parse_lessons.return_value = [{"failure_signature": sig}]
        hg = HypothesisGenerator(lesson_parser=mock_parser)

        res = hg._get_lessons()
        mock_parser.parse_lessons.assert_called_once()
        self.assertEqual(res[0]["failure_signature"], sig)

    def test_parser_exception_handling(self):
        mock_parser = MagicMock()
        mock_parser.extract_lessons.side_effect = LessonParserError(f"Fail_{uuid.uuid4().hex[:6]}")
        hg = HypothesisGenerator(lesson_parser=mock_parser)
        with self.assertRaises(HypothesisGeneratorError):
            hg._get_lessons()

    def test_analyze_failure_patterns_basic(self):
        hg = HypothesisGenerator()
        sig = f"sig_{uuid.uuid4().hex[:6]}"
        comp = f"comp_{uuid.uuid4().hex[:6]}"
        cause = f"cause_{uuid.uuid4().hex[:6]}"

        lessons = [
            {"failure_signature": sig, "component": comp, "root_cause": cause},
            {"failure_signature": sig, "component": comp, "root_cause": cause}
        ]

        patterns = hg.analyze_failure_patterns(lessons)
        self.assertIn(sig, patterns)
        self.assertEqual(patterns[sig]["count"], 2)
        self.assertEqual(patterns[sig]["component"], comp)
        self.assertEqual(len(patterns[sig]["root_causes"]), 2)

    def test_analyze_failure_patterns_fallbacks(self):
        hg = HypothesisGenerator()
        error_msg = f"err_{uuid.uuid4().hex[:6]}"
        lessons = [{"error_message": error_msg}]

        patterns = hg.analyze_failure_patterns(lessons)
        self.assertIn("unknown_signature", patterns)
        self.assertEqual(patterns["unknown_signature"]["component"], "unknown_component")
        self.assertEqual(patterns["unknown_signature"]["count"], 1)

    def test_generate_hypotheses_empty(self):
        hg = HypothesisGenerator()
        self.assertEqual(hg.generate_hypotheses([]), [])

    def test_generate_hypotheses_logic(self):
        hg = HypothesisGenerator()
        sig1 = f"sig_a_{uuid.uuid4().hex[:4]}"
        sig2 = f"sig_b_{uuid.uuid4().hex[:4]}"
        comp = f"comp_{uuid.uuid4().hex[:4]}"

        lessons = [
            {"failure_signature": sig1, "component": comp},
            {"failure_signature": sig1, "component": comp},
            {"failure_signature": sig2, "component": comp}
        ]

        hyps = hg.generate_hypotheses(lessons)
        self.assertEqual(len(hyps), 2)
        self.assertEqual(hyps[0]["pattern_id"], sig1)
        self.assertAlmostEqual(hyps[0]["confidence"], 0.6667, places=3)
        self.assertEqual(hyps[1]["pattern_id"], sig2)
        self.assertAlmostEqual(hyps[1]["confidence"], 0.3333, places=3)

    def test_generate_recommendations(self):
        hg = HypothesisGenerator()
        sig = f"sig_{uuid.uuid4().hex[:4]}"
        comp = f"comp_{uuid.uuid4().hex[:4]}"
        cause = f"cause_{uuid.uuid4().hex[:4]}"
        lesson_text = f"action_{uuid.uuid4().hex[:4]}"

        lessons = [{
            "failure_signature": sig,
            "component": comp,
            "root_cause": cause,
            "lesson": lesson_text
        }]

        recs = hg.generate_recommendations(lessons)
        self.assertEqual(len(recs), 1)
        self.assertIn(sig, recs[0])
        self.assertIn(comp, recs[0])
        self.assertIn(cause, recs[0])
        self.assertIn(lesson_text, recs[0])

    def test_run_cycle_analysis(self):
        mock_parser = MagicMock()
        sig = f"sig_{uuid.uuid4().hex[:4]}"
        mock_parser.extract_lessons.return_value = [{"failure_signature": sig, "component": "c"}]
        hg = HypothesisGenerator(lesson_parser=mock_parser)

        max_c = random.randint(5, 50)
        res = hg.run_cycle_analysis(max_commits=max_c)

        self.assertIn("patterns", res)
        self.assertIn("hypotheses", res)
        self.assertIn("recommendations", res)
        self.assertIn(sig, res["patterns"])
        self.assertEqual(len(res["hypotheses"]), 1)
        self.assertEqual(len(res["recommendations"]), 1)

    def test_run_cycle_analysis_exception(self):
        mock_parser = MagicMock()
        mock_parser.extract_lessons.side_effect = LessonParserError("err")
        hg = HypothesisGenerator(lesson_parser=mock_parser)
        with self.assertRaises(HypothesisGeneratorError):
            hg.run_cycle_analysis()

    def test_load_metrics_stream(self):
        hg = HypothesisGenerator()
        key = f"key_{uuid.uuid4().hex[:6]}"
        val = random.randint(1, 1000)
        payload = json.dumps({key: val})

        stream = io.BytesIO(payload.encode("utf-8"))
        data = hg.load_metrics_stream(stream)
        self.assertEqual(data[key], val)

    def test_enrich_failure_context(self):
        mock_inspector = MagicMock()
        commit = uuid.uuid4().hex
        diff_text = f"diff_{uuid.uuid4().hex[:8]}"
        mock_inspector.get_file_diff.return_value = diff_text

        hg = HypothesisGenerator(git_inspector=mock_inspector)
        ctx = hg.enrich_failure_context(commit)

        self.assertEqual(ctx["commit_hash"], commit)
        self.assertEqual(ctx["diff"], diff_text)
        mock_inspector.get_file_diff.assert_called_once_with(commit)

    def test_enrich_failure_context_no_inspector(self):
        hg = HypothesisGenerator()
        commit = uuid.uuid4().hex
        ctx = hg.enrich_failure_context(commit)
        self.assertEqual(ctx, {"commit_hash": commit})


class TestHypothesisGeneratorIntegration(unittest.TestCase):
    def test_generate_hypotheses_from_failure_patterns(self):
        hg = HypothesisGenerator()
        sig = f"integration_sig_{uuid.uuid4().hex[:8]}"
        comp = f"integration_comp_{uuid.uuid4().hex[:8]}"
        cause = f"integration_cause_{uuid.uuid4().hex[:8]}"

        lessons = [
            {
                "failure_signature": sig,
                "component": comp,
                "root_cause": cause,
                "lesson": "Do not fail"
            },
            {
                "failure_signature": sig,
                "component": comp,
                "root_cause": cause,
                "lesson": "Really, do not fail"
            }
        ]

        patterns = hg.analyze_failure_patterns(lessons)
        self.assertGreater(len(patterns), 0)

        hypotheses = hg.generate_hypotheses(lessons)
        self.assertGreater(len(hypotheses), 0)
        self.assertEqual(hypotheses[0]["pattern_id"], sig)
        self.assertEqual(hypotheses[0]["count"], 2)
        self.assertEqual(hypotheses[0]["confidence"], 1.0)

        recommendations = hg.generate_recommendations(lessons)
        self.assertEqual(len(recommendations), 2)
        for rec in recommendations:
            self.assertIn(sig, rec)
            self.assertIn(comp, rec)