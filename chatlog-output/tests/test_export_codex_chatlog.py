import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_codex_chatlog.py"


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class ExportCodexChatlogTest(unittest.TestCase):
    def test_list_sessions_shows_matching_current_cwd_session_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cwd = root / "project"
            cwd.mkdir()
            session = root / "sessions" / "2026" / "06" / "13" / "rollout-test.jsonl"
            write_jsonl(
                session,
                [
                    {
                        "timestamp": "2026-06-13T10:00:00.000Z",
                        "type": "session_meta",
                        "payload": {
                            "id": "session-123",
                            "timestamp": "2026-06-13T10:00:00.000Z",
                            "cwd": str(cwd),
                            "cli_version": "test",
                            "model_provider": "openai",
                        },
                    }
                ],
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "list",
                    "--sessions-root",
                    str(root / "sessions"),
                    "--cwd",
                    str(cwd),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("session-123", result.stdout)
            self.assertIn(str(session), result.stdout)

    def test_export_writes_markdown_for_target_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cwd = root / "project"
            out_dir = root / "out"
            cwd.mkdir()
            session = root / "sessions" / "2026" / "06" / "13" / "rollout-test.jsonl"
            write_jsonl(
                session,
                [
                    {
                        "timestamp": "2026-06-13T10:00:00.000Z",
                        "type": "session_meta",
                        "payload": {
                            "id": "session-123",
                            "timestamp": "2026-06-13T10:00:00.000Z",
                            "cwd": str(cwd),
                            "cli_version": "test",
                            "model_provider": "openai",
                        },
                    },
                    {
                        "timestamp": "2026-06-13T10:01:00.000Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "请导出会话"}],
                        },
                    },
                    {
                        "timestamp": "2026-06-13T10:02:00.000Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "已经导出"}],
                        },
                    },
                ],
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "export",
                    "--sessions-root",
                    str(root / "sessions"),
                    "--session-id",
                    "session-123",
                    "--output-dir",
                    str(out_dir),
                    "--include-tools",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            output_path = Path(result.stdout.strip().splitlines()[-1])
            self.assertTrue(output_path.exists())
            text = output_path.read_text(encoding="utf-8")
            self.assertIn("# Codex Chatlog", text)
            self.assertIn("session-123", text)
            self.assertIn("请导出会话", text)
            self.assertIn("已经导出", text)


if __name__ == "__main__":
    unittest.main()
