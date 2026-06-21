from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import UserProfile, UserSkill, UserSkillEvidence, InterviewQuestion
from app.services.readiness_engine import calculate_readiness

def predict_readiness(db: Session, profile: UserProfile) -> dict:
    """
    Predicts the user's career readiness levels and forecasts trajectories for
    30, 60, and 90-day intervals based on evidence entries, roadmap rates, and quiz scores.
    """
    # 1. Target role readiness (computed from market demands)
    readiness_res = calculate_readiness(db, profile)
    target_readiness = readiness_res.score

    # 2. Current role readiness (generic estimate of competency in current role skills)
    user_skills_count = len(profile.skills)
    current_readiness = min(100.0, 50.0 + (user_skills_count * 8.0))

    # 3. Calculate execution velocity (based on solved questions and evidence additions)
    evidence_count = db.query(UserSkillEvidence).join(UserSkill).filter(
        UserSkill.user_profile_id == profile.id
    ).count()

    solved_quizzes_count = db.query(InterviewQuestion).filter(
        InterviewQuestion.score >= 7
    ).count()

    # Base growth velocity per day (percent readiness gain)
    # E.g. having evidence and high quiz scores implies faster acquisition of target skills
    growth_velocity = 0.2 + (evidence_count * 0.08) + (solved_quizzes_count * 0.05)

    # 4. Projections over time
    proj_30 = round(min(100.0, target_readiness + (growth_velocity * 30)), 1)
    proj_60 = round(min(100.0, target_readiness + (growth_velocity * 60)), 1)
    proj_90 = round(min(100.0, target_readiness + (growth_velocity * 90)), 1)

    return {
        "current_role_readiness": round(current_readiness, 1),
        "target_role_readiness": round(target_readiness, 1),
        "velocity": round(growth_velocity, 2),
        "projections": {
            "days_30": proj_30,
            "days_60": proj_60,
            "days_90": proj_90
        }
    }
