---
name: chatlog-output
description: Use when Codex needs to export a local Codex CLI/App session transcript, chatlog, conversation log, session JSONL, or Markdown/TXT-style record from ~/.codex/sessions.
---

# Chatlog Output

Export Codex local session JSONL files to readable Markdown. Use the bundled script; do not hand-parse session files unless the script fails and the failure is understood.

## Workflow

1. Ask the user which folder to export into unless they already provided an output directory.
2. Query the current session id by listing recent Codex sessions for the current working directory:

```bash
python3 <skill-dir>/scripts/export_codex_chatlog.py list --cwd "$PWD" --limit 5
```

Treat the first `*` entry as the current or most recent matching session. If the user wants a different session, use the session id they choose from this list.

3. Export the selected session:

```bash
python3 <skill-dir>/scripts/export_codex_chatlog.py export \
  --session-id "<session-id>" \
  --output-dir "<output-folder>" \
  --include-tools \
  --verbose
```

Use `--include-tools` by default for a Claude Code-like operation log. Omit it only when the user asks for a clean transcript containing just user and assistant messages.

## Script Notes

- Codex stores session transcripts under `$CODEX_HOME/sessions`; when `CODEX_HOME` is unset, the script uses `~/.codex/sessions`.
- `list` prints session id, timestamp, cwd, and source JSONL path.
- `export` writes a file named like `YYYY-MM-DD-HHMMSS-codex-chatlog-<cwd>.md` and prints the final path.
- Use `--sessions-root <path>` for nonstandard or archived session directories.
- Use `--include-system` only if the user explicitly asks for system/developer instructions in the export.
