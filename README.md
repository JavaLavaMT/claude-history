# /history for Claude Code

[![Tests](https://github.com/JavaLavaMT/claude-history/actions/workflows/test.yml/badge.svg)](https://github.com/JavaLavaMT/claude-history/actions/workflows/test.yml)

Type `/history` in Claude Code and you get a private web page listing every Claude Code session on your computer. Each one shows its title, a one-line summary of what you did, the project, when you last used it, and a **Copy** button for the command that reopens it.

Run it again any time. The link stays the same, and only new sessions get summarized.

---

## Setup (about 2 minutes, one time only)

Every grey box below has a copy button in its top-right corner. Copy one box at a time and paste it where the step says.

> **Two places you'll paste:**
> - **Terminal** is the Terminal app on your Mac (press ⌘ Space, type `Terminal`, press Enter).
> - **Claude Code** is where you chat with Claude. Start it by typing `claude` in Terminal.

### Step 1. Add the plugin

Paste into **Claude Code**:

```
/plugin marketplace add JavaLavaMT/claude-history
```

Then paste into **Claude Code**:

```
/plugin install history@jeremy-tools
```

### Step 2. Restart Claude Code

Paste into **Claude Code** to quit:

```
/exit
```

Then paste into **Terminal** to start it again:

```
claude
```

### Step 3. Make your page

Paste into **Claude Code**:

```
/history
```

Claude reads your past sessions, writes a short summary for each, and gives you a link to your page. If you have lots of sessions, the first run summarizes your 40 most recent. Run `/history` again to fill in the rest.

---

## Using it

- **Update the page:** run `/history` again. Same link every time.
- **Reopen an old session:** on the page, click **Copy** next to the session and paste it into **Terminal**.
- **Find something:** type in the search box on the page, or click a project name to filter.

## Getting updates

When Jeremy updates the plugin, paste into **Claude Code**:

```
/plugin marketplace update jeremy-tools
```

---

## Something not working?

| What you see | Fix |
|---|---|
| `/history` isn't recognized | Restart Claude Code (Step 2). It may show up as `/history:history`. Type that instead. |
| An error about the repo when adding the plugin | Check the spelling: `JavaLavaMT/claude-history`. Then run `/plugin marketplace add JavaLavaMT/claude-history` again. |
| `python3: command not found` | Paste `xcode-select --install` into **Terminal** and click Install, then try again. |
| Claude can't publish the page | You need to be signed in to Claude Code with a claude.ai account. |

## Privacy

- **Only you can see your page.** It's private to your claude.ai account. Jeremy can't see it, and nobody else can either unless you share it from the page's Share menu.
- **Your data stays on your computer.** Summaries and your page link are saved in `~/.claude/history-data`. Delete that folder to start over.
- **Secrets are removed.** API keys, tokens and passwords are stripped out before Claude reads anything. The page does show the start of your first message in each session, though, so look it over before you share the link with anyone.

---

## For Jeremy: shipping an update

1. Make the change and run the tests: `python3 -m unittest discover tests -v`
2. Bump `version` in `.claude-plugin/plugin.json` (for example `1.1.0` to `1.2.0`). Friends only get the update when this number changes.
3. Commit and push to `main`.
4. Tell friends to run `/plugin marketplace update jeremy-tools`.
