# R6 Scope — Candidate Comparison

Three R6 candidates ranked for effort, leverage, and dependencies.
PostHog has only had ~24 hours of telemetry as of S32 — revisit this doc once a
full week of funnel data is in before final selection.

## Candidate A — BACKLOG-153: File Sync UX

Sync runs invisibly today. New users have no idea anything is working.

- **Effort:** Medium (~1 week). Needs a sync-status WebSocket channel, a visible
  toolbar/footer indicator, an in-page "last sync" tooltip, and conflict-resolution
  UI for the existing prompt strategy. Backend already emits sync events
  (see `useDiscoveryWebSocket`), so reuse is plausible.
- **Leverage:** **High.** First-install activation likely depends on users
  *seeing* the sync work. PostHog `gate_hit_*` data after one full week will
  confirm whether this is the gap; gut says yes.
- **Dependencies:** None. Pure frontend + small backend WS additions. No DNS,
  no Stripe, no third-party.

## Candidate B — BACKLOG-159: Post-Activation Welcome Flow

Today the only feedback after a $X purchase is a bare toast saying "License
accepted." That's a wasted moment.

- **Effort:** Small (~2-3 days). One modal / route, content design, link to a
  feature tour for the unlocked tier (gtd or full).
- **Leverage:** **Medium.** Moves the needle on per-user satisfaction but only
  fires once per buyer; absolute volume is small until acquisition scales.
  Pairs naturally with MON-008 from S32 (Stripe inline now activates).
- **Dependencies:** Needs the feature-tour content (writer time, not engineer
  time). Could ship as a stub without a tour and add the tour incrementally.

## Candidate C — BACKLOG-087: Starter Templates by Persona

Pre-built project + area templates for Writer, Knowledge Worker, PM, etc.,
applied at first-launch onboarding.

- **Effort:** **Large.** Code is small (template loader + selection UI), but
  the content side — designing each persona's starter set so it's actually
  useful — is the bulk of the work and is content design, not engineering.
- **Leverage:** Medium-high *if* the personas are well-chosen. A bad persona
  template is worse than none — it teaches the wrong mental model. Strong gut
  feel needed before committing.
- **Dependencies:** Persona research (interviews? assumed?), content authoring,
  legal-style review of any templates that imply commitments.

## Recommendation

**Wait one week**, then re-rank with PostHog data. If `gate_hit_*` events show
users bouncing off file sync confusion, ship A. If the funnel shows healthy
activation but low conversion-to-paid, ship B. C is a parking-lot item until
content design has bandwidth.

If forced to commit today: **A (File Sync UX)**, because it benefits every user,
not just paid ones, and the data is more likely to confirm than refute the
hypothesis.
