"""
Starter template definitions — BACKLOG-087 (Starter Templates by Persona).

Hardcoded persona templates that scaffold a tasteful starting structure
(areas + projects with phases + starter next actions) for a brand-new user.

Kept as Python data (not DB rows) so they are curated, versioned with the
code, and require no database migration. ``TemplateService.apply_template``
turns one of these definitions into real Areas / Projects / ProjectPhases /
Tasks (and activates the PhaseTemplate model via ``phase_templates``).

Shape of each template dict::

    {
        "id": str,                     # stable slug, used in URLs
        "name": str,                   # display name
        "tagline": str,                # one-line hook for the gallery card
        "icon": str,                   # lucide-react icon name (frontend)
        "description": str,            # short paragraph
        "areas": [
            {"key": str, "title": str, "description": str,
             "standard_of_excellence": str},
        ],
        "phase_templates": [
            {"name": str, "description": str, "phases": [str, ...]},
        ],
        "projects": [
            {"title": str, "area_key": str, "outcome_statement": str,
             "purpose": str, "priority": int,
             "phase_template": str | None,   # references phase_templates[].name
             "tasks": [
                 {"title": str, "context": str, "energy_level": str,
                  "is_next_action": bool},
             ]},
        ],
    }

Task ``context`` values mirror the Task model: creative, administrative,
research, communication, deep_work, quick_win. ``energy_level``: high/medium/low.
"""

from __future__ import annotations

from typing import Any

