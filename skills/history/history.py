#!/usr/bin/env python3
"""Index local Claude Code sessions for the /history page.

  history.py scan            -> writes pending.json: digests of sessions that need a summary
  history.py add FILE        -> merges {"<session id>": "<summary>", ...} into summaries.json
  history.py render DIR      -> writes the page (index.html + sessions.json) into DIR, ready to publish
  history.py url [URL]       -> prints the saved page URL, or saves URL

Your data (summaries, page URL) lives in ~/.claude/history-data, or $CLAUDE_HISTORY_DATA if set,
so it is never inside the plugin folder and survives plugin updates.
"""
import collections
import datetime
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.expanduser("~/.claude/projects")
HOME = os.path.expanduser("~")
DATA = os.environ.get("CLAUDE_HISTORY_DATA") or os.path.join(HOME, ".claude", "history-data")
SUMMARIES = os.path.join(DATA, "summaries.json")
PENDING = os.path.join(DATA, "pending.json")
URL_FILE = os.path.join(DATA, "url.txt")
PAGE = os.path.join(HERE, "site", "index.html")

# A session is summarized again once it has this many new prompts since its last summary.
RESUMMARIZE_AFTER = 5
# At most this many sessions are summarized per run, newest first; the rest wait for the next run.
SCAN_LIMIT = 40

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b(\s*[:=]\s*|\s+is\s+)\S+"),
    # Long opaque strings with both letters and digits (keys, hashes); paths and URLs keep their slashes.
    re.compile(r"(?<![/\w.-])(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{40,}(?![/\w])"),
]


def redact(text):
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def prompt_text(record):
    content = record.get("message", {}).get("content")
    if isinstance(content, list):
        content = " ".join(
            part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
        )
    if not isinstance(content, str):
        return None
    content = re.sub(r"<pasted_content[^>]*>.*?</pasted_content>", "[pasted text]", content, flags=re.S)
    content = content.strip()
    if not content or content.startswith("<"):
        return None
    return content


def read_session(path):
    session = {
        "id": os.path.basename(path)[:-len(".jsonl")],
        "title": "",
        "cwd": "",
        "branch": "",
        "started": None,
        "last": None,
        "prompts": [],
        "recap": "",
        "paths": [],
    }
    with open(path, errors="ignore") as f:
        for line in f:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("aiTitle"):
                session["title"] = record["aiTitle"]
            stamp = record.get("timestamp")
            if stamp:
                session["started"] = session["started"] or stamp
                session["last"] = stamp
            if record.get("cwd") and not session["cwd"]:
                session["cwd"] = record["cwd"]
            if record.get("gitBranch") and record["gitBranch"] != "HEAD":
                session["branch"] = record["gitBranch"]
            if record.get("type") == "assistant":
                session["paths"].extend(tool_paths(record))
                continue
            if record.get("type") != "user" or record.get("isMeta") or record.get("isSidechain"):
                continue
            text = prompt_text(record)
            if not text:
                continue
            if text.startswith("This session is being continued from a previous conversation"):
                session["recap"] = text
                continue
            session["prompts"].append(text)
    return session


PATH_IN_TEXT = re.compile(r"(?:~|/)[\w.\-/]+")
CD_RELATIVE = re.compile(r"\bcd\s+([\w][\w.\-]*)")
PROJECT_MARKERS = (".git", "package.json", "pyproject.toml", "Package.swift", "Cargo.toml", "go.mod",
                   "pubspec.yaml", "Gemfile", "composer.json", "requirements.txt", "setup.py", "pom.xml",
                   "build.gradle", "wrangler.toml", "config.xml")


def tool_paths(record):
    """File paths an assistant message's tool calls touched (absolute, or relative for `cd x`)."""
    found = []
    for part in record.get("message", {}).get("content") or []:
        if not isinstance(part, dict) or part.get("type") != "tool_use":
            continue
        tool_input = part.get("input") or {}
        for key in ("file_path", "path", "notebook_path"):
            if isinstance(tool_input.get(key), str):
                found.append(tool_input[key])
        command = tool_input.get("command")
        if isinstance(command, str):
            found += PATH_IN_TEXT.findall(command)
            found += ["./" + name for name in CD_RELATIVE.findall(command)]
    return found


def is_project_root(path):
    try:
        names = os.listdir(path)
    except OSError:
        return False
    return any(m in names for m in PROJECT_MARKERS) or any(n.endswith((".xcodeproj", ".xcworkspace")) for n in names)


