from sqlalchemy.orm import Session
from app.models.domain import JobPosting, JobSkill

def get_skill_roi_profile(db: Session, skill_name: str) -> dict:
    """
    Calculates ROI details for a given skill.
    Formula: ROI = (Demand Score * Salary Impact Weight * 10) / Est Learning Time
    """
    total_jobs = db.query(JobPosting).count()
    skill_demand_count = db.query(JobSkill).filter(JobSkill.skill_name.ilike(skill_name)).count()
    
    demand_pct = (skill_demand_count / total_jobs * 100.0) if total_jobs > 0 else 40.0
    demand_pct = round(demand_pct, 1)

    # Estimate learning time (Hours) based on technical complexity
    skill_lower = skill_name.lower()
    if skill_lower in ["git", "sql", "linux", "rest apis", "restapi"]:
        learning_time = 10
    elif skill_lower in ["docker", "mongodb", "postgresql", "mysql", "redis", "springboot", "spring boot"]:
        learning_time = 20
    elif skill_lower in ["kafka", "system design", "java", "microservices"]:
        learning_time = 30
    elif skill_lower in ["aws", "azure", "kubernetes", "openSearch", "multithreading"]:
        learning_time = 40
    else:
        learning_time = 20

    # Determine Salary Impact and weight
    if demand_pct > 50:
        salary_impact = "High"
        salary_weight = 3.0
    elif demand_pct > 25:
        salary_impact = "Medium"
        salary_weight = 2.0
    else:
        salary_impact = "Low"
        salary_weight = 1.0

    # Custom override for high-value topics
    if skill_lower in ["system design", "microservices", "kafka", "aws"]:
        salary_impact = "High"
        salary_weight = 3.0

    # Calculate ROI Score (0-100 scale)
    raw_roi = (demand_pct * salary_weight * 10.0) / learning_time
    roi_score = min(100.0, max(10.0, round(raw_roi, 1)))

    return {
        "skill": skill_name,
        "learning_time_hours": learning_time,
        "demand_percentage": demand_pct,
        "salary_impact": salary_impact,
        "roi_score": int(roi_score)
    }

def calculate_skills_roi(db: Session, missing_skills: list) -> list:
    """Calculates ROI scores for a list of skills, returning them ordered by ROI descending."""
    profiles = []
    for skill in missing_skills:
        profiles.append(get_skill_roi_profile(db, skill))
    profiles.sort(key=lambda x: x["roi_score"], reverse=True)
    return profiles
