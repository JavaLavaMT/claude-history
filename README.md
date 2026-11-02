# /history for Claude Code

Type `/history` and Claude builds a private web page listing every Claude Code session on your computer: title, a one-line summary, project, when you last used it, and a copyable `claude --resume` command. Run it again any time; the page keeps the same link and only new or grown sessions get summarized.

## Install

In Claude Code:

```
/plugin marketplace add JavaLavaMT/claude-history
/plugin install history@jeremy-tools
```

This repo is private: you need to be added as a collaborator, and git on your computer needs to be signed in to GitHub (`gh auth login` is the easiest way).

Restart Claude Code, then run `/history` (it may show as `/history:history`).

To get updates later: `/plugin marketplace update jeremy-tools`.

## Needs

- Python 3 (built into macOS; `python3 --version` to check)
- A claude.ai account with artifacts, since the page is published as a private artifact

## Privacy

- Your page is private to your claude.ai account. Nobody else, including whoever shared this plugin, can see it unless you share it from the page's Share menu.
- Summaries and the page link are stored on your computer in `~/.claude/history-data`. Delete that folder to start fresh.
- Obvious secrets (API keys, tokens, passwords) are stripped from prompts before Claude reads them, but the page does show the start of your first message in each session, so review it before sharing the link with anyone.
