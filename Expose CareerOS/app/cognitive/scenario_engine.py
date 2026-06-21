from sqlalchemy.orm import Session
from app.models.domain import UserProfile

def simulate_scenarios(db: Session, profile: UserProfile) -> list[dict]:
    """
    Simulates and compares potential career directions: Backend, Platform, and AI Engineer.
    """
    user_skills = [s.skill_name.lower() for s in profile.skills]
    
    # Path Definitions
    scenarios_definition = [
        {
            "name": "Backend Engineer",
            "skills": ["Java", "Spring Boot", "PostgreSQL", "Kafka", "System Design"],
            "base_salary_premium": 0.0  # relative to profile.target_salary
        },
        {
            "name": "Platform Engineer",
            "skills": ["Kubernetes", "AWS", "Docker", "Terraform", "Linux", "Git"],
            "base_salary_premium": 3.0
        },
        {
            "name": "AI Engineer",
            "skills": ["Python", "Machine Learning", "PyTorch", "SQL", "Docker", "REST APIs"],
            "base_salary_premium": 6.0
        }
    ]
    
    results = []
    for definition in scenarios_definition:
        skills = definition["skills"]
        matched = [s for s in skills if s.lower() in user_skills]
        gaps = [s for s in skills if s.lower() not in user_skills]
        
        # Salary target calculation
        expected_salary = max(profile.target_salary, profile.current_salary) + definition["base_salary_premium"]
        expected_salary = round(expected_salary, 1)

        # Success Probability based on matched skills count
        success_prob = (len(matched) / len(skills)) * 100.0 if skills else 50.0
        success_prob = round(min(98.0, max(20.0, success_prob)), 1)
        
        # Time to readiness in weeks (estimate 4 weeks per missing skill)
        time_to_ready_weeks = len(gaps) * 4
        
        results.append({
            "name": definition["name"],
            "skills": skills,
            "matched_skills": matched,
            "skill_gap": gaps,
            "expected_salary": expected_salary,
            "time_to_readiness_weeks": time_to_ready_weeks,
            "probability_of_success": success_prob
        })
        
    return results
