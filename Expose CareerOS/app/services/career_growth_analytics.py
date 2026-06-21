from sqlalchemy.orm import Session
from app.models.domain import UserProfile, AgentState, JobApplication, InterviewQuestion, UserSkill

def get_growth_trends(db: Session, profile: UserProfile) -> dict:
    """
    Measures and aggregates career performance metrics over time, compiling
    historical timelines for skill growth, interview scores, applications, and salary projections.
    """
    # 1. Fetch historical states for timeline
    states = db.query(AgentState).filter(
        AgentState.user_profile_id == profile.id
    ).order_by(AgentState.id.asc()).all()

    timeline_points = []
    
    # 2. Extract values from historical states
    for idx, s in enumerate(states):
        import json
        try:
            obs = json.loads(s.last_observation) if s.last_observation else {}
            skills_count = len(obs.get("missing_skills", []))
        except Exception:
            skills_count = 0
            
        timeline_points.append({
            "run_index": idx + 1,
            "readiness": s.current_readiness,
            "salary_projection": s.current_salary_estimate,
            "skills_count": max(1, len(profile.skills) - skills_count)
        })

    # Fallback/seed default timeline points if no states are logged yet
    if not timeline_points:
        timeline_points = [
            {
                "run_index": 1,
                "readiness": 30.0,
                "salary_projection": profile.current_salary,
                "skills_count": max(1, len(profile.skills) - 2)
            },
            {
                "run_index": 2,
                "readiness": 38.0,
                "salary_projection": profile.current_salary + 0.5,
                "skills_count": len(profile.skills)
            }
        ]

    # 3. Calculate Interview growth (average score over time)
    resolved_questions = db.query(InterviewQuestion).filter(InterviewQuestion.score > 0).all()
    interview_scores_timeline = []
    accumulated_sum = 0
    
    for idx, q in enumerate(resolved_questions):
        accumulated_sum += q.score
        interview_scores_timeline.append({
            "index": idx + 1,
            "avg_score": round(accumulated_sum / (idx + 1), 2)
        })
        
    if not interview_scores_timeline:
        interview_scores_timeline = [{"index": 1, "avg_score": 6.5}]

    # 4. Calculate Application growth timeline (cumulative count by date)
    apps = db.query(JobApplication).order_by(JobApplication.applied_date.asc()).all()
    application_timeline = []
    cumulative_count = 0
    for idx, ap in enumerate(apps):
        cumulative_count += 1
        application_timeline.append({
            "date": ap.applied_date.isoformat(),
            "count": cumulative_count
        })
        
    if not application_timeline:
        application_timeline = [{"date": "2026-06-13", "count": 1}]

    return {
        "timeline": timeline_points,
        "interview_growth": interview_scores_timeline,
        "application_growth": application_timeline,
        "summary": {
            "total_skills": len(profile.skills),
            "solved_questions": len(resolved_questions),
            "total_applications": len(apps),
            "current_valuation": timeline_points[-1]["salary_projection"] if timeline_points else profile.current_salary
        }
    }
