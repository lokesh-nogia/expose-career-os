from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import UserProfile, JobPosting, JobSkill, AgentState
from app.services.readiness_engine import calculate_readiness
from app.services.salary_intelligence import analyze_salaries

class ObservationSnapshot:
    def __init__(self, new_jobs: int, new_high_demand_skill: str, readiness_change: float, salary_estimate: float, current_readiness: float, missing_skills: list):
        self.new_jobs = new_jobs
        self.new_high_demand_skill = new_high_demand_skill
        self.readiness_change = readiness_change
        self.salary_estimate = salary_estimate
        self.current_readiness = current_readiness
        self.missing_skills = missing_skills

    def to_dict(self) -> dict:
        return {
            "new_jobs": self.new_jobs,
            "new_high_demand_skill": self.new_high_demand_skill,
            "readiness_change": self.readiness_change,
            "salary_estimate": self.salary_estimate,
            "current_readiness": self.current_readiness,
            "missing_skills": self.missing_skills
        }

def observe_career_state(db: Session, profile: UserProfile) -> ObservationSnapshot:
    """
    Scans the current database state for job postings, market demand,
    user profile status, and readiness delta relative to the last recorded AgentState.
    """
    # 1. New jobs (jobs marked as pending review)
    new_jobs_count = db.query(JobPosting).filter(JobPosting.review_status == "pending").count()
    if new_jobs_count == 0:
        new_jobs_count = db.query(JobPosting).count()

    # 2. Identify top high demand skill that user is missing
    user_skills = [s.skill_name.lower() for s in profile.skills]
    top_skills = db.query(JobSkill.skill_name, func.count(JobSkill.id))\
        .group_by(JobSkill.skill_name)\
        .order_by(func.count(JobSkill.id).desc())\
        .all()
    
    new_high_demand_skill = "Kafka"  # Default fallback
    for skill_name, _ in top_skills:
        if skill_name.lower() not in user_skills:
            new_high_demand_skill = skill_name
            break

    # 3. Calculate current readiness and missing skills
    readiness_result = calculate_readiness(db, profile)
    current_readiness = readiness_result.score
    missing_skills = readiness_result.missing_skills

    # 4. Calculate readiness change based on last AgentState
    last_state = db.query(AgentState).filter(AgentState.user_profile_id == profile.id)\
        .order_by(AgentState.id.desc()).first()
    
    if last_state:
        readiness_change = round(current_readiness - last_state.current_readiness, 2)
    else:
        readiness_change = 0.0

    # 5. Salary estimate from salary intelligence
    salary_analysis = analyze_salaries(db, profile, missing_skills)
    salary_estimate = salary_analysis.estimated_market_salary

    return ObservationSnapshot(
        new_jobs=new_jobs_count,
        new_high_demand_skill=new_high_demand_skill,
        readiness_change=readiness_change,
        salary_estimate=salary_estimate,
        current_readiness=current_readiness,
        missing_skills=missing_skills
    )
