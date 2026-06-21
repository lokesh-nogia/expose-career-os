from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting
from app.services.readiness_engine import calculate_readiness
from app.cognitive.forecasting_engine import forecast_outcomes
from app.cognitive.roi_engine import calculate_skills_roi
from app.cognitive.constraint_engine import evaluate_constraints
from app.cognitive.scenario_engine import simulate_scenarios

def make_decisions(db: Session, profile: UserProfile) -> dict:
    """
    Evaluates forecasts, ROI scores, constraints, and scenarios to generate
    prioritized recommendations, risks, and high-value opportunities.
    """
    # 1. Fetch dependencies
    readiness_res = calculate_readiness(db, profile)
    missing = readiness_res.missing_skills
    
    constraints = evaluate_constraints(db, profile)
    max_hours = constraints["hours_available"]
    weak_areas = constraints["weak_areas"]
    
    scenarios = simulate_scenarios(db, profile)
    forecasts = forecast_outcomes(db, profile)
    
    # Calculate ROI for missing skills
    roi_profiles = calculate_skills_roi(db, missing)
    
    recommendations = []
    
    # A. Add Top ROI Skill Acquisition Recommendation
    if roi_profiles:
        top_roi = roi_profiles[0]
        # Calculate time in weeks based on available hours
        weeks_needed = int(top_roi["learning_time_hours"] / (max_hours / 2))
        weeks_needed = max(1, weeks_needed)
        
        recommendations.append({
            "action": f"Learn {top_roi['skill']}",
            "reason": f"Appears in {top_roi['demand_percentage']}% of target jobs. Currently identified as a key skill gap.",
            "expected_impact": f"High (+{top_roi['roi_score']} points on ROI scale)",
            "time_required": f"{weeks_needed} Weeks ({top_roi['learning_time_hours']} hours total)",
            "confidence": "High",
            "risk": "Low"
        })
        
    # B. Add Weak Category Revision Recommendation
    for area in weak_areas[:1]:
        recommendations.append({
            "action": f"Practice {area} Questions",
            "reason": f"Active retention index in {area} is low. Revision is necessary to clear interview screening stages.",
            "expected_impact": "High (Reduces interview failure risk by 20%)",
            "time_required": "1 Week (3 hours of mock revision)",
            "confidence": "Medium-High",
            "risk": "Low"
        })

    # C. Add Job Review Recommendation if jobs exist
    pending_jobs_count = db.query(JobPosting).filter(JobPosting.review_status == "pending").count()
    if pending_jobs_count > 0:
        recommendations.append({
            "action": "Review Matched Jobs Queue",
            "reason": f"You have {pending_jobs_count} matched jobs pending review. Taking action helps populate the recruitment funnel.",
            "expected_impact": "Medium (Progresses active pipeline)",
            "time_required": "1 Hour",
            "confidence": "High",
            "risk": "Medium (Rejection risk exists for direct submissions)"
        })

    # 2. Identify Top Risks
    risks = []
    if len(missing) >= 4:
        risks.append({
            "title": "Broad Skill Gaps",
            "description": f"You are missing {len(missing)} core skills for '{profile.target_role}', which lowers your direct applicant screening compatibility."
        })
        
    if max_hours < 15:
        risks.append({
            "title": "Severe Time Limitations",
            "description": "With less than 15 hours per week available, acquiring complex technologies (like cloud architectures) will take multiple months."
        })

    # Check if target salary is highly aggressive
    if profile.current_salary > 0 and (profile.target_salary / profile.current_salary) > 2.0:
        risks.append({
            "title": "High Salary Target Disparity",
            "description": "Your target salary represents >100% growth. Requires flawless interview performance and mastery of top salary-premium skills."
        })

    # 3. Identify Top Opportunities
    opportunities = []
    if roi_profiles:
        opp_skill = roi_profiles[0]
        opportunities.append({
            "title": f"Skill Premium: {opp_skill['skill']}",
            "description": f"Learning {opp_skill['skill']} offers the highest career ROI ({opp_skill['roi_score']}/100) and unlocks an estimated market value premium."
        })
        
    # Find scenario with highest success rate
    scenarios_sorted = sorted(scenarios, key=lambda x: x["probability_of_success"], reverse=True)
    if scenarios_sorted:
        best_path = scenarios_sorted[0]
        opportunities.append({
            "title": f"Optimal Path: {best_path['name']}",
            "description": f"The '{best_path['name']}' path has your highest probability of success ({best_path['probability_of_success']}%) and shortest readiness timeline."
        })

    return {
        "recommendations": recommendations,
        "risks": risks,
        "opportunities": opportunities
    }
