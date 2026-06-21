from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.helpers import render_template, templates
from app.config import FEATURE_FLAGS
from app.models.domain import UserProfile, UserSkill, JobPosting, JobApplication, ImportRun, Notification, Resume, ResumeVersion, RecommendationHistory, AgentState, ApplicationPackage
from app.services import (
    profile_service, roadmap_engine, salary_intelligence, 
    readiness_engine, daily_mission_engine, opportunity_engine, 
    market_trend_engine, career_score_engine, discovery_scheduler,
    career_coach_agent, notification_service, job_match_agent, cover_letter_agent
)
from app.agents.orchestrator import run_orchestration_loop
from app.agents.memory_agent import record_recommendation_history, get_historical_readiness, get_historical_salaries

router = APIRouter()

@router.get("/")
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """Serves the Career OS Workstation Dashboard. Enforces onboarding wizard redirection."""
    profile = profile_service.get_profile(db)
    
    # 1. Enforce Onboarding wizard redirection
    if not profile.is_onboarded:
        return RedirectResponse(url="/onboarding")

    # 2. Run Career Engines under Feature Flags
    user_skills = [sk.skill_name for sk in profile.skills]
    
    trends = market_trend_engine.analyze_market_trends(db)
    demanded_skills = [s["skill_name"] for s in trends["demanded"]]
    
    # Gap analysis
    missing_skills = [s for s in demanded_skills if s.lower() not in [u.lower() for u in user_skills]]
    
    # Compute scores using engines
    roadmap = None
    if FEATURE_FLAGS.get("roadmap_engine"):
        roadmap = roadmap_engine.generate_roadmap(db, profile, missing_skills)
        
    salary_intel = None
    if FEATURE_FLAGS.get("salary_engine"):
        salary_intel = salary_intelligence.analyze_salaries(db, profile, missing_skills)
        
    readiness = None
    if FEATURE_FLAGS.get("readiness_engine"):
        readiness = readiness_engine.calculate_readiness(db, profile)

    # Opportunity review queue (pending jobs) with match scores
    queue_with_scores = []
    total_postings = db.query(JobPosting).count()
    
    if FEATURE_FLAGS.get("opportunity_engine"):
        pending_jobs = db.query(JobPosting).filter(JobPosting.review_status == "pending").all()
        for job in pending_jobs:
            match_info = job_match_agent.calculate_job_match(db, profile, job)
            # Generate cover letter dynamically for modal review
            c_letter = cover_letter_agent.generate_cover_letter(db, profile, job)
            queue_with_scores.append({
                "job": job,
                "match": match_info,
                "cover_letter": c_letter
            })
        # Sort queue by match score descending
        queue_with_scores.sort(key=lambda x: x["match"]["match_score"], reverse=True)

    # Run Orchestrator Loop
    orch_result = run_orchestration_loop(db, profile)

    daily_mission = None
    if FEATURE_FLAGS.get("daily_mission"):
        daily_mission = orch_result.daily_mission

    career_score = None
    if FEATURE_FLAGS.get("career_score_engine"):
        career_score = career_score_engine.calculate_career_score(db, profile)

    # 3. Phase 3 Refactor Features
    freshness = None
    if FEATURE_FLAGS.get("discovery_scheduler"):
        freshness = discovery_scheduler.check_data_freshness(db)

    coach_plan = None
    if FEATURE_FLAGS.get("career_coach"):
        coach_plan = career_coach_agent.generate_weekly_career_plan(db, profile, missing_skills)

    notifications = []
    if FEATURE_FLAGS.get("notifications"):
        notifications = notification_service.list_notifications(db, unread_only=True)

    # Fetch latest resumes list for Resume intelligence panel
    latest_resumes = db.query(Resume).filter(Resume.user_profile_id == profile.id).all()
    resumes_data = []
    for r in latest_resumes:
        v = db.query(ResumeVersion).filter(ResumeVersion.resume_id == r.id).order_by(ResumeVersion.version_number.desc()).first()
        if v:
            resumes_data.append({"resume": r, "version": v})

    # Recent activities
    activities = []
    import_runs = db.query(ImportRun).order_by(ImportRun.completed_at.desc()).limit(3).all()
    for run in import_runs:
        activities.append({
            "type": "import",
            "icon": "database",
            "title": f"Discovery Run: {run.status}",
            "desc": f"Processed jobs (Imported: {run.imported_records})",
            "date": run.completed_at.strftime("%b %d, %I:%M %p")
        })

    apps = db.query(JobApplication).order_by(JobApplication.applied_date.desc()).limit(2).all()
    for ap in apps:
        activities.append({
            "type": "application",
            "icon": "briefcase",
            "title": f"Funnel Status: {ap.status}",
            "desc": f"{ap.position} at {ap.company}",
            "date": ap.applied_date.strftime("%b %d, %Y")
        })

    # 4. Phase 5 Analytics & Workflows
    from app.models.domain import ApplicationPackage
    from app.services.outcome_analyzer import analyze_outcomes
    from app.services.readiness_prediction import predict_readiness
    from app.services.career_growth_analytics import get_growth_trends
    
    draft_packages = db.query(ApplicationPackage).filter(ApplicationPackage.status != "Submitted").all()
    outcomes = analyze_outcomes(db)
    predictions = predict_readiness(db, profile)
    growth_trends = get_growth_trends(db, profile)
    recs_effectiveness = db.query(RecommendationHistory).all()

    return render_template(
        "pages/dashboard.html",
        request=request,
        db=db,
        active_page="dashboard",
        profile=profile,
        career_score=career_score,
        readiness=readiness,
        salary_intel=salary_intel,
        roadmap=roadmap,
        daily_mission=daily_mission,
        trends=trends,
        queue_jobs=queue_with_scores[:5],  # limit to top 5 for dashboard
        total_postings=total_postings,
        activities=activities[:5],
        feature_flags=FEATURE_FLAGS,
        freshness=freshness,
        coach_plan=coach_plan,
        notifications=notifications,
        resumes_data=resumes_data,
        recommendations=orch_result.recommendations,
        adjustments=orch_result.adjustments,
        packages=draft_packages,
        outcomes=outcomes,
        predictions=predictions,
        growth_trends=growth_trends,
        recs_effectiveness=recs_effectiveness
    )

