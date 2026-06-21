import json
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.domain import ApplicationPackage, ApplicationOutcome, JobPosting, JobApplication, JobCreate
from app.services.job_service import create_job

def export_package(db: Session, package_id: int) -> dict:
    """
    Exports the customized resume variant and the tailored cover letter
    from the application package as a structured text document.
    """
    pkg = db.query(ApplicationPackage).filter(ApplicationPackage.id == package_id).first()
    if not pkg:
        return {}
    
    resume_ver = pkg.resume_version
    resume_content = ""
    if resume_ver:
        # Load experience bullet details cleanly if possible
        try:
            exp_data = json.loads(resume_ver.experience)
            exp_str = ""
            for job in exp_data:
                bullets_joined = "\n  - ".join(job.get("bullets", []))
                exp_str += f"\n* {job.get('position')} at {job.get('company')}:\n  - {bullets_joined}\n"
        except Exception:
            exp_str = resume_ver.experience

        resume_content = (
            f"Resume Title: {resume_ver.summary[:40]}...\n"
            f"ATS Match Score: {resume_ver.match_score or 0.0}%\n"
            f"Skills: {resume_ver.skills}\n"
            f"Achievements details:\n{exp_str}"
        )
        
    return {
        "job_title": pkg.job.title if pkg.job else "Target Role",
        "company": pkg.job.company if pkg.job else "Target Company",
        "resume": resume_content,
        "cover_letter": pkg.cover_letter or ""
    }

def save_submission_record(db: Session, package_id: int) -> None:
    """
    Saves a record of the application package submission, updating the package status
    to Submitted and adding it to the tracked JobApplication funnel.
    """
    pkg = db.query(ApplicationPackage).filter(ApplicationPackage.id == package_id).first()
    if not pkg:
        return
        
    # 1. Update status
    pkg.status = "Submitted"
    pkg.updated_at = datetime.utcnow()
    
    # 2. Add to active application tracker funnel
    existing_app = db.query(JobApplication).filter(
        JobApplication.company == pkg.job.company,
        JobApplication.position == pkg.job.title
    ).first()
    
    if not existing_app:
        job_form = JobCreate(
            company=pkg.job.company,
            position=pkg.job.title,
            status="Applied",
            applied_date=date.today(),
            notes=f"Auto-logged via Execution Service package #{pkg.id}."
        )
        create_job(db, job_form)
        
    # 3. Log recruitment outcome mapping
    existing_outcome = db.query(ApplicationOutcome).filter(
        ApplicationOutcome.job_posting_id == pkg.job_posting_id
    ).first()
    
    if not existing_outcome:
        outcome = ApplicationOutcome(
            job_posting_id=pkg.job_posting_id,
            opportunity_score=pkg.match_score,
            result="Applied",
            notes=f"Submission created on {date.today().isoformat()}."
        )
        db.add(outcome)
    else:
        existing_outcome.result = "Applied"
        
    db.commit()
