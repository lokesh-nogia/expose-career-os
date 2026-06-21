from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import UserProfile, JobPosting, JobSkill, UserSkill
from app.models.contracts import SalaryAnalysisResult, SalaryImpactDetail

def analyze_salaries(
    db: Session, 
    profile: UserProfile, 
    missing_skills: List[str]
) -> SalaryAnalysisResult:
    """
    Computes market salary estimates and calculates potential impacts 
    for missing skills based on imported JobPostings.
    """
    # 1. Calculate General Market Average
    all_jobs = db.query(JobPosting).all()
    total_jobs_count = len(all_jobs)
    
    if total_jobs_count == 0:
        return SalaryAnalysisResult(
            estimated_market_salary=0.0,
            salary_gap=profile.target_salary,
            missing_high_value_skills=[],
            salary_impact_breakdown=[]
        )
        
    avg_market_salary = db.query(func.avg(JobPosting.salary)).scalar() or 0.0
    avg_market_salary = round(avg_market_salary, 1)

    # 2. Calculate Estimated Market Salary based on matching user skills
    # Let's find average salary of jobs that match at least one of user's skills
    user_skill_names = [s.skill_name.lower() for s in profile.skills]
    
    matching_jobs_query = db.query(JobPosting).join(JobSkill).filter(
        func.lower(JobSkill.skill_name).in_(user_skill_names)
    )
    
    matching_jobs_count = matching_jobs_query.count()
    if matching_jobs_count > 0:
        estimated_market_salary = db.query(func.avg(JobPosting.salary)).select_from(JobPosting).join(JobSkill).filter(
            func.lower(JobSkill.skill_name).in_(user_skill_names)
        ).scalar() or 0.0
        estimated_market_salary = round(estimated_market_salary, 1)
    else:
        # Fallback to general market average if no skills match
        estimated_market_salary = avg_market_salary

    # 3. Calculate salary gap (Target - Current)
    salary_gap = max(0.0, round(profile.target_salary - profile.current_salary, 1))

    # 4. Identify high value missing skills (found in jobs with salary > profile.current_salary)
    missing_high_value = []
    impact_details = []

    for skill in missing_skills:
        # Query average salary for this skill
        skill_jobs = db.query(JobPosting).join(JobSkill).filter(
            JobSkill.skill_name.ilike(skill)
        ).all()
        
        job_count = len(skill_jobs)
        if job_count == 0:
            continue
            
        skill_avg_salary = sum(j.salary for j in skill_jobs) / job_count
        
        if skill_avg_salary > profile.current_salary:
            missing_high_value.append(skill)
            
        # Compute dynamic salary premium compared to jobs without this skill
        non_skill_jobs = db.query(JobPosting).filter(
            ~JobPosting.id.in_([j.id for j in skill_jobs])
        ).all()
        
        non_skill_avg = sum(j.salary for j in non_skill_jobs) / len(non_skill_jobs) if non_skill_jobs else avg_market_salary
        premium = max(1.0, skill_avg_salary - non_skill_avg)
        
        # Ranges
        low_bound = round(max(0.5, premium - 0.8), 1)
        high_bound = round(premium + 1.2, 1)
        
        # Confidence
        if job_count >= 4:
            confidence = "High"
        elif job_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"
            
        impact_details.append(
            SalaryImpactDetail(
                skill_name=skill,
                confidence_level=confidence,
                estimated_impact=f"+{low_bound} to +{high_bound} LPA"
            )
        )

    # Sort breakdown by impact (descending)
    impact_details.sort(key=lambda x: x.estimated_impact, reverse=True)

    return SalaryAnalysisResult(
        estimated_market_salary=estimated_market_salary,
        salary_gap=salary_gap,
        missing_high_value_skills=missing_high_value[:4],
        salary_impact_breakdown=impact_details
    )