@router.get("/onboarding")
def get_onboarding(request: Request):
    """Serves the onboarding tab view."""
    return templates.TemplateResponse(
        request=request,
        name="pages/onboarding.html",
        context={}
    )

@router.post("/onboarding/submit")
async def handle_onboarding_submit(
    request: Request,
    full_name: str = Form(...),
    current_role: str = Form(...),
    experience_years: int = Form(...),
    current_salary: float = Form(...),
    target_role: str = Form(...),
    target_salary: float = Form(...),
    target_timeline: str = Form(...),
    db: Session = Depends(get_db)
):
    """Saves onboarding wizard specifications and initializes profile states."""
    profile = profile_service.get_profile(db)
    
    profile.full_name = full_name
    profile.current_role = current_role
    profile.experience_years = experience_years
    profile.current_salary = current_salary
    profile.target_role = target_role
    profile.target_salary = target_salary
    profile.target_timeline = target_timeline
    profile.is_onboarded = True
    
    db.query(UserSkill).filter(UserSkill.user_profile_id == profile.id).delete()
    
    form_data = await request.form()
    for key, value in form_data.items():
        if key.startswith("skill_check_"):
            skill_name = key.replace("skill_check_", "")
            
            if skill_name == "SpringBoot":
                skill_name = "Spring Boot"
            elif skill_name == "RESTAPIs":
                skill_name = "REST APIs"
                
            skill_level = form_data.get(f"level_{key.replace('skill_check_', '')}", "Beginner")
            
            user_sk = UserSkill(
                user_profile_id=profile.id,
                skill_name=skill_name,
                level=skill_level
            )
            db.add(user_sk)
            
    db.commit()
    
    # Send welcome notification
    notification_service.create_notification(
        db=db,
        n_type="system",
        message="Welcome to Expose Autospy Career Growth Operating System! Setup complete."
    )
    
    return RedirectResponse(url="/", status_code=303)

# ==========================================
# Phase 3 Notifications Read Endpoint
# ==========================================

@router.post("/dashboard/notifications/read")
def read_all_notifications(db: Session = Depends(get_db)):
    """Marks all unread notifications as read."""
    notification_service.mark_all_as_read(db)
    return Response(content="All notifications marked read.")

@router.post("/dashboard/notifications/{notification_id}/read")
def read_single_notification(notification_id: int, db: Session = Depends(get_db)):
    """Marks a single notification as read."""
    notification_service.mark_as_read(db, notification_id)
    return Response(content="")

@router.post("/dashboard/agents/approve")
def approve_agent_recommendation(topic: str = Form(...), db: Session = Depends(get_db)):
    """Approves a recommendation, marking it as accepted in history and preparing a study plan."""
    record_recommendation_history(db, recommendation_text=f"Learn {topic}", accepted=True, rejected=False, outcome="Approved")
    
    # Trigger a notification
    notification_service.create_notification(
        db=db,
        n_type="agent_approved",
        message=f"Approved recommendation to master '{topic}'. Actionable learning plan generated."
    )
    return Response(
        content=f"<div class='p-3 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/20 rounded-2xl text-[11px] text-emerald-800 dark:text-emerald-400 font-bold'><i data-lucide='check-circle' class='w-3.5 h-3.5 inline mr-1'></i> Approved learning of {topic}! Plan is ready in workspace.</div>"
    )

