from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models.domain import UserProfile, JobPosting, JobSkill

def calculate_job_match(
    db: Session, 
    profile: UserProfile, 
    job: JobPosting
) -> Dict[str, Any]:
    """
    Computes a matching compatibility score (0-100) between UserProfile and JobPosting:
    - Skill Match (40%): Overlap between user skills and job skills.
    - Experience Match (20%): Senority titles matched against experience years.
    - Salary Match (20%): Job salary compared with target salary bounds.
    - Role Match (20%): Overlap of words between target role and posting title.
    """
    # 1. Skill Match (40%)
    user_skills = [s.skill_name.lower().strip() for s in profile.skills]
    job_skills_query = job.skills
    job_skills = [sk.skill_name.lower().strip() for sk in job_skills_query]
    
    if not job_skills:
        skill_score = 100.0
        missing_skills = []
    else:
        shared_skills = [s for s in job_skills if s in user_skills]
        skill_score = (len(shared_skills) / len(job_skills)) * 100.0
        missing_skills = [sk.skill_name for sk in job_skills_query if sk.skill_name.lower().strip() not in user_skills]

    # 2. Experience Match (20%)
    # Title analysis for seniority expectations
    title_lower = job.title.lower()
    required_years = 0
    if any(keyword in title_lower for keyword in ["staff", "principal", "architect", "manager"]):
        required_years = 8
    elif any(keyword in title_lower for keyword in ["senior", "sr.", "iii", "lead"]):
        required_years = 5
    elif any(keyword in title_lower for keyword in ["intermediate", "ii", "mid"]):
        required_years = 2
    else:
        required_years = 0

    if profile.experience_years >= required_years:
        experience_score = 100.0
    else:
        experience_score = max(0.0, 100.0 - (required_years - profile.experience_years) * 20.0)

    # 3. Salary Match (20%)
    if not job.salary:
        salary_score = 80.0  # Neutral fallback when salary is hidden
    else:
        # If job salary meets target, give full score
        if job.salary >= profile.target_salary:
            salary_score = 100.0
        elif job.salary >= profile.current_salary:
            # Scale proportionally between current and target
            range_diff = max(1.0, profile.target_salary - profile.current_salary)
            salary_score = 70.0 + 30.0 * ((job.salary - profile.current_salary) / range_diff)
        else:
            # Below current salary
            salary_score = max(0.0, 50.0 * (job.salary / max(1.0, profile.current_salary)))

    # 4. Role Match (20%)
    # Keyword intersection
    target_words = set(profile.target_role.lower().split())
    title_words = set(job.title.lower().split())
    if not target_words:
        role_score = 80.0
    else:
        overlap = target_words.intersection(title_words)
        role_score = (len(overlap) / len(target_words)) * 100.0

    # Total Score
    total_score = round(
        (skill_score * 0.4) + 
        (experience_score * 0.2) + 
        (salary_score * 0.2) + 
        (role_score * 0.2), 
        1
    )

    recommended_resume = f"{job.company} - {job.title} Resume"

    return {
        "match_score": total_score,
        "recommended_resume": recommended_resume,
        "missing_skills": missing_skills,
        "breakdown": {
            "skill_match": round(skill_score, 1),
            "experience_match": round(experience_score, 1),
            "salary_match": round(salary_score, 1),
            "role_match": round(role_score, 1)
        }
    }