def infer_project(cwd, paths, prompts):
    """When Claude ran in a folder that holds many projects (e.g. ~/code), find the one the session was about.

    Walks down from cwd while one subfolder holds at least half of the touched paths, and stops at the
    first folder that looks like a project (.git, package.json, ...). Distinctive folder names mentioned
    in the user's prompts count too. Returns None when there's no clear answer.
    """
    if not cwd or is_project_root(cwd):
        return None
    rels = []
    for raw in paths:
        path = os.path.expanduser(raw)
        path = os.path.normpath(os.path.join(cwd, path) if path.startswith("./") else path)
        if path.startswith(cwd + os.sep):
            parts = [p for p in os.path.relpath(path, cwd).split(os.sep) if p]
            if parts and not parts[0].startswith("."):
                rels.append(parts)
    try:
        subdirs = {n for n in os.listdir(cwd) if not n.startswith(".") and os.path.isdir(os.path.join(cwd, n))}
    except OSError:
        subdirs = set()
    text = " ".join(prompts)
    for name in subdirs:
        # Only distinctive names count, so a folder called "real" or "app" doesn't match plain English.
        if re.search(r"[-_\d]|[a-z][A-Z]", name) or len(name) >= 7:
            mentions = len(re.findall(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", text, re.I))
            rels += [[name]] * (2 * min(mentions, 5))
    if len(rels) < 2:
        return None
    prefix = []
    for _ in range(5):
        nexts = collections.Counter(r[len(prefix)] for r in rels if len(r) > len(prefix) and r[:len(prefix)] == prefix)
        if not nexts:
            break
        name, count = nexts.most_common(1)[0]
        if count * 2 < len(rels) or not os.path.isdir(os.path.join(cwd, *prefix, name)):
            break
        prefix.append(name)
        if is_project_root(os.path.join(cwd, *prefix)):
            return name
    return prefix[0] if prefix else None


def project_label(cwd):
    if not cwd:
        return "unknown"
    if os.path.normpath(cwd) == os.path.normpath(HOME):
        return "~"
    return os.path.basename(os.path.normpath(cwd)) or cwd


def all_sessions():
    for path in glob.glob(os.path.join(PROJECTS, "*", "*.jsonl")):
        session = read_session(path)
        if session["prompts"]:
            session["project"] = infer_project(session["cwd"], session["paths"], session["prompts"]) or project_label(session["cwd"])
            yield session


def needs_summary(session, summaries):
    known = summaries.get(session["id"])
    return not known or len(session["prompts"]) - known.get("prompts", 0) >= RESUMMARIZE_AFTER


def digest(session):
    prompts = session["prompts"]
    picked = prompts[:4] + prompts[4:-4][:: max(1, len(prompts[4:-4]) // 4 or 1)][:4] + prompts[-4:]
    seen, sample = set(), []
    for text in picked:
        if text not in seen:
            seen.add(text)
            sample.append(redact(text[:240]))
    return {
        "id": session["id"],
        "title": session["title"],
        "project": session["project"],
        "prompt_count": len(prompts),
        "recap": redact(session["recap"][:1500]),
        "prompts": sample,
    }


def save_json(path, data, **kwargs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, **kwargs)


def scan():
    summaries = load_json(SUMMARIES, {})
    waiting = [s for s in all_sessions() if needs_summary(s, summaries)]
    waiting.sort(key=lambda s: s["last"] or "", reverse=True)
    pending = [digest(s) for s in waiting[:SCAN_LIMIT]]
    save_json(PENDING, pending, indent=1)
    later = len(waiting) - len(pending)
    more = f" ({later} more next run)" if later else ""
    print(f"{len(pending)} session(s) need a summary{more} -> {PENDING}")


def add(path):
    summaries = load_json(SUMMARIES, {})
    counts = {s["id"]: len(s["prompts"]) for s in all_sessions()}
    for session_id, text in load_json(path, {}).items():
        summaries[session_id] = {"summary": redact(text.strip()), "prompts": counts.get(session_id, 0)}
    save_json(SUMMARIES, summaries, indent=1)
    print(f"{len(summaries)} summaries saved")


def render(out_dir):
    summaries = load_json(SUMMARIES, {})
    rows = []
    for session in all_sessions():
        first = session["prompts"][0]
        rows.append({
            "id": session["id"],
            "title": session["title"] or redact(first[:60]),
            "summary": summaries.get(session["id"], {}).get("summary", ""),
            "project": session["project"],
            "cwd": session["cwd"].replace(HOME, "~", 1),
            "branch": session["branch"],
            "started": session["started"],
            "last": session["last"],
            "prompts": len(session["prompts"]),
            "first": redact(first[:400]),
        })
    rows.sort(key=lambda r: r["last"] or "", reverse=True)
    os.makedirs(out_dir, exist_ok=True)
    shutil.copy(PAGE, os.path.join(out_dir, "index.html"))
    save_json(os.path.join(out_dir, "sessions.json"),
              {"generated": datetime.datetime.now().astimezone().isoformat(), "sessions": rows})
    missing = sum(1 for r in rows if not r["summary"])
    print(f"{len(rows)} sessions -> {out_dir} ({missing} without a summary)")


def url(new=None):
    if new:
        os.makedirs(DATA, exist_ok=True)
        with open(URL_FILE, "w") as f:
            f.write(new.strip() + "\n")
        print(f"saved {new.strip()}")
        return
    try:
        with open(URL_FILE) as f:
            print(f.read().strip())
    except OSError:
        print("none")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "scan":
        scan()
    elif command == "add" and len(sys.argv) == 3:
        add(sys.argv[2])
    elif command == "render" and len(sys.argv) == 3:
        render(sys.argv[2])
    elif command == "url" and len(sys.argv) <= 3:
        url(sys.argv[2] if len(sys.argv) == 3 else None)
    else:
        sys.exit(__doc__)
