# Findings — Session 17 (2026-02-20)

## Pre-session audit

### AI Component Debt Cluster — 6 of 9 already fixed
| ID | Status | Evidence |
|----|--------|----------|
| DEBT-093 | FIXED | Both files use `replace(/_/g, ' ')` |
| DEBT-096 | N/A | No `onSuccess` invalidation exists on the mutation |
| DEBT-097 | FIXED | Single source: mutation data; only `hasRun` boolean remains |
| DEBT-099 | FIXED | `border border-violet-200 dark:border-violet-800` present |
| DEBT-100 | FIXED | `aria-expanded` + `aria-controls` + matching `id` present |
| DEBT-101 | FIXED | `aria-label={Create task: ${task.title}}` present |
| DEBT-102 | OPEN | Proactive + decompose endpoints lack upfront API key check |
| DEBT-104 | OPEN | Pipe-delimited parsing at intelligence.py:1281-1313 |
| DEBT-105 | N/A | No `mb-0` exists; grid uses `mb-8` consistently |

### DEBT-133: requirements.txt removal
- `requirements.txt` is stale orphan (all versions old, missing deps, conflicting Pillow pin)
- `pyproject.toml` is already the source of truth with Pillow `^11.0.0`
- 3 live references need updating: README.md, build.bat, next_session_prompt.md

*Updated: 2026-02-20*
