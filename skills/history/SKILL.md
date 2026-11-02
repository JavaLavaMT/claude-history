---
name: history
description: Publish a searchable web page of every local Claude Code session on this computer (title, short summary, project, last active, copyable resume command). Use when the user runs /history or asks to find, browse or list past Claude sessions.
---

# Session history page

Builds one private artifact page listing every Claude Code session in `~/.claude/projects`, and keeps it at the same URL across runs.

`<skill>` below means this skill's folder: the "Base directory for this skill" shown above. The user's own data (summaries, page URL) is kept in `~/.claude/history-data`, never in the skill folder.

## 1. Find sessions that need a summary

```
python3 <skill>/history.py scan
```

This writes `~/.claude/history-data/pending.json`: one digest per session that is new or has grown by 5+ prompts since it was last summarized. Secrets are already redacted from it.

## 2. Write the summaries

Read `pending.json`. For each session write a summary of one or two plain sentences (under 220 characters): what the user was working on and where it ended up, naming the app, feature or bug. Use the `recap` field when present, it is the best source. Write it for the user ("Fixed the 500 error on checkout in the shop app"), not about them, and never copy secrets, tokens, passwords or personal data into it.

Write them as `{"<id>": "<summary>", ...}` to a file in your scratchpad, then merge:

```
python3 <skill>/history.py add <that file>
```

With many pending sessions, do it in batches of about 25 so nothing gets dropped. On a first run with hundreds of sessions, tell the user it will take a while.

## 3. Build the page and publish

The Artifact tool only publishes files from the working directory or your scratchpad, so build straight into the scratchpad:

```
python3 <skill>/history.py render <scratchpad>/history
python3 <skill>/history.py url
```

Publish `<scratchpad>/history/index.html` with `root: "<scratchpad>/history"` and `files: {"sessions.json": "sessions.json"}`, using the full scratchpad path.

- If `url` printed a link, first `read` that URL and list its files (`scope: "files"`), then publish with that `url` so the link stays the same.
- If it printed `none`, publish without `url`, with `icon: "history"` and the description "Searchable list of your local Claude Code sessions with summaries and resume commands." Then save the returned link: `python3 <skill>/history.py url <link>`.

## 4. Reply

Give the link and one line: how many sessions are listed and how many summaries were added this run. If the user also asked about a specific session, answer that too with its resume command.
