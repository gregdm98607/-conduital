"""
Goal API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.goal import Goal as GoalModel
from app.schemas.goal import Goal, GoalCreate, GoalUpdate

router = APIRouter()


@router.get("", response_model=list[Goal])
def list_goals(db: Session = Depends(get_db)):
    """List all goals"""
    goals = db.execute(select(GoalModel).order_by(GoalModel.target_date.nullslast())).scalars().all()
    return list(goals)


@router.get("/{goal_id}", response_model=Goal)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    """Get a single goal by ID"""
    goal = db.get(GoalModel, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.post("", response_model=Goal, status_code=201)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal"""
    new_goal = GoalModel(**goal.model_dump())
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@router.put("/{goal_id}", response_model=Goal)
def update_goal(goal_id: int, goal: GoalUpdate, db: Session = Depends(get_db)):
    """Update a goal"""
    existing_goal = db.get(GoalModel, goal_id)
    if not existing_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_dict = goal.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(existing_goal, field, value)

    db.commit()
    db.refresh(existing_goal)
    return existing_goal


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete a goal"""
    goal = db.get(GoalModel, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(goal)
    db.commit()
    return None
