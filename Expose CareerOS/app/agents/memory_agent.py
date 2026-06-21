import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.domain import AgentState, RecommendationHistory, UserProfile

class CareerEvent:
    def __init__(self, event_type: str, description: str, timestamp: datetime = None):
        self.event_type = event_type
        self.description = description
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat()
        }

def log_agent_state(
    db: Session,
    profile_id: int,
    goal: str,
    roadmap: dict,
    readiness: float,
    salary_estimate: float,
    recommendations: list,
    observation: dict,
    plan: dict,
    outcome: dict
) -> AgentState:
    """Persists a snapshot of the current Agent State into the database."""
    state = AgentState(
        user_profile_id=profile_id,
        current_goal=goal,
        current_roadmap=json.dumps(roadmap),
        current_readiness=readiness,
        current_salary_estimate=salary_estimate,
        current_recommendations=json.dumps(recommendations),
        last_observation=json.dumps(observation),
        last_plan=json.dumps(plan),
        last_outcome=json.dumps(outcome)
    )
    db.add(state)
    db.commit()
    db.refresh(state)
    return state

def record_recommendation_history(
    db: Session,
    recommendation_text: str,
    accepted: bool = False,
    rejected: bool = False,
    outcome: str = "Pending"
) -> RecommendationHistory:
    """Logs a recommendation and its status to prevent duplicates or repeat rejections."""
    history = RecommendationHistory(
        recommendation=recommendation_text,
        accepted=accepted,
        rejected=rejected,
        outcome=outcome
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def get_historical_readiness(db: Session, profile_id: int) -> list[dict]:
    """Retrieves readiness score timeline points for the profile."""
    states = db.query(AgentState).filter(AgentState.user_profile_id == profile_id)\
        .order_by(AgentState.id.asc()).all()
    
    return [
        {
            "id": s.id,
            "readiness": s.current_readiness,
            "timestamp": s.id  # Sequential sequence identifier
        }
        for s in states
    ]

def get_historical_salaries(db: Session, profile_id: int) -> list[dict]:
    """Retrieves salary estimate timeline points for the profile."""
    states = db.query(AgentState).filter(AgentState.user_profile_id == profile_id)\
        .order_by(AgentState.id.asc()).all()
    
    return [
        {
            "id": s.id,
            "salary": s.current_salary_estimate,
            "timestamp": s.id
        }
        for s in states
    ]
