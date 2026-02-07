"""
AI service - Multi-provider AI integration for intelligent task generation

Supports:
- Anthropic Claude (default)
- OpenAI GPT
- Google Gemini
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.models.activity_log import ActivityLog
from app.models.project import Project
from app.models.task import Task


# =============================================================================
# Provider Abstraction
# =============================================================================

class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """Generate a text response from the AI model."""
        ...

    @abstractmethod
    def test_connection(self) -> dict:
        """Test the connection. Returns {'success': bool, 'message': str, 'model': str|None}."""
        ...


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def test_connection(self) -> dict:
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return {"success": True, "message": f"Connection successful. Model: {self.model}", "model": self.model}
        except Exception as e:
            return {"success": False, "message": str(e), "model": self.model}


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    def test_connection(self) -> dict:
        try:
            self.client.chat.completions.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return {"success": True, "message": f"Connection successful. Model: {self.model}", "model": self.model}
        except Exception as e:
            return {"success": False, "message": str(e), "model": self.model}


class GoogleProvider(AIProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str, model: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": temperature},
        )
        return response.text.strip()

    def test_connection(self) -> dict:
        try:
            self.model.generate_content(
                "hi",
                generation_config={"max_output_tokens": 1},
            )
            return {"success": True, "message": f"Connection successful. Model: {self.model_name}", "model": self.model_name}
        except Exception as e:
            return {"success": False, "message": str(e), "model": self.model_name}


# Provider model catalogs
PROVIDER_MODELS = {
    "anthropic": [
        {"id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5 (Recommended)"},
        {"id": "claude-opus-4-6", "name": "Claude Opus 4"},
        {"id": "claude-haiku-3-5-20241022", "name": "Claude 3.5 Haiku (Fast)"},
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o (Recommended)"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Fast)"},
    ],
    "google": [
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (Recommended)"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Fast)"},
    ],
}

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-5-20250929",
    "openai": "gpt-4o",
    "google": "gemini-1.5-pro",
}


def get_api_key_for_provider(provider: str) -> Optional[str]:
    """Get the configured API key for a provider."""
    if provider == "anthropic":
        return settings.ANTHROPIC_API_KEY
    elif provider == "openai":
        return settings.OPENAI_API_KEY
    elif provider == "google":
        return settings.GOOGLE_API_KEY
    return None


def create_provider(provider: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None) -> AIProvider:
    """Factory function to create the appropriate AI provider."""
    provider = provider or settings.AI_PROVIDER
    model = model or settings.AI_MODEL
    key = api_key or get_api_key_for_provider(provider)

    if not key:
        raise ValueError(f"No API key configured for provider: {provider}")

    if provider == "anthropic":
        return AnthropicProvider(api_key=key, model=model)
    elif provider == "openai":
        return OpenAIProvider(api_key=key, model=model)
    elif provider == "google":
        return GoogleProvider(api_key=key, model=model)
    else:
        raise ValueError(f"Unknown AI provider: {provider}")


# =============================================================================
# AI Service (uses provider abstraction)
# =============================================================================

class AIService:
    """Service for AI-powered project intelligence features"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI service with the configured provider."""
        self.provider = create_provider(api_key=api_key)

    def generate_unstuck_task(
        self, db: Session, project: Project, max_tokens: int = 200
    ) -> str:
        """
        Generate AI-powered unstuck task suggestion
        """
        context = self._build_project_context(db, project)
        prompt = self._create_unstuck_task_prompt(project, context)

        try:
            suggestion = self.provider.generate(prompt, max_tokens=max_tokens, temperature=0.7)
            suggestion = suggestion.strip('"\'')
            if suggestion.startswith("Task:"):
                suggestion = suggestion[5:].strip()
            return suggestion
        except Exception as e:
            logger.warning(f"AI generation failed, using fallback: {e}")
            from app.services.intelligence_service import IntelligenceService
            return IntelligenceService.generate_unstuck_task_suggestion(db, project)

    def _build_project_context(self, db: Session, project: Project) -> dict:
        """Build comprehensive context for AI analysis."""
        recent_activity = (
            db.execute(
                select(ActivityLog)
                .where(
                    ActivityLog.entity_type == "project",
                    ActivityLog.entity_id == project.id,
                )
                .order_by(ActivityLog.timestamp.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

        pending_tasks = (
            db.execute(
                select(Task)
                .where(Task.project_id == project.id, Task.status == "pending")
                .limit(10)
            )
            .scalars()
            .all()
        )

        completed_tasks = (
            db.execute(
                select(Task)
                .where(Task.project_id == project.id, Task.status == "completed")
                .order_by(Task.completed_at.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

        current_phase = None
        if project.phases:
            current_phase = next(
                (p for p in project.phases if p.status == "active"), None
            )

        days_stalled = 0
        if project.stalled_since:
            days_stalled = (datetime.now(timezone.utc) - project.stalled_since).days

        return {
            "title": project.title,
            "description": project.description or "",
            "area": project.area.name if project.area else None,
            "status": project.status,
            "days_stalled": days_stalled,
            "momentum_score": project.momentum_score,
            "current_phase": current_phase.name if current_phase else None,
            "recent_activity": [
                {"action": a.action_type, "timestamp": a.timestamp.isoformat()}
                for a in recent_activity
            ],
            "pending_tasks": [{"title": t.title} for t in pending_tasks],
            "completed_tasks": [{"title": t.title} for t in completed_tasks],
            "has_next_action": any(t.is_next_action for t in pending_tasks),
        }

    def _create_unstuck_task_prompt(self, project: Project, context: dict) -> str:
        """Create prompt for unstuck task generation."""
        prompt = f"""You are a GTD (Getting Things Done) productivity assistant helping someone restart momentum on a stalled project.

Project: {context['title']}
Status: Stalled for {context['days_stalled']} days
Momentum Score: {context['momentum_score']}/1.0
Area: {context['area'] or 'Not specified'}

Description:
{context['description'] or 'No description available'}

Current Phase: {context['current_phase'] or 'Not specified'}

Recent Activity:
{self._format_activity_list(context['recent_activity'])}

Pending Tasks ({len(context['pending_tasks'])}):
{self._format_task_list(context['pending_tasks'])}

Recently Completed:
{self._format_task_list(context['completed_tasks'])}

Generate a SINGLE minimal viable task (5-15 minutes) to restart momentum on this project.

Requirements:
1. Must be a concrete, physical action (not "review" or "think about")
2. Should be achievable in 5-15 minutes
3. Should create visible progress
4. Should naturally lead to the next step
5. Should require low energy/willpower
6. Must be specific enough to do immediately

Return ONLY the task title (maximum 80 characters). Do not include explanations, quotes, or formatting.

Example good tasks:
- "Open project file and read first 3 pages"
- "Send 2-sentence email to check on editor status"
- "Create bullet list of 5 potential next steps"
- "Set 15-minute timer and write opening paragraph"
- "Make phone call to schedule follow-up meeting"

Task:"""
        return prompt

    def _format_activity_list(self, activities: list[dict]) -> str:
        """Format activity list for prompt"""
        if not activities:
            return "- No recent activity"
        return "\n".join(f"- {a['action']}" for a in activities[:3])

    def _format_task_list(self, tasks: list[dict]) -> str:
        """Format task list for prompt"""
        if not tasks:
            return "- None"
        return "\n".join(f"- {t['title']}" for t in tasks[:5])

    def analyze_project_health(
        self, db: Session, project: Project, max_tokens: int = 500
    ) -> dict:
        """Generate AI-powered project health analysis."""
        context = self._build_project_context(db, project)

        prompt = f"""Analyze the health of this project and provide recommendations.

Project: {context['title']}
Momentum Score: {context['momentum_score']}/1.0
Days Since Activity: {context['days_stalled']}
Current Phase: {context['current_phase'] or 'Not specified'}

Pending Tasks: {len(context['pending_tasks'])}
Has Next Action: {context['has_next_action']}

Provide a brief analysis (2-3 sentences) and 2-3 specific actionable recommendations.

Format:
Analysis: [Your analysis]
Recommendations:
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]"""

        try:
            response = self.provider.generate(prompt, max_tokens=max_tokens, temperature=0.7)
            parts = response.split("Recommendations:")
            analysis = parts[0].replace("Analysis:", "").strip()
            recommendations = []
            if len(parts) > 1:
                for line in parts[1].strip().split("\n"):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        rec = line.lstrip("0123456789.-) ").strip()
                        if rec:
                            recommendations.append(rec)
            return {"analysis": analysis, "recommendations": recommendations}
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            return {"analysis": "Unable to generate AI analysis", "recommendations": []}

    def suggest_next_action(
        self, db: Session, project: Project, max_tokens: int = 200
    ) -> str:
        """Suggest the next action for a project."""
        context = self._build_project_context(db, project)

        prompt = f"""Suggest the single most important next action for this project.

Project: {context['title']}
Current Phase: {context['current_phase'] or 'Not specified'}

Description:
{context['description'] or 'No description'}

Pending Tasks:
{self._format_task_list(context['pending_tasks'])}

Recently Completed:
{self._format_task_list(context['completed_tasks'])}

Generate ONE concrete next action that will move this project forward.

Requirements:
1. Must be a physical, visible action
2. Should take 15-60 minutes
3. Should align with project goals
4. Must be specific and actionable

Return ONLY the task title (maximum 80 characters).

Next Action:"""

        try:
            suggestion = self.provider.generate(prompt, max_tokens=max_tokens, temperature=0.7)
            suggestion = suggestion.strip('"\'')
            if suggestion.startswith("Next Action:"):
                suggestion = suggestion[12:].strip()
            return suggestion
        except Exception as e:
            logger.warning(f"AI suggestion failed: {e}")
            return f"Review project status and define next steps for {project.title}"
