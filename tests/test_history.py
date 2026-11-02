"""Runs history.py against fake sessions in a temporary HOME, never your real ones."""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest

START = datetime.datetime(2026, 1, 1)
SCRIPT = os.path.join(os.path.dirname(__file__), "..", "skills", "history", "history.py")


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = self.tmp.name
        self.projects = os.path.join(self.home, ".claude", "projects", "demo")
        os.makedirs(self.projects)
        self.data = os.path.join(self.home, ".claude", "history-data")

    def tearDown(self):
        self.tmp.cleanup()

    def write_session(self, session_id, prompts, hour=0):
        cwd = os.path.join(self.home, "code", "demo")
        with open(os.path.join(self.projects, session_id + ".jsonl"), "w") as f:
            for i, text in enumerate(prompts):
                f.write(json.dumps({
                    "type": "user",
                    "cwd": cwd,
                    "timestamp": (START + datetime.timedelta(hours=hour, minutes=i)).isoformat() + "Z",
                    "message": {"content": text},
                }) + "\n")

    def run_script(self, *args):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_HISTORY_DATA"}
        env["HOME"] = self.home
        result = subprocess.run([sys.executable, SCRIPT, *args], env=env,
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def load(self, *parts):
        with open(os.path.join(*parts)) as f:
            return json.load(f)

    def test_scan_redacts_secrets(self):
        self.write_session("s1", [
            "my key is sk-ant-abcdefghijklmnop1234567890",
            "password: hunter2 please log in",
        ])
        self.run_script("scan")
        text = " ".join(self.load(self.data, "pending.json")[0]["prompts"])
        self.assertNotIn("sk-ant-abcdefghijklmnop", text)
        self.assertNotIn("hunter2", text)
        self.assertIn("[redacted]", text)

    def test_scan_caps_at_forty_newest_first(self):
        for n in range(45):
            self.write_session(f"s{n:02d}", [f"task {n}"], hour=n)
        out = self.run_script("scan")
        pending = self.load(self.data, "pending.json")
        self.assertEqual(len(pending), 40)
        self.assertIn("5 more next run", out)
        picked = [int(p["prompts"][0].split()[1]) for p in pending]
        self.assertEqual(picked, list(range(44, 4, -1)))  # the 40 newest, newest first

    def test_add_and_render(self):
        self.write_session("s1", ["fix the login bug"])
        summaries = os.path.join(self.home, "summaries-in.json")
        with open(summaries, "w") as f:
            json.dump({"s1": "Fixed the login bug."}, f)
        self.run_script("add", summaries)
        out_dir = os.path.join(self.home, "site")
        self.run_script("render", out_dir)
        self.assertTrue(os.path.exists(os.path.join(out_dir, "index.html")))
        row = self.load(out_dir, "sessions.json")["sessions"][0]
        self.assertEqual(row["summary"], "Fixed the login bug.")
        self.assertEqual(row["project"], "demo")
        self.assertEqual(row["cwd"], "~/code/demo")
        # once summarized, it is no longer pending
        self.assertIn("0 session(s)", self.run_script("scan"))

    def test_url_roundtrip(self):
        self.assertEqual(self.run_script("url"), "none")
        self.run_script("url", "https://claude.ai/artifact/example")
        self.assertEqual(self.run_script("url"), "https://claude.ai/artifact/example")


if __name__ == "__main__":
    unittest.main()
