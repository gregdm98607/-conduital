# Lessons Learned

Friction patterns, wrong approaches, and solutions that worked. Referenced by session prompts to prevent recurring issues.

---

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
