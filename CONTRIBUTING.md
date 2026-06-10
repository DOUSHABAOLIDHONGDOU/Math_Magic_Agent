# Contributing

Thanks for the interest! This project is a Codex + Claude Code multi-agent
workflow for CUMCM-style mathematical modeling competitions. PRs are welcome.

## Quick orientation

- `05_code/tools/agentctl.py` — thin CLI entry point. ~450 lines.
- `05_code/tools/mm/` — all the logic, split by domain:
  - `_state.py` — workflow state, snapshots, trust profile
  - `_paths.py` — every project path constant lives here
  - `_archive.py` — stale-artifact archival for problem switching
  - `_data.py` — data dictionary scanner
  - `_eda.py` — Phase 3a auto-EDA (6 diagnostic figures)
  - `_briefs.py` — scheme / approval / model-confirmation brief renderers
  - `_workorder.py` — Phase 2 rich Claude prompts (inlined context)
  - `_dispatch.py` — Claude Code visible terminal + monitor + watch loops
  - `_paper.py` — LaTeX compile + layout check + figure lint integration
  - `_review.py` — Phase 3b data-driven scheme comparison
  - `_rag.py` — Phase 4 BM25 retrieval over excellent papers
  - `_figure_lint.py` — Phase 5 PIL-based figure violation checks
  - `_env.py` — env-check / doctor / readiness self-healing hints
  - `_commands.py` — orchestration wrappers used by the CLI
- `05_code/tools/tests/` — pytest suite (43 tests).

## Development setup

```bash
conda env create -f environment.yml
conda activate math-magic
python 05_code/tools/agentctl.py env-check
python -m pytest 05_code/tools/tests/ -q
```

The tests do **not** require xelatex, tesseract, or Claude Code, so they run
fine in plain CI.

## Things to know before opening a PR

### 1. Don't break the CLI surface

Existing commands and their argparse flags are a stable contract. If you need
to change a flag's behaviour, add a new flag instead (boolean flags use
`add_boolean_optional_argument` from `_util`).

### 2. State changes need a migration

`mm/_state.py:STATE_VERSION` bumps on every breaking state-schema change.
`migrate_state` is responsible for upgrading older state files in place. Add
a test in `tests/test_state.py` that loads the previous shape and verifies
it round-trips.

### 3. Tests first

Every new module in `mm/` should ship with a `tests/test_*.py` file. The
shared fixtures in `conftest.py` give you an `isolated_project` tmp dir and
a `minimal_state` factory. Use `monkeypatch.setattr(mm._paths, "PROJECT_ROOT", tmp)`
when you need to redirect module-level path constants.

### 4. Windows compatibility

This project is used on Windows + VS Code as the primary surface. When
touching anything that talks to a subprocess:
- Use bytes mode (`capture_output=True` without `text=True`) and decode with
  `errors="replace"` so the GBK console can't crash.
- Write PowerShell scripts as UTF-8 with BOM (`_util.write_powershell_script`)
  so Chinese paths render correctly.
- Use `_util.rel()` (which now returns POSIX-style strings) when embedding
  paths in Markdown or LaTeX.

### 5. Don't commit per-problem material

`.gitignore` excludes `01_problem/source/`, `03_methods/Q*/`, `06_results/Q*/`,
imported problem statements, and the BM25 index. The pattern is: **anything an
`agentctl` command can regenerate from a fresh `import-problem` should not be
in git**. Sample paper texts in `02_references/paper_texts/` are an exception
when they're licensed for distribution.

### 6. Run the pre-merge sanity check

```bash
python -m pytest 05_code/tools/tests/ -v
python 05_code/tools/agentctl.py --help
python 05_code/tools/agentctl.py readiness  # should print and not crash
```

## Project-specific terminology

| Term | Meaning |
|---|---|
| Codex | The "modeling controller" agent — designs schemes, writes the paper, reviews code. |
| Claude Code | The "implementer" agent — generates and runs code, writes basic figures, hands back a completion report. |
| Workorder | A bounded implementation task for Claude Code with explicit do-not-modify boundaries. |
| Brief | A user-facing markdown document offering numbered approval choices. |
| Trust profile | `strict` / `normal` / `fast` — controls how many human approval gates the workflow inserts. |

## Releasing a new version

1. Bump `STATE_VERSION` in `mm/_state.py` if state schema changed.
2. Bump `version` in `tool_registry.json`.
3. Run `python 05_code/tools/agentctl.py readiness` on a clean checkout to make sure the migration runs.
4. Tag and push. There is no PyPI package; users install via `git clone` + `conda env create`.

## Where to ask questions

Open a GitHub issue. Include:
- Your OS + Python version
- Output of `python 05_code/tools/agentctl.py doctor`
- The full command that misbehaved + its output
