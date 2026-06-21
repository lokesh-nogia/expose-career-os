from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.helpers import render_template, templates
from app.services import (
    job_service, job_discovery_service, resume_intelligence, 
    job_match_agent, cover_letter_agent, notification_service,
    profile_service
)
from app.models.domain import (
    JobCreate, JobUpdate, JobPosting, JobApplication, 
    ApplicationOutcome, Notification
)

router = APIRouter()

@router.get("/jobs")
def get_jobs(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Serves the job applications page. Returns HTML lists for HTMX requests."""
    jobs = job_service.list_jobs(db, search=search, status=status)
    
    # Check if this is an HTMX request to return just the list fragment
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            request=request,
            name="components/job_list.html",
            context={
                "jobs": jobs
            }
        )
        
    return render_template(
        "pages/jobs.html",
        request=request,
        db=db,
        active_page="jobs",
        jobs=jobs,
        selected_status=status or "",
        search_query=search or ""
    )

@router.post("/jobs")
def create_job(
    request: Request,
    company: str = Form(...),
    position: str = Form(...),
    status: str = Form(...),
    applied_date: str = Form(...),
    notes: Optional[str] = Form(""),
    db: Session = Depends(get_db)
):
    """Handles adding a new job application and returns the updated job list."""
    parsed_date = date.fromisoformat(applied_date) if applied_date else date.today()
    
    job_data = JobCreate(
        company=company,
        position=position,
        status=status,
        applied_date=parsed_date,
        notes=notes
    )
    
    job_service.create_job(db, job_data)
    
    # Fetch fresh job list and statistics
    jobs = job_service.list_jobs(db)
    stats = job_service.get_job_stats(db)
    
    # Trigger 'jobAdded' client event to reset/close the modal
    headers = {"HX-Trigger": "jobAdded"}
    
    return templates.TemplateResponse(
        request=request,
        name="components/job_list_with_stats.html",
        context={
            "jobs": jobs,
            "stats": stats
        },
        headers=headers
    )

@router.get("/jobs/{job_id}/edit")
def get_edit_row(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Returns the editing row template for a job card."""
    job = job_service.get_job(db, job_id)
    if not job:
        return Response(status_code=404)
        
    return templates.TemplateResponse(
        request=request,
        name="components/job_edit_card.html",
        context={
            "job": job
        }
    )

@router.get("/jobs/{job_id}/cancel")
def cancel_edit_row(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Cancels edit mode and returns the default job card component."""
    job = job_service.get_job(db, job_id)
    if not job:
        return Response(status_code=404)
        
    return templates.TemplateResponse(
        request=request,
        name="components/job_card.html",
        context={
            "job": job
        }
    )

@router.post("/jobs/{job_id}/edit")
def update_job(
    request: Request,
    job_id: int,
    company: str = Form(...),
    position: str = Form(...),
    status: str = Form(...),
    applied_date: str = Form(...),
    notes: Optional[str] = Form(""),
    db: Session = Depends(get_db)
):
    """Updates job details and returns its updated view component."""
    parsed_date = date.fromisoformat(applied_date) if applied_date else date.today()
    
    job_data = JobUpdate(
        company=company,
        position=position,
        status=status,
        applied_date=parsed_date,
        notes=notes
    )
    
    job = job_service.update_job(db, job_id, job_data)
    if not job:
        return Response(status_code=404)
        
    stats = job_service.get_job_stats(db)
    
    return templates.TemplateResponse(
        request=request,
        name="components/job_card_with_oob_stats.html",
        context={
            "job": job,
            "stats": stats
        }
    )

@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Deletes the job application from the database and returns OOB stats update."""
    success = job_service.delete_job(db, job_id)
    if not success:
        return Response(status_code=404)
        
    stats = job_service.get_job_stats(db)
    
    oob_html = f"""
    <div id="stats-total" hx-swap-oob="true" class="text-3xl font-extrabold text-slate-900 dark:text-white">{stats['total']}</div>
    <div id="stats-applied" hx-swap-oob="true" class="text-3xl font-extrabold text-blue-600 dark:text-blue-400">{stats['applied']}</div>
    <div id="stats-interviews" hx-swap-oob="true" class="text-3xl font-extrabold text-purple-600 dark:text-purple-400">{stats['interviews']}</div>
    <div id="stats-offers" hx-swap-oob="true" class="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">{stats['offers']}</div>
    """
    return Response(content=oob_html)

# ==========================================
# Phase 3 Refactored Queue & Sourcing Endpoints
# ==========================================

@router.post("/dashboard/discover")
def discover_jobs_endpoint(request: Request, db: Session = Depends(get_db)):
    """Triggers job discovery from configured real data sources (CSV)."""
    res = job_discovery_service.run_job_discovery(db, source_type="CSV")
    
    # Send Notification
    notification_service.create_notification(
        db=db,
        n_type="job_imported",
        message=f"Discovered {res['records_imported']} new matching jobs from CSV Ingestion."
    )
    
    return RedirectResponse(url="/", status_code=303)

@router.post("/dashboard/import-csv")
def import_csv_post(db: Session = Depends(get_db)):
    """Triggers CSV Ingestion Pipeline (retained for backward compatibility)."""
    res = job_discovery_service.run_job_discovery(db, source_type="CSV")
    notification_service.create_notification(
        db=db,
        n_type="job_imported",
        message=f"Discovered {res['records_imported']} new matching jobs from CSV Ingestion."
    )
    return Response(headers={"HX-Redirect": "/"})

@router.post("/jobs/queue/{posting_id}/approve")
def approve_posting(posting_id: int, db: Session = Depends(get_db)):
    """Approves a discovered opportunity, spawning custom resumes/cover letters and saving application package draft."""
    posting = db.query(JobPosting).filter(JobPosting.id == posting_id).first()
    if not posting:
        return Response(status_code=404)
        
    # Mark as approved in queue
    posting.review_status = "approved"
    
    # 1. Fetch user profile
    profile = profile_service.get_profile(db)
    
    # 2. Spawn resume variant
    resume_ver = resume_intelligence.create_resume_variant(
        db=db,
        profile=profile,
        job=posting,
        title=f"{posting.company} - {posting.title} Resume"
    )
    
    # 3. Generate cover letter and score
    from app.services.cover_letter_agent import generate_cover_letter_v2
    c_letter, confidence_score = generate_cover_letter_v2(db, profile, posting)
    
    # 4. Calculate Match Score
    match_res = job_match_agent.calculate_job_match(db, profile, posting)
    match_score = match_res["match_score"]
    
    # 5. Extract gaps and salary analysis
    missing_skills = match_res.get("missing_skills", [])
    from app.services.salary_intelligence import analyze_salaries
    salary_intel = analyze_salaries(db, profile, missing_skills)
    salary_analysis_text = f"Market Valuation: {salary_intel.estimated_market_salary} LPA. Current Salary Gap: {salary_intel.salary_gap} LPA."
    
    # 6. Save as ApplicationPackage draft
    from app.models.domain import ApplicationPackage
    import json
    package = ApplicationPackage(
        job_posting_id=posting.id,
        match_score=match_score,
        resume_version_id=resume_ver.id,
        cover_letter=c_letter,
        missing_skills=json.dumps(missing_skills),
        salary_analysis=salary_analysis_text,
        status="Draft"
    )
    db.add(package)
    
    # Create notification
    notification_service.create_notification(
        db=db,
        n_type="application_approved",
        message=f"Prepared Application Package Draft for {posting.title} at {posting.company}. Ready for human review."
    )
    
    db.commit()
    
    # Return empty response to delete card from DOM via HTMX
    return Response(content="")

@router.post("/jobs/queue/{posting_id}/reject")
def reject_posting(posting_id: int, db: Session = Depends(get_db)):
    """Rejects a discovered opportunity from the queue."""
    posting = db.query(JobPosting).filter(JobPosting.id == posting_id).first()
    if not posting:
        return Response(status_code=404)
        
    posting.review_status = "rejected"
    db.commit()
    
    return Response(content="")

@router.post("/jobs/queue/{posting_id}/save")
def save_posting(posting_id: int, db: Session = Depends(get_db)):
    """Saves a discovered opportunity to review it later."""
    posting = db.query(JobPosting).filter(JobPosting.id == posting_id).first()
    if not posting:
        return Response(status_code=404)
        
    posting.review_status = "saved"
    db.commit()
    
    return Response(content="")

@router.post("/jobs/applications/outcome")
def log_outcome_endpoint(
    job_posting_id: int = Form(...),
    result: str = Form(...),
    notes: Optional[str] = Form(""),
    db: Session = Depends(get_db)
):
    """Logs the recruitment outcome of a job application for learning matching weights."""
    # Find matching application posting
    posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
    if not posting:
        return Response(status_code=404)
        
    # Query if outcome already exists
    outcome = db.query(ApplicationOutcome).filter(
        ApplicationOutcome.job_posting_id == job_posting_id
    ).first()
    
    profile = profile_service.get_profile(db)
    match_res = job_match_agent.calculate_job_match(db, profile, posting)

    if not outcome:
        outcome = ApplicationOutcome(
            job_posting_id=job_posting_id,
            opportunity_score=match_res["match_score"],
            result=result,
            notes=notes
        )
        db.add(outcome)
    else:
        outcome.result = result
        outcome.notes = notes
        
    # Trigger notification
    notification_service.create_notification(
        db=db,
        n_type="outcome_logged",
        message=f"Logged recruitment outcome: '{result}' for position at {posting.company}."
    )
    
    db.commit()
    return Response(content="Outcome saved successfully.")