@router.post("/dashboard/agents/reject")
def reject_agent_recommendation(topic: str = Form(...), db: Session = Depends(get_db)):
    """Rejects a recommendation, marking it as rejected so it won't be recommended again."""
    record_recommendation_history(db, recommendation_text=f"Learn {topic}", accepted=False, rejected=True, outcome="Rejected")
    
    # Trigger a notification
    notification_service.create_notification(
        db=db,
        n_type="agent_rejected",
        message=f"Rejected recommendation to learn '{topic}'."
    )
    return Response(
        content=f"<div class='p-3 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/20 rounded-2xl text-[11px] text-rose-800 dark:text-rose-455 font-bold'><i data-lucide='x-circle' class='w-3.5 h-3.5 inline mr-1'></i> Rejection logged. Recommendations will adjust.</div>"
    )

@router.get("/dashboard/executive-report")
def get_executive_report(request: Request, db: Session = Depends(get_db)):
    """Generates the Weekly Executive Report with Career Cognitive insights."""
    from app.cognitive.career_brief_generator import generate_weekly_career_brief
    from app.cognitive.prioritization_engine import prioritize_opportunities
    
    profile = profile_service.get_profile(db)
    
    # Generate cognitive brief and prioritization queue
    brief = generate_weekly_career_brief(db, profile)
    priority_queue = prioritize_opportunities(db, profile)
    
    # Calculate trending parameters
    readiness_trend = get_historical_readiness(db, profile.id)
    salary_trend = get_historical_salaries(db, profile.id)
    
    # Simple funnel count
    total_apps = db.query(JobApplication).count()
    rejected_apps = db.query(JobApplication).filter(JobApplication.status == "Rejected").count()
    interview_apps = db.query(JobApplication).filter(JobApplication.status == "Interview").count()
    offer_apps = db.query(JobApplication).filter(JobApplication.status == "Offer").count()
    applied_apps = db.query(JobApplication).filter(JobApplication.status == "Applied").count()
    wishlist_apps = db.query(JobApplication).filter(JobApplication.status == "Wishlist").count()
    
    # Compute career health score
    career_score = None
    if FEATURE_FLAGS.get("career_score_engine"):
        career_score = career_score_engine.calculate_career_score(db, profile)
        
    # Calculate top recommendations
    orch = run_orchestration_loop(db, profile)
    
    return render_template(
        "pages/executive_report.html",
        request=request,
        db=db,
        profile=profile,
        readiness_trend=readiness_trend,
        salary_trend=salary_trend,
        funnel={
            "total": total_apps,
            "wishlist": wishlist_apps,
            "applied": applied_apps,
            "rejected": rejected_apps,
            "interview": interview_apps,
            "offer": offer_apps
        },
        career_health_score=career_score.score if career_score else 75,
        top_recommendations=brief["recommendations"],  # Overwrite with cognitive recommendations
        expected_salary_growth=round(brief["projected_market_value_90d"] - brief["current_market_value"], 1),
        adjustments=orch.adjustments,
        brief=brief,
        priority_queue=priority_queue
    )

@router.post("/dashboard/packages/{package_id}/approve")
def approve_application_package(package_id: int, db: Session = Depends(get_db)):
    """Approves an Application Package draft, moving its status to Approved."""
    package = db.query(ApplicationPackage).filter(ApplicationPackage.id == package_id).first()
    if not package:
        return Response(status_code=404)
        
    package.status = "Approved"
    db.commit()
    
    # Trigger notification
    notification_service.create_notification(
        db=db,
        n_type="package_approved",
        message=f"Approved Application Package for {package.job.title if package.job else 'Position'}."
    )
    
    return Response(
        content="<span class='px-2.5 py-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 font-extrabold rounded-lg text-[10px] uppercase'>Approved</span>"
    )

@router.post("/dashboard/packages/{package_id}/submit")
def submit_application_package(package_id: int, db: Session = Depends(get_db)):
    """Submits the application package, triggering execution and funnel updates."""
    from app.services import execution_service
    package = db.query(ApplicationPackage).filter(ApplicationPackage.id == package_id).first()
    if not package:
        return Response(status_code=404)
        
    execution_service.save_submission_record(db, package_id)
    
    # Trigger notification
    notification_service.create_notification(
        db=db,
        n_type="package_submitted",
        message=f"Submitted Application Package for {package.job.title if package.job else 'Position'}."
    )
    
    # Return empty response to remove card from DOM via HTMX
    return Response(content="")

@router.get("/dashboard/packages/{package_id}/export")
def export_application_package(package_id: int, db: Session = Depends(get_db)):
    """Exports application package details as a text document for manual transmission."""
    from app.services import execution_service
    pkg_data = execution_service.export_package(db, package_id)
    if not pkg_data:
        return Response(status_code=404)
        
    from fastapi.responses import PlainTextResponse
    export_text = (
        f"==================================================\n"
        f"APPLICATION PACKAGE: {pkg_data['job_title']} at {pkg_data['company']}\n"
        f"==================================================\n\n"
        f"--- COVER LETTER ---\n\n"
        f"{pkg_data['cover_letter']}\n\n"
        f"--- RESUME OPTIMIZATIONS ---\n\n"
        f"{pkg_data['resume']}\n"
    )
    return PlainTextResponse(
        content=export_text,
        headers={"Content-Disposition": f"attachment; filename=package_{package_id}.txt"}
    )
