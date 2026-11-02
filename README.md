# /history for Claude Code

Type `/history` in Claude Code and you get a private web page listing every Claude Code session on your computer. Each one shows its title, a one-line summary of what you did, the project, when you last used it, and a **Copy** button for the command that reopens it.

Run it again any time. The link stays the same, and only new sessions get summarized.

---

## Setup (about 5 minutes, one time only)

Every grey box below has a copy button in its top-right corner. Copy one box at a time and paste it where the step says.

> **Two places you'll paste:**
> - **Terminal** is the Terminal app on your Mac (press ⌘ Space, type `Terminal`, press Enter).
> - **Claude Code** is where you chat with Claude. Start it by typing `claude` in Terminal.

### Step 1. Get access to this repo

This repo is private. Send Jeremy your GitHub username and wait for the invite email, then click **Accept invitation** in it.

### Step 2. Sign in to GitHub on your computer

Paste into **Terminal**:

```
gh auth login
```

Pick **GitHub.com**, then **HTTPS**, then **Yes**, then **Login with a web browser**, and follow the steps in your browser.

If Terminal says `command not found: gh`, install it first by pasting this into **Terminal**, then run `gh auth login` again:

```
brew install gh
```

(No `brew` either? Download GitHub CLI from https://cli.github.com instead.)

### Step 3. Add the plugin

Paste into **Claude Code**:

```
/plugin marketplace add JavaLavaMT/claude-history
```

Then paste into **Claude Code**:

```
/plugin install history@jeremy-tools
```

### Step 4. Restart Claude Code

Paste into **Claude Code** to quit:

```
/exit
```

Then paste into **Terminal** to start it again:

```
claude
```

### Step 5. Make your page

Paste into **Claude Code**:

```
/history
```

Claude reads your past sessions, writes a short summary for each, and gives you a link to your page. The first run takes a few minutes if you have lots of sessions. After that it's quick.

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
| `/history` isn't recognized | Restart Claude Code (Step 4). It may show up as `/history:history`. Type that instead. |
| An error about the repo when adding the plugin (not found, or access denied) | You haven't accepted the GitHub invite yet (Step 1), or you aren't signed in (Step 2). |
| `python3: command not found` | Paste `xcode-select --install` into **Terminal** and click Install, then try again. |
| Claude can't publish the page | You need to be signed in to Claude Code with a claude.ai account. |

## Privacy

- **Only you can see your page.** It's private to your claude.ai account. Jeremy can't see it, and nobody else can either unless you share it from the page's Share menu.
- **Your data stays on your computer.** Summaries and your page link are saved in `~/.claude/history-data`. Delete that folder to start over.
- **Secrets are removed.** API keys, tokens and passwords are stripped out before Claude reads anything. The page does show the start of your first message in each session, though, so look it over before you share the link with anyone.
