#!/usr/bin/env python3
"""List and export local Codex session JSONL files as Markdown."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def default_codex_home():
    return Path(sys.argv[0]).expanduser().home() / ".codex"


def default_sessions_root():
    return Path(
        __import__("os").environ.get("CODEX_HOME", str(default_codex_home()))
    ).expanduser() / "sessions"


def iter_jsonl(path):
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def load_meta(path):
    for obj in iter_jsonl(path):
        if obj.get("type") == "session_meta":
            payload = obj.get("payload") or {}
            return {
                "id": payload.get("id", ""),
                "timestamp": payload.get("timestamp") or obj.get("timestamp") or "",
                "cwd": payload.get("cwd", ""),
                "cli_version": payload.get("cli_version", ""),
                "model_provider": payload.get("model_provider", ""),
                "path": str(path),
                "mtime": path.stat().st_mtime,
            }
    return {
        "id": path.stem,
        "timestamp": "",
        "cwd": "",
        "cli_version": "",
        "model_provider": "",
        "path": str(path),
        "mtime": path.stat().st_mtime,
    }


def discover_sessions(sessions_root):
    root = Path(sessions_root).expanduser()
    if not root.exists():
        return []
    sessions = [load_meta(path) for path in root.glob("**/*.jsonl")]
    sessions.sort(key=lambda item: item["mtime"], reverse=True)
    return sessions


def same_cwd(session_cwd, cwd):
    if not session_cwd:
        return False
    try:
        return Path(session_cwd).expanduser().resolve() == Path(cwd).expanduser().resolve()
    except OSError:
        return str(session_cwd) == str(cwd)


def select_session(sessions, session_id=None, cwd=None):
    if session_id:
        for item in sessions:
            if item["id"] == session_id or Path(item["path"]).stem == session_id:
                return item
        raise SystemExit(f"No Codex session found for session id: {session_id}")
    if cwd:
        for item in sessions:
            if same_cwd(item.get("cwd", ""), cwd):
                return item
    if sessions:
        return sessions[0]
    raise SystemExit("No Codex session JSONL files found.")


def markdown_text_from_content(content):
    texts = []
    for item in content or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"input_text", "output_text"}:
            text = item.get("text") or ""
            if text:
                texts.append(text)
    return "\n\n".join(texts).strip()


def compact_output(value, max_chars):
    if value is None:
        return ""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, indent=2)
    value = value.strip()
    if max_chars <= 0 or len(value) <= max_chars:
        return value
    return value[:max_chars] + f"\n\n...[truncated {len(value) - max_chars} chars]"


def parse_timestamp(value):
    if value:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def slugify(value):
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", value).strip("-")
    return slug or "codex"


def build_markdown(session_path, include_tools=False, include_system=False, max_output_chars=5000):
    meta = {}
    sections = []
    call_names = {}
    seen_messages = set()

    for obj in iter_jsonl(session_path):
        typ = obj.get("type")
        payload = obj.get("payload") or {}
        timestamp = obj.get("timestamp") or ""

        if typ == "session_meta":
            meta = payload
            continue

        if typ != "response_item":
            continue

        payload_type = payload.get("type")

        if payload_type == "message":
            role = payload.get("role") or "unknown"
            if role in {"system", "developer"} and not include_system:
                continue
            text = markdown_text_from_content(payload.get("content"))
            if not text:
                continue
            key = (role, text)
            if key in seen_messages:
                continue
            seen_messages.add(key)

            title = {
                "user": "User",
                "assistant": "Codex",
                "developer": "Developer",
                "system": "System",
            }.get(role, role.title())
            phase = payload.get("phase")
            if phase and role == "assistant":
                title += f" ({phase})"
            sections.append((timestamp, title, text, "markdown"))

        elif include_tools and payload_type == "function_call":
            name = payload.get("name") or "tool_call"
            call_id = payload.get("call_id") or ""
            call_names[call_id] = name
            args = payload.get("arguments") or ""
            try:
                text = json.dumps(json.loads(args), ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                text = str(args)
            sections.append((timestamp, f"Tool Call: {name}", text, "json"))

        elif include_tools and payload_type == "function_call_output":
            call_id = payload.get("call_id") or ""
            name = call_names.get(call_id, call_id or "tool")
            text = compact_output(payload.get("output"), max_output_chars)
            sections.append((timestamp, f"Tool Output: {name}", text, "text"))

    session_id = meta.get("id") or Path(session_path).stem
    header = [
        "# Codex Chatlog",
        "",
        f"- Session: `{session_id}`",
        f"- Source JSONL: `{session_path}`",
        f"- CWD: `{meta.get('cwd', '')}`",
        f"- CLI version: `{meta.get('cli_version', '')}`",
        f"- Model provider: `{meta.get('model_provider', '')}`",
        "",
    ]

    body = []
    for timestamp, title, text, kind in sections:
        body.append(f"## {title}")
        if timestamp:
            body.append(f"`{timestamp}`")
        body.append("")
        if kind == "json":
            body.extend(["```json", text, "```"])
        elif kind == "text" and "\n" in text:
            body.extend(["```text", text, "```"])
        else:
            body.append(text)
        body.append("")

    return "\n".join(header + body), meta, len(sections)


def command_list(args):
    sessions = discover_sessions(args.sessions_root)
    if args.cwd:
        sessions = [item for item in sessions if same_cwd(item.get("cwd", ""), args.cwd)]
    sessions = sessions[: args.limit]

    if args.json:
        print(json.dumps(sessions, ensure_ascii=False, indent=2))
        return

    if not sessions:
        print("No matching Codex sessions found.")
        return

    for index, item in enumerate(sessions, 1):
        marker = "*" if index == 1 else " "
        print(f"{marker} {item['id']}")
        print(f"  timestamp: {item.get('timestamp', '')}")
        print(f"  cwd: {item.get('cwd', '')}")
        print(f"  path: {item.get('path', '')}")


def command_export(args):
    sessions = discover_sessions(args.sessions_root)
    selected = select_session(sessions, session_id=args.session_id, cwd=args.cwd)
    session_path = Path(selected["path"])
    markdown, meta, section_count = build_markdown(
        session_path,
        include_tools=args.include_tools,
        include_system=args.include_system,
        max_output_chars=args.max_output_chars,
    )

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    started = parse_timestamp(meta.get("timestamp") or selected.get("timestamp"))
    stamp = started.astimezone().strftime("%Y-%m-%d-%H%M%S")
    cwd_name = slugify(Path(meta.get("cwd") or selected.get("cwd") or "codex").name)
    output_path = output_dir / f"{stamp}-codex-chatlog-{cwd_name}.md"
    output_path.write_text(markdown, encoding="utf-8")

    if args.verbose:
        print(f"session_id={meta.get('id') or selected.get('id')}")
        print(f"sections={section_count}")
    print(output_path)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List Codex session ids")
    list_parser.add_argument("--sessions-root", default=str(default_sessions_root()))
    list_parser.add_argument("--cwd", default=str(Path.cwd()), help="Only show sessions for this cwd")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(func=command_list)

    export_parser = subparsers.add_parser("export", help="Export a Codex session as Markdown")
    export_parser.add_argument("--sessions-root", default=str(default_sessions_root()))
    export_parser.add_argument("--session-id", help="Session id from the list command")
    export_parser.add_argument("--cwd", default=None, help="Export latest session for this cwd when no session id is provided")
    export_parser.add_argument("--output-dir", required=True)
    export_parser.add_argument("--include-tools", action="store_true", help="Include tool calls and tool output")
    export_parser.add_argument("--include-system", action="store_true", help="Include system/developer messages")
    export_parser.add_argument("--max-output-chars", type=int, default=5000)
    export_parser.add_argument("--verbose", action="store_true")
    export_parser.set_defaults(func=command_export)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
