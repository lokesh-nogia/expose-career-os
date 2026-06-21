from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import UserProfile, UserSkill, UserSkillEvidence, InterviewQuestion
from app.services.readiness_engine import calculate_readiness
from app.services.salary_intelligence import analyze_salaries

def forecast_outcomes(db: Session, profile: UserProfile) -> dict:
    """
    Generates 30, 60, and 90-day projections for Career Readiness, Salary, and Interview readiness scores.
    """
    # 1. Base readiness
    readiness_res = calculate_readiness(db, profile)
    base_readiness = readiness_res.score
    missing_skills = readiness_res.missing_skills

    # Calculate velocity based on skills, evidence, and completed interviews
    user_skills_count = len(profile.skills)
    evidence_count = db.query(UserSkillEvidence).join(UserSkill).filter(
        UserSkill.user_profile_id == profile.id
    ).count()
    solved_count = db.query(InterviewQuestion).filter(InterviewQuestion.score > 0).count()
    
    velocity = 0.2 + (evidence_count * 0.08) + (solved_count * 0.05)

    # 2. Base salary
    salary_analysis = analyze_salaries(db, profile, missing_skills)
    base_salary = salary_analysis.estimated_market_salary
    salary_gap = salary_analysis.salary_gap
    
    # 3. Base interview performance (average score out of 10)
    avg_interview_score_row = db.query(func.avg(InterviewQuestion.score)).filter(InterviewQuestion.score > 0).first()
    base_interview_score = float(avg_interview_score_row[0]) if avg_interview_score_row and avg_interview_score_row[0] else 5.0

    # Projections
    readiness_30 = round(min(100.0, base_readiness + (velocity * 30)), 1)
    readiness_60 = round(min(100.0, base_readiness + (velocity * 60)), 1)
    readiness_90 = round(min(100.0, base_readiness + (velocity * 90)), 1)

    # Salary growth corresponds to closed skill gaps
    salary_growth_rate = 0.05 * velocity  # LPA gained per day of active practice
    salary_30 = round(min(profile.target_salary, base_salary + (salary_growth_rate * 30)), 1)
    salary_60 = round(min(profile.target_salary, base_salary + (salary_growth_rate * 60)), 1)
    salary_90 = round(min(profile.target_salary, base_salary + (salary_growth_rate * 90)), 1)
    
    # Ensure projections don't fall below base salary
    salary_30 = max(base_salary, salary_30)
    salary_60 = max(base_salary, salary_60)
    salary_90 = max(base_salary, salary_90)

    # Interview score growth
    interview_growth_rate = 0.03 * velocity
    interview_30 = round(min(10.0, base_interview_score + (interview_growth_rate * 30)), 1)
    interview_60 = round(min(10.0, base_interview_score + (interview_growth_rate * 60)), 1)
    interview_90 = round(min(10.0, base_interview_score + (interview_growth_rate * 90)), 1)

    return {
        "readiness": {
            "current": base_readiness,
            "days_30": readiness_30,
            "days_60": readiness_60,
            "days_90": readiness_90
        },
        "salary": {
            "current": base_salary,
            "days_30": salary_30,
            "days_60": salary_60,
            "days_90": salary_90
        },
        "interview": {
            "current": base_interview_score,
            "days_30": interview_30,
            "days_60": interview_60,
            "days_90": interview_90
        }
    }
