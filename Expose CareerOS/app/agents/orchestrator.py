import json
from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting
from app.agents.observer_agent import observe_career_state
from app.agents.planner_agent import plan_career_actions
from app.agents.recommendation_agent import generate_recommendations
from app.agents.learning_agent import analyze_learning_progress
from app.agents.memory_agent import log_agent_state

class OrchestrationResult:
    def __init__(self, observation, weekly_plan, daily_plan, recommendations, adjustments, daily_mission):
        self.observation = observation
        self.weekly_plan = weekly_plan
        self.daily_plan = daily_plan
        self.recommendations = recommendations
        self.adjustments = adjustments
        self.daily_mission = daily_mission

    def to_dict(self) -> dict:
        return {
            "observation": self.observation.to_dict(),
            "weekly_plan": self.weekly_plan.to_dict(),
            "daily_plan": self.daily_plan.to_dict(),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "adjustments": [a.to_dict() for a in self.adjustments],
            "daily_mission": self.daily_mission
        }

def run_orchestration_loop(db: Session, profile: UserProfile) -> OrchestrationResult:
    """
    Executes the complete human-in-the-loop agent loop:
    Observe -> Plan -> Recommend -> Prepare -> Learn.
    Logs state to AgentState and returns active data.
    """
    # 1. Observe
    snapshot = observe_career_state(db, profile)

    # 2. Plan
    weekly_plan, daily_plan = plan_career_actions(snapshot)

    # 3. Recommend (Respecting memory/rejection history)
    recommendations = generate_recommendations(db, weekly_plan)

    # 4. Learn
    adjustments = analyze_learning_progress(db)

    # 5. Generate Daily Mission tasks
    daily_mission_tasks = []
    top_topic = weekly_plan.topics[0] if weekly_plan.topics else "System Design"
    
    daily_mission_tasks.append({
        "description": f"{top_topic} Module",
        "duration": "45 min",
        "linked_to": f"{top_topic} Readiness"
    })
    daily_mission_tasks.append({
        "description": "Interview Practice",
        "duration": "20 min",
        "linked_to": "Interview Preparation"
    })
    daily_mission_tasks.append({
        "description": f"Review {snapshot.new_jobs} Job Opportunities",
        "duration": "15 min",
        "linked_to": "Opportunity Sourcing"
    })

    daily_mission = {
        "tasks": daily_mission_tasks,
        "expected_readiness_gain": daily_plan.expected_readiness_gain
    }

    # 6. Memory Persist
    roadmap_data = {
        "phases": [
            {
                "title": f"Phase: Master {topic}",
                "skills": [topic]
            } for topic in weekly_plan.topics
        ]
    }

    goal = f"Obtain {profile.target_role} in {profile.target_timeline}"
    
    # Pack observation/plan/outcome details for state logging
    obs_dict = snapshot.to_dict()
    plan_dict = {
        "weekly": weekly_plan.to_dict(),
        "daily": daily_plan.to_dict()
    }
    outcome_dict = {
        "adjustments": [a.to_dict() for a in adjustments]
    }
    recs_list = [r.to_dict() for r in recommendations]

    log_agent_state(
        db=db,
        profile_id=profile.id,
        goal=goal,
        roadmap=roadmap_data,
        readiness=snapshot.current_readiness,
        salary_estimate=snapshot.salary_estimate,
        recommendations=recs_list,
        observation=obs_dict,
        plan=plan_dict,
        outcome=outcome_dict
    )

    return OrchestrationResult(
        observation=snapshot,
        weekly_plan=weekly_plan,
        daily_plan=daily_plan,
        recommendations=recommendations,
        adjustments=adjustments,
        daily_mission=daily_mission
    )
