from sqlalchemy.orm import Session
from app.models.domain import UserProfile
from app.services.readiness_engine import calculate_readiness
from app.cognitive.forecasting_engine import forecast_outcomes
from app.cognitive.roi_engine import calculate_skills_roi
from app.cognitive.constraint_engine import evaluate_constraints
from app.cognitive.scenario_engine import simulate_scenarios
from app.cognitive.career_strategy_engine import generate_strategy
from app.cognitive.decision_engine import make_decisions

def generate_weekly_career_brief(db: Session, profile: UserProfile) -> dict:
    """
    Assembles the Weekly Executive Career Brief combining forecasts, skill ROIs,
    constraints, scenarios, strategy, and decision recommendations.
    """
    # Calculate baseline inputs
    readiness_res = calculate_readiness(db, profile)
    missing_skills = readiness_res.missing_skills
    
    # Run Cognitive Engines
    forecasts = forecast_outcomes(db, profile)
    roi_skills = calculate_skills_roi(db, missing_skills)
    constraints = evaluate_constraints(db, profile)
    scenarios = simulate_scenarios(db, profile)
    strategy = generate_strategy(db, profile)
    decisions = make_decisions(db, profile)

    # Extract specific summary stats
    current_market_value = forecasts["salary"]["current"]
    projected_market_value_90d = forecasts["salary"]["days_90"]
    
    highest_roi_skills = [s for s in roi_skills[:3]]  # Top 3 ROI skills
    
    return {
        "current_market_value": current_market_value,
        "projected_market_value_90d": projected_market_value_90d,
        "readiness": forecasts["readiness"],
        "salary": forecasts["salary"],
        "interview": forecasts["interview"],
        "skill_gaps": missing_skills,
        "highest_roi_skills": highest_roi_skills,
        "scenarios": scenarios,
        "strategy": strategy["timeline"],
        "constraints": constraints,
        "recommendations": decisions["recommendations"],
        "risks": decisions["risks"],
        "opportunities": decisions["opportunities"]
    }
