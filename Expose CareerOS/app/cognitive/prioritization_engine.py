from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting
from app.services.readiness_engine import calculate_readiness
from app.services.job_match_agent import calculate_job_match
from app.cognitive.roi_engine import get_skill_roi_profile
from app.cognitive.constraint_engine import evaluate_constraints

def prioritize_opportunities(db: Session, profile: UserProfile) -> list[dict]:
    """
    Ranks competing career activities (Learning skills, Applying for jobs,
    Refining resumes, and practicing interview categories) into a single ordered queue.
    """
    priority_queue = []
    
    # 1. Gather Skill Learning Opportunities (based on ROI)
    readiness_res = calculate_readiness(db, profile)
    for skill in readiness_res.missing_skills[:3]:
        roi_prof = get_skill_roi_profile(db, skill)
        priority_queue.append({
            "type": "Skill Acquisition",
            "action": f"Learn {skill}",
            "description": f"Close core skill gap. Projected ROI score: {roi_prof['roi_score']}/100.",
            "priority_score": roi_prof["roi_score"],
            "time_required": f"{roi_prof['learning_time_hours']} hours"
        })

    # 2. Gather Job Opportunities (based on Job Match Score)
    pending_jobs = db.query(JobPosting).filter(JobPosting.review_status == "pending").limit(3).all()
    for job in pending_jobs:
        match_info = calculate_job_match(db, profile, job)
        score = match_info.get("match_score", 50.0)
        priority_queue.append({
            "type": "Job Application",
            "action": f"Apply to {job.title} at {job.company}",
            "description": f"High market alignment found (Match Score: {score}%).",
            "priority_score": int(score),
            "time_required": "1 hour"
        })

    # 3. Gather Weak Interview Practice areas (based on retention deficit)
    constraints = evaluate_constraints(db, profile)
    for weak_area in constraints.get("weak_areas", [])[:2]:
        priority_queue.append({
            "type": "Interview Academy",
            "action": f"Practice {weak_area} Questions",
            "description": f"Revise and practice modules to improve retention in {weak_area}.",
            "priority_score": 75,  # High fixed priority for core weak areas
            "time_required": "3 hours"
        })

    # 4. Gather Resume Refinement
    priority_queue.append({
        "type": "Resume Optimization",
        "action": "Refine Core Resume",
        "description": "Optimize achievements verbs and metrics formatting for ATS filters.",
        "priority_score": 70,
        "time_required": "2 hours"
    })

    # Sort queue by priority score descending
    priority_queue.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return priority_queue