STARTER_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "writer",
        "name": "Writer / Author",
        "tagline": "Keep a manuscript moving and start building a readership.",
        "icon": "pen-tool",
        "description": (
            "Everything an author needs to finish a draft and grow an "
            "audience — a writing area, a publishing area, and a phased "
            "manuscript project to anchor the work."
        ),
        "areas": [
            {
                "key": "writing",
                "title": "Writing",
                "description": "Drafting, revising, and finishing your manuscripts.",
                "standard_of_excellence": (
                    "A manuscript moves forward most weeks; drafts get "
                    "finished, not abandoned."
                ),
            },
            {
                "key": "platform",
                "title": "Publishing & Platform",
                "description": "Audience, submissions, and getting your work into the world.",
                "standard_of_excellence": (
                    "You show up for readers consistently and submissions go "
                    "out on schedule."
                ),
            },
        ],
        "phase_templates": [
            {
                "name": "Manuscript Development",
                "description": "A complete arc from idea to a submission-ready manuscript.",
                "phases": [
                    "Research",
                    "Outline",
                    "First Draft",
                    "Revision",
                    "Editing",
                    "Submission",
                ],
            },
        ],
        "projects": [
            {
                "title": "Finish the first draft of my book",
                "area_key": "writing",
                "outcome_statement": "A complete first draft exists, start to finish, ready to revise.",
                "purpose": "Get the whole story out of my head and onto the page.",
                "priority": 3,
                "phase_template": "Manuscript Development",
                "tasks": [
                    {
                        "title": "Outline the opening chapter",
                        "context": "creative",
                        "energy_level": "high",
                        "is_next_action": True,
                    },
                    {
                        "title": "Write 500 words today",
                        "context": "creative",
                        "energy_level": "high",
                        "is_next_action": False,
                    },
                    {
                        "title": "Block a daily 30-minute writing window",
                        "context": "administrative",
                        "energy_level": "low",
                        "is_next_action": False,
                    },
                ],
            },
            {
                "title": "Build my author platform",
                "area_key": "platform",
                "outcome_statement": "A simple home base readers can find and follow.",
                "purpose": "Start growing an audience before launch day.",
                "priority": 5,
                "phase_template": None,
                "tasks": [
                    {
                        "title": "Reserve my author name on one platform",
                        "context": "administrative",
                        "energy_level": "medium",
                        "is_next_action": True,
                    },
                    {
                        "title": "Draft a one-paragraph author bio",
                        "context": "communication",
                        "energy_level": "medium",
                        "is_next_action": False,
                    },
                ],
            },
        ],
    },
    {
        "id": "knowledge_worker",
        "name": "Knowledge Worker",
        "tagline": "Move your top initiative and build a weekly review rhythm.",
        "icon": "briefcase",
        "description": (
            "A focused setup for professionals juggling priorities — a work "
            "area for your current initiatives and a growth area so your "
            "career keeps advancing too."
        ),
        "areas": [
            {
                "key": "work",
                "title": "Work",
                "description": "Your current role's priorities and deliverables.",
                "standard_of_excellence": (
                    "Your top initiatives move every week and nothing "
                    "important is dropped."
                ),
            },
            {
                "key": "growth",
                "title": "Career Growth",
                "description": "Skills, relationships, and the next step in your career.",
                "standard_of_excellence": (
                    "You invest in growth regularly, not just when job-hunting."
                ),
            },
        ],
        "phase_templates": [
            {
                "name": "Initiative Delivery",
                "description": "Take a work initiative from a fuzzy idea to a delivered outcome.",
                "phases": ["Scope", "Plan", "Execute", "Review"],
            },
        ],
        "projects": [
            {
                "title": "Land my top work initiative",
                "area_key": "work",
                "outcome_statement": "The initiative is delivered and recognized as done.",
                "purpose": "Make visible progress on what matters most this quarter.",
                "priority": 2,
                "phase_template": "Initiative Delivery",
                "tasks": [
                    {
                        "title": "Write the one-line outcome for this initiative",
                        "context": "administrative",
                        "energy_level": "medium",
                        "is_next_action": True,
                    },
                    {
                        "title": "List the 3 key stakeholders",
                        "context": "communication",
                        "energy_level": "medium",
                        "is_next_action": False,
                    },
                    {
                        "title": "Block 2 hours of focus time this week",
                        "context": "deep_work",
                        "energy_level": "medium",
                        "is_next_action": False,
                    },
                ],
            },
            {
                "title": "Build a weekly review habit",
                "area_key": "growth",
                "outcome_statement": "A weekly review is on the calendar and actually happens.",
                "purpose": "Stay on top of commitments instead of reacting.",
                "priority": 5,
                "phase_template": None,
                "tasks": [
                    {
                        "title": "Schedule a recurring 30-minute weekly review",
                        "context": "administrative",
                        "energy_level": "low",
                        "is_next_action": True,
                    },
                ],
            },
        ],
    },
    {
        "id": "engineer",
        "name": "Software Engineer",
        "tagline": "Ship your next feature and level up a core skill.",
        "icon": "code",
        "description": (
            "A starting structure for engineers balancing delivery and "
            "growth — an engineering area with a phased feature project, plus "
            "a learning area for deliberate practice."
        ),
        "areas": [
            {
                "key": "engineering",
                "title": "Engineering",
                "description": "Features, fixes, and the systems you own.",
                "standard_of_excellence": (
                    "Work ships steadily with tests; nothing critical lingers "
                    "half-done."
                ),
            },
            {
                "key": "learning",
                "title": "Learning & Growth",
                "description": "Deliberate practice and skills you're leveling up.",
                "standard_of_excellence": "You spend focused time learning every week.",
            },
        ],
        "phase_templates": [
            {
                "name": "Feature Delivery",
                "description": "Take a feature from a ticket all the way to production.",
                "phases": [
                    "Planning",
                    "Design",
                    "Implementation",
                    "Testing",
                    "Deployment",
                ],
            },
        ],
        "projects": [
            {
                "title": "Ship my next feature",
                "area_key": "engineering",
                "outcome_statement": "The feature is live in production and verified.",
                "purpose": "Deliver real user value end to end.",
                "priority": 2,
                "phase_template": "Feature Delivery",
                "tasks": [
                    {
                        "title": "Write a one-page design doc",
                        "context": "creative",
                        "energy_level": "high",
                        "is_next_action": True,
                    },
                    {
                        "title": "Break the work into tasks",
                        "context": "research",
                        "energy_level": "medium",
                        "is_next_action": False,
                    },
                    {
                        "title": "Create the feature branch",
                        "context": "deep_work",
                        "energy_level": "medium",
                        "is_next_action": False,
                    },
                ],
            },
            {
                "title": "Level up a core skill",
                "area_key": "learning",
                "outcome_statement": "Noticeably more fluent in one chosen skill.",
                "purpose": "Compound my abilities with deliberate practice.",
                "priority": 6,
                "phase_template": None,
                "tasks": [
                    {
                        "title": "Pick one skill to focus on this month",
                        "context": "research",
                        "energy_level": "medium",
                        "is_next_action": True,
                    },
                    {
                        "title": "Block 2 hours of deep-work practice weekly",
                        "context": "deep_work",
                        "energy_level": "low",
                        "is_next_action": False,
                    },
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

_TEMPLATES_BY_ID: dict[str, dict[str, Any]] = {t["id"]: t for t in STARTER_TEMPLATES}


def get_template_definition(template_id: str) -> dict[str, Any] | None:
    """Return the raw template definition for ``template_id`` or ``None``."""
    return _TEMPLATES_BY_ID.get(template_id)
