from sqlalchemy.orm import Session
from app.models.domain import UserProfile
from app.services.readiness_engine import calculate_readiness

def generate_strategy(db: Session, profile: UserProfile) -> dict:
    """
    Builds a long-term strategic timeline (6, 12, 18-month roadmap) mapping milestones and targets.
    """
    readiness_res = calculate_readiness(db, profile)
    missing = readiness_res.missing_skills
    
    # Estimate milestone focus based on actual profile gaps
    primary_gap = missing[0] if len(missing) > 0 else "System Design"
    secondary_gap = missing[1] if len(missing) > 1 else "Microservices"
    
    current_val = profile.current_salary
    target_val = profile.target_salary
    
    # Progression steps
    step_6m_comp = round(current_val + (target_val - current_val) * 0.4, 1)
    step_12m_comp = target_val
    step_18m_comp = round(target_val * 1.2, 1)

    return {
        "timeline": {
            "months_6": {
                "milestone": f"Close primary skill gap: Master {primary_gap}",
                "actions": [
                    f"Complete {primary_gap} theoretical modules & hands-on setup.",
                    f"Solve at least 15 practice questions in {primary_gap}.",
                    "Build a portfolio project showcasing this technology."
                ],
                "expected_compensation": step_6m_comp
            },
            "months_12": {
                "milestone": f"Transition to target role: {profile.target_role}",
                "actions": [
                    f"Acquire {secondary_gap} expertise and cloud certification.",
                    "Optimize resume variant and initiate active portal sourcing.",
                    "Perform mock interviews and negotiate offer letters."
                ],
                "expected_compensation": step_12m_comp
            },
            "months_18": {
                "milestone": "Consolidate and Scale Senior Standing",
                "actions": [
                    "Lead high-performance scaling architectural modules.",
                    "Contribute to technical strategy and mentor junior developers.",
                    "Secure leadership track designation in target organization."
                ],
                "expected_compensation": step_18m_comp
            }
        }
    }
