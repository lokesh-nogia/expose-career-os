from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import UserProfile, JobPosting, JobSkill
from app.models.contracts import ReadinessResult

def calculate_readiness(db: Session, profile: UserProfile) -> ReadinessResult:
    """
    Computes a readiness score based on how many core skills 
    for the user's target_role they have acquired.
    """
    target = profile.target_role.strip() if profile.target_role else "Backend Engineer"
    
    # Query job postings matching target role
    target_jobs = db.query(JobPosting).filter(
        JobPosting.title.ilike(f"%{target}%")
    ).all()
    
    # Fallback to all jobs if no role-specific listings exist
    if not target_jobs:
        target_jobs = db.query(JobPosting).all()
        
    job_ids = [j.id for j in target_jobs]
    total_target_jobs = len(job_ids)
    
    if total_target_jobs == 0:
        return ReadinessResult(
            score=0.0,
            target_role=target,
            matched_skills=[],
            missing_skills=[],
            explanation="No market jobs found in the database. Please import jobs via CSV."
        )

    # Count core skills demanded in these jobs
    skills_query = db.query(
        JobSkill.skill_name,
        func.count(JobSkill.id)
    ).filter(
        JobSkill.job_posting_id.in_(job_ids)
    ).group_by(JobSkill.skill_name).order_by(
        func.count(JobSkill.id).desc()
    ).limit(8).all()
    
    core_demands = [s[0] for s in skills_query]
    
    # Map user skills
    user_skills = [s.skill_name.lower() for s in profile.skills]
    
    matched = []
    missing = []
    
    for skill in core_demands:
        if skill.lower() in user_skills:
            matched.append(skill)
        else:
            missing.append(skill)
            
    # Calculate score
    total_core = len(core_demands)
    score = (len(matched) / total_core * 100.0) if total_core > 0 else 0.0
    score = round(score, 1)
    
    explanation = (
        f"You possess {len(matched)} of the {total_core} core skills demanded in "
        f"market job postings matching '{target}'. Acquisition of remaining skills "
        f"will align your profile closer to target positions."
    )

    return ReadinessResult(
        score=score,
        target_role=target,
        matched_skills=matched,
        missing_skills=missing,
        explanation=explanation
    )
