import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from abacus_standards import genworkflows
from abacus_standards.common import CANONICAL

JSC = shutil.which("osascript")


def run_js(source):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(source)
    script = ('function run(argv){ var s=$.NSString.stringWithContentsOfFileEncodingError(argv[0],4,null).js; '
              'try { return String(eval(s)) } catch(e) { return "ERROR: "+e } }')
    return subprocess.run(["osascript", "-l", "JavaScript", "-e", script, f.name],
                          capture_output=True, text=True).stdout.strip()


class WorkflowTest(unittest.TestCase):
    def test_generated_files_match_body(self):
        for p in genworkflows.PIPELINES:
            path = CANONICAL / "workflows" / f"abacus-{p}.js"
            self.assertEqual(path.read_text(), genworkflows.render(p),
                             f"{path.name} drifted from _body.js: run `make workflows`")

    def test_meta_is_a_pure_literal_with_matching_name(self):
        for p in genworkflows.PIPELINES:
            text = (CANONICAL / "workflows" / f"abacus-{p}.js").read_text()
            meta = text.split("\n}\n", 1)[0]
            self.assertIn(f"name: 'abacus-{p}'", meta)
            self.assertNotIn("${", meta)

    def test_no_nondeterministic_builtins(self):
        body = (CANONICAL / "workflows" / "_body.js").read_text()
        for bad in ("Date.now(", "Math.random(", "new Date()"):
            self.assertNotIn(bad, body)

    @unittest.skipUnless(JSC, "needs JavaScriptCore via osascript")
    def test_scripts_parse(self):
        for p in genworkflows.PIPELINES:
            text = (CANONICAL / "workflows" / f"abacus-{p}.js").read_text().replace("export const meta", "const meta")
            out = run_js(f"new Function({text!r}.replace(/^/, '(async function(){{').concat('\\n}})')); 'ok'")
            self.assertEqual(out, "ok", f"abacus-{p}.js: {out}")

    @unittest.skipUnless(JSC, "needs JavaScriptCore via osascript")
    def test_verdicts_align_by_index_and_restore_verbatim_text(self):
        import json
        body = (CANONICAL / "workflows" / "_body.js").read_text()
        fn = re.search(r"function alignVerdicts\(acceptance, verdicts\) \{.*?\n\}", body, re.S).group(0)
        acc = ["`make gate` passes", "README lists word_count", "prints 3"]
        verdicts = [{"index": 1, "criterion": "1. make gate passes (paraphrased)", "verdict": "met", "evidence": "ok"},
                    {"index": 9, "criterion": "readme LISTS   word_count", "verdict": "met", "evidence": "README:5"}]
        out = json.loads(run_js(f"{fn}; JSON.stringify(alignVerdicts({json.dumps(acc)}, {json.dumps(verdicts)}))"))
        self.assertEqual(out[0]["criterion"], acc[0])   # matched by index, verbatim text restored
        self.assertEqual(out[1]["criterion"], acc[1])   # matched by normalized text
        self.assertIsNone(out[2])                       # genuinely unjudged

    @unittest.skipUnless(JSC, "needs JavaScriptCore via osascript")
    def test_emit_trigger_precedence_table(self):
        body = (CANONICAL / "workflows" / "_body.js").read_text()
        fn = re.search(r"function emitTrigger\(s\) \{.*?\n\}", body, re.S).group(0)
        table = [
            ({}, ""),
            ({"manual": True}, "manual"),
            ({"escalated": True, "manual": True}, "escalation"),
            ({"gateRedOnMain": True, "escalated": True}, "gate-red-on-main"),
            ({"capReached": True, "recheckGreen": False, "gateRedOnMain": True}, "fix-loop-cap"),
            ({"capReached": True, "recheckGreen": True}, ""),  # cap reached but recheck green: no trigger
            ({"intractable": True, "capReached": True, "escalated": True}, "intractable"),
        ]
        import json
        cases = json.dumps([c for c, _ in table])
        out = run_js(f"{fn}; JSON.stringify({cases}.map(emitTrigger))")
        self.assertEqual(json.loads(out), [want for _, want in table])


if __name__ == "__main__":
    unittest.main()


class CrossRepoCriteriaGuidanceTest(unittest.TestCase):
    """i3p: filing keeps cross-repository conditions out of worker criteria (no sandbox change needed)."""

    def test_bead_file_says_criteria_check_this_repository_only(self):
        text = (Path(__file__).resolve().parents[1] / "canonical" / "skills" / "bead-file" / "SKILL.md").read_text()
        self.assertIn("Criteria check this repository only", text)
        self.assertIn("WAITS-ON <repo>:<bead>", text)


class WorkerRefusalGuidanceTest(unittest.TestCase):
    """Heartbeat run 2: a refused sibling read led a worker to try zlib on raw git objects, then absolute paths."""

    def test_worker_reports_blocked_instead_of_routing_around(self):
        text = (Path(__file__).resolve().parents[1] / "canonical" / "skills" / "abacus-worker" / "SKILL.md").read_text()
        self.assertIn("Never reach the other repository another way", text)
        self.assertIn("Work around a refusal", text)
