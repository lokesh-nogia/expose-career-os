from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting, JobSkill
from app.models.contracts import OpportunityResult

def score_opportunity(
    db: Session, 
    job: JobPosting, 
    profile: UserProfile
) -> OpportunityResult:
    """
    Scores an ingested JobPosting from 0 to 100 based on alignment with the user:
    - Skill Match: 40%
    - Salary Match: 30%
    - Career Growth Potential: 20%
    - Goal Alignment: 10%
    """
    reasons = []
    
    # 1. Skill Match (40%)
    job_skills = [s.skill_name.lower() for s in job.skills]
    user_skills = [s.skill_name.lower() for s in profile.skills]
    
    if job_skills:
        matched_skills = [s for s in job_skills if s in user_skills]
        skill_match_ratio = len(matched_skills) / len(job_skills)
        skill_score = skill_match_ratio * 40.0
        
        if skill_match_ratio >= 0.7:
            reasons.append(f"Strong skill match ({len(matched_skills)}/{len(job_skills)} skills matched)")
        elif skill_match_ratio >= 0.4:
            reasons.append(f"Moderate skill match ({len(matched_skills)}/{len(job_skills)} skills matched)")
        else:
            reasons.append(f"Low skill match (Missing core required skills: {', '.join([s for s in job_skills if s not in user_skills][:3])})")
    else:
        # If no skills are defined in the posting, default to neutral score
        skill_score = 25.0
        reasons.append("No specific skills required in job posting details")

    # 2. Salary Match (30%)
    # If job salary >= target, full 30. If less, scale down.
    if profile.target_salary > 0.0 and job.salary > 0.0:
        if job.salary >= profile.target_salary:
            salary_score = 30.0
            reasons.append(f"Salary is above your target ({job.salary} {profile.target_timeline or 'LPA'} vs Target {profile.target_salary})")
        else:
            ratio = job.salary / profile.target_salary
            salary_score = ratio * 30.0
            reasons.append(f"Salary is below target ({job.salary} LPA vs Target {profile.target_salary})")
    else:
        salary_score = 15.0
        reasons.append("Salary details or target figures are unconfigured")

    # 3. Career Growth (20%)
    # Look for terms like "Senior", "Lead", "Architect" or skills like "System Design"
    growth_score = 0.0
    growth_reasons = []
    
    title_lower = job.title.lower()
    if "senior" in title_lower or "sde iii" in title_lower or "lead" in title_lower or "architect" in title_lower:
        growth_score += 10.0
        growth_reasons.append("Seniority tier role")
        
    # Check if job requires System Design or Microservices
    for sk in job_skills:
        if "system design" in sk or "architecture" in sk or "microservices" in sk:
            growth_score += 10.0
            growth_reasons.append("Involves high-level architectural design")
            break
            
    if growth_score > 0.0:
        reasons.append(f"High growth potential: {', '.join(growth_reasons)}")
    else:
        reasons.append("Standard growth potential role")
        growth_score = 5.0

    # 4. Goal Alignment (10%)
    # Does title match target role?
    goal_score = 0.0
    if profile.target_role and profile.target_role.lower() in title_lower:
        goal_score = 10.0
        reasons.append(f"Job title aligns directly with target role '{profile.target_role}'")
    else:
        goal_score = 2.0

    total_score = round(skill_score + salary_score + growth_score + goal_score, 1)

    return OpportunityResult(
        job_posting_id=job.id,
        title=job.title,
        company=job.company,
        score=total_score,
        reasons=reasons
    )
