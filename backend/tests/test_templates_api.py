"""
Tests for the starter-template API (BACKLOG-087).

Covers:
- GET  /templates              — list with preview counts
- GET  /templates/{id}         — full preview + 404
- POST /templates/{id}/apply   — scaffolds areas/projects/phases/tasks, links
                                  PhaseTemplate, sets live momentum, 404, and
                                  idempotent re-apply (areas + phase templates)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.area import Area
from app.models.base import Base
from app.models.phase_template import PhaseTemplate
from app.models.project import Project
from app.models.project_phase import ProjectPhase
from app.models.task import Task


@pytest.fixture(autouse=True)
def reset_module_registry():
    from app.modules.registry import registry
    registry._modules.clear()
    registry._initialized.clear()
    yield
    registry._modules.clear()
    registry._initialized.clear()


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(test_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


def _count(db, model) -> int:
    return db.execute(select(func.count(model.id))).scalar_one()


class TestList:
    def test_returns_three_personas(self, client):
        resp = client.get("/api/v1/templates")
        assert resp.status_code == 200, resp.text
        templates = resp.json()["templates"]
        assert len(templates) == 3
        ids = {t["id"] for t in templates}
        assert ids == {"writer", "knowledge_worker", "engineer"}

    def test_summary_counts_match_definition(self, client):
        resp = client.get("/api/v1/templates")
        writer = next(t for t in resp.json()["templates"] if t["id"] == "writer")
        # 2 areas; 2 projects; 3 + 2 = 5 tasks
        assert writer["area_count"] == 2
        assert writer["project_count"] == 2
        assert writer["task_count"] == 5
        assert writer["icon"] and writer["tagline"]


class TestDetail:
    def test_detail_shape(self, client):
        resp = client.get("/api/v1/templates/writer")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["areas"]) == 2
        assert len(body["projects"]) == 2
        manuscript = next(
            p for p in body["projects"] if p["phase_template"] == "Manuscript Development"
        )
        assert manuscript["phases"] == [
            "Research", "Outline", "First Draft", "Revision", "Editing", "Submission",
        ]
        assert any(t["is_next_action"] for t in manuscript["tasks"])

    def test_detail_unknown_returns_404(self, client):
        assert client.get("/api/v1/templates/does-not-exist").status_code == 404


class TestApply:
    def test_apply_creates_entities(self, client, db):
        resp = client.post("/api/v1/templates/engineer/apply")
        assert resp.status_code == 201, resp.text
        result = resp.json()
        assert result["areas_created"] == 2
        assert result["projects_created"] == 2
        assert result["tasks_created"] == 5
        assert result["first_project_id"] is not None

        assert _count(db, Area) == 2
        assert _count(db, Project) == 2
        assert _count(db, Task) == 5

    def test_apply_links_phase_template_and_creates_phases(self, client, db):
        client.post("/api/v1/templates/engineer/apply")

        # The dormant PhaseTemplate model is now populated + linked.
        pt = db.execute(
            select(PhaseTemplate).where(PhaseTemplate.name == "Feature Delivery")
        ).scalar_one()
        feature_project = db.execute(
            select(Project).where(Project.phase_template_id == pt.id)
        ).scalar_one()
        assert feature_project.title == "Ship my next feature"

        phases = db.execute(
            select(ProjectPhase)
            .where(ProjectPhase.project_id == feature_project.id)
            .order_by(ProjectPhase.phase_order)
        ).scalars().all()
        assert [p.phase_name for p in phases] == [
            "Planning", "Design", "Implementation", "Testing", "Deployment",
        ]
        assert phases[0].status == "active"
        assert phases[1].status == "pending"

        # The non-phased project has no phases and no phase_template_id.
        learning_project = db.execute(
            select(Project).where(Project.title == "Level up a core skill")
        ).scalar_one()
        assert learning_project.phase_template_id is None
        assert _count_phases_for(db, learning_project.id) == 0

    def test_apply_marks_next_actions_and_context(self, client, db):
        client.post("/api/v1/templates/engineer/apply")
        next_actions = db.execute(
            select(Task).where(Task.is_next_action.is_(True))
        ).scalars().all()
        assert len(next_actions) == 2  # one per project
        for task in next_actions:
            assert task.context  # context populated
            assert task.energy_level
            assert task.urgency_zone == "opportunity_now"

    def test_apply_sets_live_momentum(self, client, db):
        client.post("/api/v1/templates/knowledge_worker/apply")
        projects = db.execute(select(Project)).scalars().all()
        assert projects
        for p in projects:
            assert 0.0 < p.momentum_score <= 1.0
            assert p.last_activity_at is not None

    def test_apply_unknown_returns_404(self, client):
        assert client.post("/api/v1/templates/nope/apply").status_code == 404

    def test_reapply_dedupes_areas_and_phase_templates(self, client, db):
        first = client.post("/api/v1/templates/writer/apply").json()
        assert first["areas_created"] == 2

        second = client.post("/api/v1/templates/writer/apply").json()
        # Areas + phase templates are get-or-created -> not duplicated.
        assert second["areas_created"] == 0
        assert _count(db, Area) == 2
        assert (
            db.execute(
                select(func.count(PhaseTemplate.id)).where(
                    PhaseTemplate.name == "Manuscript Development"
                )
            ).scalar_one()
            == 1
        )
        # Projects/tasks are intentionally additive across applies.
        assert _count(db, Project) == 4


def _count_phases_for(db, project_id: int) -> int:
    return db.execute(
        select(func.count(ProjectPhase.id)).where(ProjectPhase.project_id == project_id)
    ).scalar_one()
