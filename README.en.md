[中文](README.md) | English

# Obsidian + AI Agent Knowledge Base Management

> Let AI Agents manage your Obsidian vault — without trashing your notes.
> Permission zones + script-level hard constraints + Git version control. You decide every step.

---

## Table of Contents

- [What is this](#what-is-this)
- [Why you need this](#why-you-need-this)
- [Core Design](#core-design)
- [Required Obsidian Plugins](#required-obsidian-plugins)
- [Quick Start](#quick-start)
- [Installation Details](#installation-details)
- [File Structure](#file-structure)
- [Permission Zones](#permission-zones)
- [Entry Workflow](#entry-workflow)
- [Scripts Reference](#scripts-reference)
- [Management & Error Logs](#management--error-logs)
- [FAQ](#faq)
- [Lessons Learned](#lessons-learned)
- [Dependencies](#dependencies)
- [License](#license)

---

## What is this

You save articles in Obsidian: Zhihu answers, blog posts, papers, reports... They pile up, and you never organize them.

You want AI to help — classify, tag, build bidirectional links, compile Wiki concept pages. But you don't trust it not to wreck your notes.

This project solves exactly that: **permission zones + script-level hard constraints + Git version control, so AI can do the work without causing damage.**

It's not just a set of rules — it's a complete, deployable template. Download, change a few paths, tell your Agent to "ingest," and it starts organizing your inbox.

---

## Why you need this

### Problem 1: AI is unpredictable

When you tell AI "organize my notes," it might:

- Edit drafts you're still working on
- Overwrite carefully maintained Wiki pages
- Remove tags you wanted to keep
- Add random links to read-only articles

**Solution**: Four-zone permissions. AI can only freely operate in the activity zone; restricted zones are blocked by scripts; forbidden zones are untouchable.

### Problem 2: Can't undo mistakes

AI modifies 20 articles. You spot problems in 3 — but you don't know what changed or how to roll back.

**Solution**: Git snapshot before every operation, commit after. Screw up? `rollback`.

### Problem 3: No traceability

AI silently does a bunch of work. You don't know what, when, or whether anything went wrong.

**Solution**: Management log + error log, enforced after every operation. No log = not done.

### Problem 4: Link chaos

Today you link A → B. Tomorrow you forget and link A → B again. Duplicates, omissions, wrong links everywhere.

**Solution**: Three-phase entry workflow. Classification doesn't touch links. Wiki doesn't touch links. Links are proposed, reviewed, and applied all at once. Multiple calls to the same article auto-accumulate and deduplicate.

---

## Core Design

### Design Philosophy

> **AI does the execution. Humans make the decisions.** When AI doesn't know something, it asks. When AI can't do something, scripts handle it.

Not "AI fully automates" — but "human-AI collaboration." AI reads articles, makes suggestions, does grunt work. You make all key decisions.

### Four Permission Zones

| Zone | Color | Path | Permissions | What AI Can Do |
|------|-------|------|------------|----------------|
| Activity | 🔵 | `00-收件箱/` | Full read/write | Create, modify, delete, build links |
| Restricted | 🟡 | `01-素材库/` `03-思考/` `04-项目/` `05-产出/` | Script-blocked | Nothing — unless you explicitly authorize |
| Semi-read-only | 🟢 | `02-Wiki/` | Append only | Append related articles, add entries to `_index.md` |
| Forbidden | 🔴 | `06-系统/` | Completely blocked | Untouchable — templates and rules are the foundation |

**Why scripts instead of rules?**

Because AI sometimes ignores rules. Scripts physically refuse writes — hardware isolation.

### Three-Phase Entry Workflow

```
Phase 1: Classify → Phase 2: Compile Wiki → Phase 3: Build Links → Move to Archive
```

Every phase has your review checkpoint. AI doesn't silently modify anything.

### Git Version Control

```
Git snapshot before work → Work → Git commit after → Write management log
```

Something goes wrong? `python scripts/git_control.py rollback` back to the previous state.

---

## Required Obsidian Plugins

Not hard dependencies, but strongly recommended:

| Plugin | Purpose | How to Get |
|--------|---------|------------|
| **Templater** | Template automation — auto-fill frontmatter on entry | Obsidian Community Plugins |
| **Smart Connections** | Vector indexing — semantic search for AI retrieval | Same |
| **Calendar** | Calendar view — browse notes by date | Same |
| **Obsidian Git** | Auto-backup — 30-min auto-commit, the safety net layer | Same |

Install: Obsidian Settings → Community Plugins → Browse → Search → Install → Enable.

> ⚠️ This project does **not** require Dataview. `_index.md` is a static file, updated by `safe_link_appender.py --wiki-index`.

---

## Quick Start

For those who just want to run it. See [Installation Details](#installation-details) for more.

```bash
# 1. Clone
git clone https://github.com/hxlvcl/obsidian-agent-kb.git

# 2. Replace placeholders (three locations)
#    - scripts/*.py: {{VAULT_PATH}}
#    - agent/AGENTS.md: {{VAULT_PATH}}
#    - agent/MEMORY.md: {{VAULT_PATH}} and {{GITHUB_REMOTE}}

# 3. Copy vault/ into your Obsidian Vault root

# 4. Initialize Vault Git
cd "your-vault-path"
git init && git add -A && git commit -m "init"

# 5. Place agent/, skills/, scripts/ in your Agent workspace

# 6. Tell your Agent to "ingest"
```

---

## Installation Details

### Step 1: Download

```bash
git clone https://github.com/hxlvcl/obsidian-agent-kb.git
cd obsidian-agent-kb
```

You'll see four directories: `agent/`, `skills/`, `scripts/`, `vault/`.

### Step 2: Replace Placeholders

Files use `{{...}}` as placeholders. Replace them with your own paths.

**Files to modify:**

| File | Placeholder | Replace With | Example |
|------|-------------|-------------|---------|
| `scripts/safe_link_appender.py` | `{{VAULT_PATH}}` | Obsidian Vault absolute path | `D:\MyNotes` |
| `scripts/git_control.py` | `{{VAULT_PATH}}` | Same | Same |
| `scripts/audit_rules.py` | `{{VAULT_PATH}}` | Same | Same |
| `agent/AGENTS.md` | `{{VAULT_PATH}}` | Same | Same |
| `agent/AGENTS.md` | `{{WORKSPACE_PATH}}` | Agent workspace path | `C:\Users\xxx\.agent\workspace` |
| `agent/MEMORY.md` | `{{VAULT_PATH}}` | Same | Same |
| `agent/MEMORY.md` | `{{GITHUB_REMOTE}}` | Vault GitHub remote URL | `https://github.com/xxx/notes.git` |
| `agent/MEMORY.md` | `{{GITHUB_USER}}` | GitHub username | xxx |
| `agent/MEMORY.md` | `{{HOME_PATH}}` | User home directory | `C:\Users\xxx` |
| `agent/BOOTSTRAP.md` | `{{VAULT_PATH}}` | Same | Same |
| `vault/知识库管理指南.md` | `{{VAULT_PATH}}` | Same | Same |
| `vault/知识库管理指南.md` | `{{GITHUB_REMOTE}}` | Same | Same |

**Easiest method**: Use your editor's "find and replace in files" to replace all `{{VAULT_PATH}}`.

### Step 3: Deploy to Obsidian

Copy **all contents** of `vault/` into your Obsidian Vault root.

Note:
- Don't copy the `vault/` folder itself — copy what's inside
- The directory structure will appear at your Vault root
- Existing directories with the same name won't be overwritten

### Step 4: Initialize Git

In your Vault root:

```bash
cd "your-vault-path"
git init
git add -A
git commit -m "init: initialize knowledge base"
```

### Step 5: Deploy to Agent

Place `agent/`, `skills/`, and `scripts/` directories in your Agent workspace.

### Step 6: Verify

Tell your Agent to "ingest" (or the Chinese equivalent "入库"). It will:

1. Read articles in the inbox
2. Propose classifications, wait for your confirmation
3. Clean frontmatter
4. Keep files in inbox, wait for your Wiki approval
5. Propose link relationships in a table, wait for review
6. Execute links via scripts, move to archive

If you reject at any step, the Agent stops. That's the "you decide every step" principle.

---

## File Structure

```
obsidian-agent-kb/
│
├── README.md                         # This file (Chinese)
├── README.en.md                      # This file (English)
│
├── agent/                            # Agent identity, soul, memory
│   ├── SOUL.md                       #   Core beliefs and principles
│   ├── PROFILE.md                    #   Role, expertise, tone
│   ├── BOOTSTRAP.md                  #   Session initialization checklist
│   ├── AGENTS.md                     #   Operating manual for the Agent
│   ├── HEARTBEAT.md                  #   Scheduled task registry
│   └── MEMORY.md                     #   Long-term memory across sessions
│
├── skills/
│   └── obsidian入库/
│       └── SKILL.md                  # Entry workflow skill: 3 phases + command templates
│
├── scripts/
│   ├── safe_link_appender.py         # Safe link builder: whitelist-enforced writes
│   ├── git_control.py                # Git version control: pre/post/rollback/restore
│   ├── supplement_linker.py          # Auto-backlink from Wiki supplement sections
│   ├── wiki_audit.py                 # Wiki health check: 5 structural inspections
│   └── audit_rules.py                # Rule self-check: parse error log → cluster → suggestions
│
├── tests/                            # Unit tests
│   ├── test_safe_link_appender.py
│   ├── test_supplement_linker.py
│   ├── test_wiki_audit.py
│   └── test_audit_rules.py
│
├── .github/                          # Community health files
│   ├── CONTRIBUTING.md
│   ├── CODE_OF_CONDUCT.md
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
│
├── LICENSE                           # MIT
│
└── vault/                            # Obsidian Vault template
    ├── 知识库管理指南.md               # Rules file the Agent reads
    │
    ├── 00-收件箱/                     # 🔵 Activity zone
    │                                  #   New articles go here
    │
    ├── 01-素材库/                     # 🟡 Restricted zone
    │                                  #   Archived articles, Agent cannot touch
    │
    ├── 02-Wiki/                       # 🟢 Semi-read-only zone
    │   └── _index.md                  #   Master index
    │
    ├── 04-项目/
    │   ├── 管理日志.md                #   Management log: trace every operation
    │   └── 错误日志.md                #   Error log: record every failure
    │
    └── 06-系统/                       # 🔴 Forbidden zone
        ├── 入库流程完整版.md           #   Complete 19-step workflow document
        └── 模板/
            ├── 新笔记.md               #   Standard frontmatter template
            └── Wiki概念页.md           #   Wiki concept page template
```

---

## Permission Zones

### Why Four Zones

This came from hard experience.

**Phase 1: No zones.** AI could modify anything anywhere. It broke 20 articles. Rollback was painful.

**Phase 2: Rule-based constraints.** "Don't touch the archive." "Don't touch system files." But AI sometimes ignored rules, misread rules, or forgot rules.

**Phase 3: Permission zones + script hard blocks.** Not "tell the AI not to touch" — "the AI CAN'T touch."

### Zone Details

#### 🔵 Activity Zone: `00-收件箱/`

AI can freely create, modify, and delete files. The entire entry workflow operates here — clean frontmatter, write placeholders, build links — all in the inbox. Files only move out after link verification.

**Why build links in the inbox?** If something goes wrong, fix it here without touching the archive.

#### 🟡 Restricted Zone: `01-素材库/` etc.

Archived articles live here. AI has **zero write access** — `safe_link_appender.py` will print `[REJECT] BLOCKED`.

If you need to fix a classification, explicitly authorize the Agent.

#### 🟢 Semi-read-only Zone: `02-Wiki/`

AI can append, never overwrite:

- Append related articles to concept pages
- Append new entries to `_index.md`
- Cannot delete existing content
- Cannot modify concept page bodies (append only)

#### 🔴 Forbidden Zone: `06-系统/`

Templates and rules. AI cannot touch these. They are the foundation — if the foundation moves, everything collapses.

---

## Entry Workflow

The complete 19-step workflow is in `vault/06-系统/入库流程完整版.md`. Here are the key phases.

### Phase 1: Classification (Steps 0-8)

**Your role**: Confirm classifications.

The Agent:
1. Scans the inbox, reads every article
2. Proposes classifications (Article A → `01-素材库/教程/`, Article B → `01-素材库/技术概念/`...)
3. **Waits for your confirmation**
4. Cleans frontmatter, removes residue lines, writes placeholder `**关联文章**\n\n（待统一建链）`
5. Files stay in inbox. Git commit marked "pending links."

### Phase 2: Wiki Compilation (Steps 9-13)

**Your role**: Review Wiki change proposals.

The Agent:
1. Scans `02-Wiki/`, checks if new articles match existing concept pages
2. Proposes a Wiki change table:

| Article | Action | Target |
|---------|--------|--------|
| Article A | Incremental update | `02-Wiki/01-科技/Skill Ecosystem.md` |
| Article B | New concept page | `02-Wiki/03-哲学/xxx.md` |
| Article C | Index only | `_index.md` |

3. **Waits for your review** before executing
4. Does **NOT** build any links — Wiki only deals with content

### Phase 3: Link Building + Archive (Steps 14-19)

**Your role**: Review link proposals.

The Agent:
1. Runs `python scripts/supplement_linker.py` to auto-backlink Wiki supplement sections
2. Proposes a link table, **one relationship per row**:

| Article | Related | Reason |
|---------|---------|--------|
| A | B | Same topic |
| A | C | Same author |
| B | D | Quotes viewpoint |

3. **Waits for your review**
4. Builds commands row by row, executes:

```bash
python scripts/safe_link_appender.py --new-article --target "00-收件箱/A.md" --links "B"
python scripts/safe_link_appender.py --wiki-concept --target "02-Wiki/01-科技/xx.md" --article "A"
python scripts/safe_link_appender.py --wiki-index --category "01-科技" --entry "[[A]] — summary"
```

5. Multiple calls to the same article auto-accumulate and deduplicate
6. After link verification, moves files from inbox to archive
7. Git commit + management log

### Why One Target Per Row

Because each relationship has its own reason. If a row says "B, C, D" you can't tell why each is connected. One per row makes review crystal clear.

The script supports multiple calls to the same article with auto-deduplication, so there's no need to merge.

---

## Scripts Reference

### safe_link_appender.py

**Purpose**: Safely append bidirectional links to vault files. Without this script, AI cannot touch restricted zones.

**Three modes**:

| Mode | Command | Use Case |
|------|---------|----------|
| `--new-article` | `--target "收件箱/article.md" --links "target"` | Append links to article's `**关联文章**` block |
| `--wiki-concept` | `--target "Wiki/concept.md" --article "new-article"` | Append article reference to Wiki concept page |
| `--wiki-index` | `--category "01-科技" --entry "[[article]] — summary"` | Append index entry to `_index.md` |

**Security mechanism**:

```
Write request → Check whitelist → Yes → Execute
                                → No → [REJECT] print reason and refuse
```

Whitelist: `00-收件箱/`, `02-Wiki/`
Blacklist: `01-素材库/`, `03-思考/`, `04-项目/`, `05-产出/`, `06-系统/`

**Append mode**: Multiple calls to the same file auto-accumulate, never overwrite existing links.

### supplement_linker.py

**Purpose**: Auto-insert backlinks from Wiki supplement sections to replace manual memory.

Scans all Wiki pages for `#### 来自《Article Name》` headers and inserts `- [[Full Filename]]` on the next line, with full-name resolution and verification.

```bash
python scripts/supplement_linker.py
```

### git_control.py

**Purpose**: Snapshot before work, commit after, rollback on error.

```bash
# Snapshot before work
python scripts/git_control.py pre "entry classification: 3 articles"

# Commit after work
python scripts/git_control.py post "entry complete: 3 articles"

# Rollback to previous state
python scripts/git_control.py rollback

# Restore a single file
python scripts/git_control.py restore "00-收件箱/some-file.md"
```

### wiki_audit.py

**Purpose**: Wiki structural health check — 5 inspections:

1. Empty pages (no substantial content)
2. Orphan pages (no articles link to them)
3. Broken links (target files don't exist)
4. Frequently mentioned but missing concepts
5. Stale `_index.md` entries

```bash
python scripts/wiki_audit.py
python scripts/wiki_audit.py --output report.md
```

### audit_rules.py

**Purpose**: Analyze error logs, cluster similar errors, generate rule improvement suggestions.

```bash
python scripts/audit_rules.py
python scripts/audit_rules.py --save
```

---

## Management & Error Logs

These two files make the entire system traceable. Without them, you don't know what happened when things go wrong.

### Management Log

**Location**: `vault/04-项目/管理日志.md`

**When**: After every Git commit. No log = not done.

**What**: Which articles were ingested, what rules changed, what was fixed, configuration changes.

**Format**:
```markdown
## 2026-04-29

### Entry Records
| Article | Category | Result |

### Fix Records
| Problem | Cause | Resolved |
```

### Error Log

**Location**: `vault/04-项目/错误日志.md`

**When**: Entry self-check fails, Git rollback fails, script errors, any unexpected exceptions.

**What**: Timestamp, error type, specific error, operation context, resolution status.

**Why**: `audit_rules.py` uses this for clustering. If the same error keeps happening, clustering analysis will catch it.

---

## FAQ

### Q: Can I use only part of this?

Yes. Each component is independently usable:

- Just want permissions? Deploy `vault/` + modify Agent rules
- Just want entry scripts? Deploy `scripts/` + `skills/`
- Just want Git version control? Deploy `scripts/git_control.py`

But the full suite works best together.

### Q: Can I change the directory structure?

Yes. After changing, update `ALLOWED`/`BLOCKED` lists in `safe_link_appender.py` and the directory structure in `知识库管理指南.md`.

### Q: The Agent isn't following rules?

Check the error log first. Most likely a permission block — `safe_link_appender.py` prints `[REJECT]` with the reason.

If it's a rule problem (AI didn't read rules), verify `agent/` files are correctly deployed.

### Q: How do I rollback?

```bash
cd "your-vault-path"
python scripts/git_control.py rollback
python scripts/git_control.py restore "path/to/file.md"
```

### Q: Why a management log? Isn't git log enough?

Git log tells you "when something was committed." The management log tells you "why" — human decisions about classification, links, and rule changes.

---

## Lessons Learned

This system was built through countless iterations of failure. Key lessons:

### Don't rely on rule constraints — use script-level hard blocks

Early versions said "the rule says AI can't touch the archive." But AI sometimes ignores rules. Switched to `safe_link_appender.py` whitelist enforcement and the problem disappeared.

### Entry is three phases, not one

Early versions combined classification + links into one step. Result: classification opinions mixed with link opinions, review chaos. Split into three phases — each does one thing, crystal clear.

### Keep files in inbox until links are built

Early versions moved files to archive after cleaning. But subsequent linking needed to modify them, and the archive is read-only. Solution: stay in inbox → build links → then move.

### One target per row in the link table

Early versions: `A | B, C | same topic`. Multiple targets with one reason — you couldn't see why each was linked. One per row makes review obvious.

### Management log is immediate, not batched

Early habit: "work first, write log after." Result: forgetting, missing entries, wrong order. Now: write log immediately after every Git commit.

---

## Dependencies

- Python 3.8+
- Git
- Obsidian v1.5+
- Obsidian plugins (recommended): Templater, Smart Connections, Calendar, Obsidian Git

---

## License

MIT License — see [LICENSE](LICENSE) for full terms.
