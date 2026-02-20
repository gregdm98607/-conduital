# Lessons Learned

Friction patterns, wrong approaches, and solutions that worked. Referenced by session prompts to prevent recurring issues.

---

## Session 14 (2026-02-19)

### Friction: git commit with special chars (>, |) in -m flag breaks in cmd
- **Problem**: Using multiple `-m` flags with `>` or `|` in message text causes git to interpret them as shell redirects, producing "error: unknown switch `>`".
- **Wrong approach**: `git commit -m "message with > redirect chars"` in cmd shell.
- **Solution**: Write commit message to a temp file, use `git commit -F C:\path\to\msg.txt`. Works reliably with any special characters.

### Friction: git path with spaces fails in cmd with quoted double-quotes
- **Problem**: `"C:\Program Files\Git\bin\git.exe"` with quoted path fails in cmd: `'"C:\Program Files\..."' is not recognized`.
- **Wrong approach**: Quoting the whole path string in cmd.
- **Solution**: Use 8.3 short path `C:\PROGRA~1\Git\bin\git.exe` in cmd shell (no quotes needed). Works reliably. PowerShell uses `& "C:\Program Files\Git\bin\git.exe"`.

### Friction: npm ci only installs 77 packages (missing devDependencies)
- **Problem**: `npm ci` on a fresh clone installed only 77 packages — missing typescript, vite, etc. tsc was not in node_modules/.bin.
- **Wrong approach**: Assuming `npm ci` installs devDependencies by default.
- **Solution**: Use `npm install --include=dev` to ensure devDependencies are installed. Or check that the lock file is complete before running `npm ci`.

### Friction: tsc.cmd path in cmd shell
- **Problem**: `node_modules\.bin\tsc` not recognized; needed `.cmd` extension.
- **Solution**: Always use `node_modules\.bin\tsc.cmd` and `node_modules\.bin\vite.cmd` in cmd shell on Windows.

### Friction: Windows Store Python can't install pip packages
- **Problem**: `pip install -r requirements.txt` fails with setuptools/build errors when using the Windows Store Python stub (`C:\Users\...\WindowsApps\python.exe`). It's sandboxed.
- **Wrong approach**: Trying various pip flags (--no-build-isolation, --ignore-requires-python).
- **Solution**: Backend tests require a real Python install + venv. Use `python -m venv venv && venv\Scripts\activate.bat && pip install -r requirements.txt`. If Poetry is available, use `poetry run pytest`. If neither is set up in this environment, skip backend tests and note it in the session log.

### Friction: PowerShell swallows git output silently
- **Problem**: `& "C:\Program Files\Git\bin\git.exe" status` in PowerShell via start_process returns exit 0 with zero output, even with `> file.txt 2>&1` redirect.
- **Solution**: Use `cmd` shell for all git commands. The `cd X && git ...` pattern works reliably in cmd.

## Session 13 (2026-02-14)

### Friction: AI-disabled tests fail on dev machine
- **Problem**: Tests asserting `AI_FEATURES_ENABLED=False` returned 200 instead of 400 because local `.env` sets `AI_FEATURES_ENABLED=True`. The settings singleton reads from `.env` at import time.
- **Wrong approach**: Relying on default value (False) without patching.
- **Solution**: Always explicitly patch `settings.AI_FEATURES_ENABLED` in tests:
  ```python
  with patch("app.core.config.settings.AI_FEATURES_ENABLED", False):
  ```

### Friction: Rebalance endpoint is NOT AI-gated
- **Problem**: Wrote test assuming rebalance returns 400 when AI disabled. It returned 200.
- **Wrong approach**: Treating all intelligence endpoints as AI-gated.
- **Solution**: Rebalance and Energy endpoints are rule-based — they work without AI config. Only test AI-gated behavior for endpoints that actually check `AI_FEATURES_ENABLED` (analyze, suggest, weekly-review, proactive, review-project, decompose-tasks).

### Friction: Rebalance response schema mismatch
- **Problem**: Test asserted `{promote, demote, narrative}` but actual schema is `{opportunity_now_count, threshold, suggestions}`.
- **Wrong approach**: Guessing schema from endpoint name.
- **Solution**: Always read the Pydantic response model (or hit the endpoint first) before writing assertions. Check `RebalanceResponse` in `schemas/intelligence.py`.

### Friction: Chrome extension disconnects during browser testing
- **Problem**: Claude in Chrome extension disconnects mid-scroll, requiring reconnection.
- **Solution**: Call `tabs_context_mcp` to reconnect, then retry the action. Not a code issue — just an environment quirk.

### Friction: AITaskDecomposition hidden in NPM section
- **Problem**: Couldn't find AITaskDecomposition on project detail page during browser testing.
- **Solution**: The component is inside the "Natural Planning Model" collapsible section, which only renders when the project has brainstorm/organizing notes. Test with a project that has NPM data, or verify via code review.

### Pattern: Shared utility extraction
- **What worked**: Creating `utils/aiErrors.ts` and `utils/sort.ts` as shared utilities, then updating all consumers in one pass.
- **Key**: Read all callers first (grep for the function name), then update each one. Verify with TypeScript check after each batch.

### Pattern: Backend test helper method
- **What worked**: Created `_enable_ai_and_mock_provider()` helper in the test class to reduce boilerplate across 13 tests.
- **Key**: Mock at `create_provider` factory level, not individual methods. Return a mock provider that has all needed attributes.
