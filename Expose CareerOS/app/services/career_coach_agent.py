from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.domain import UserProfile, JobPosting, JobSkill, QuestionBank, InterviewQuestion

def generate_weekly_career_plan(
    db: Session, 
    profile: UserProfile, 
    missing_skills: List[str]
) -> Dict[str, Any]:
    """
    Generates a structured, action-oriented Weekly Career Plan:
    - Weekly Objective based on top roadmap gap
    - Curated task checklist
    - Expected readiness, salary, and interview prep gains
    """
    if not missing_skills:
        # Default fallback when all gaps are closed
        return {
            "weekly_objective": "Optimize Professional Assets & Scale Architectures",
            "tasks": [
                "Review System Design capstone architectures.",
                "Polish resume versions for high-scoring positions in the review queue.",
                "Practice Staff-level behavioral leadership scenarios."
            ],
            "expected_readiness_gain": "+1% Readiness",
            "expected_salary_impact": "0.0 LPA (Target Reached)",
            "expected_interview_readiness": "+0.5 Points"
        }

    # 1. Select the top missing skill gap
    top_skill = missing_skills[0]

    # 2. Select a curated practice question matching that skill to suggest
    suggested_q = db.query(QuestionBank).filter(
        QuestionBank.category.ilike(top_skill) | QuestionBank.question.ilike(f"%{top_skill}%")
    ).first()
    
    question_title = suggested_q.question[:45] + "..." if suggested_q else "internal engine architecture"

    # 3. Formulate Action Tasks
    tasks = [
        f"Complete curated study: {top_skill} implementation standards.",
        f"Solve and score '{question_title}' practice question in Interview Academy.",
        f"Document a project evidence log for your {top_skill} skill to boost Career Score."
    ]

    # 4. Calculate Expected Gains
    # Estimate gains based on profile targets
    salary_diff = max(1.0, profile.target_salary - profile.current_salary)
    estimated_salary_gain = round(min(3.0, 0.15 * salary_diff), 1)
    
    readiness_gain = 5 if len(missing_skills) > 1 else 10
    interview_gain = 2.0

    return {
        "weekly_objective": f"Improve {top_skill} Readiness & Close Key Market Gaps",
        "tasks": tasks,
        "expected_readiness_gain": f"+{readiness_gain}% Target Readiness",
        "expected_salary_impact": f"+{estimated_salary_gain} LPA potential premium",
        "expected_interview_readiness": f"+{interview_gain} Points in Academy"
    }
