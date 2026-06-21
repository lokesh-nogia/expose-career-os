from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.domain import JobApplication, JobCreate, JobUpdate

def list_jobs(db: Session, search: Optional[str] = None, status: Optional[str] = None) -> List[JobApplication]:
    """Lists all job applications, optionally filtering by search term and status."""
    query = db.query(JobApplication)
    
    if status and status.strip():
        query = query.filter(JobApplication.status == status)
        
    if search and search.strip():
        search_term = f"%{search}%"
        query = query.filter(
            (JobApplication.company.ilike(search_term)) | 
            (JobApplication.position.ilike(search_term)) |
            (JobApplication.notes.ilike(search_term))
        )
        
    # Order by applied date descending, then id descending
    return query.order_by(JobApplication.applied_date.desc(), JobApplication.id.desc()).all()

def get_job(db: Session, job_id: int) -> Optional[JobApplication]:
    """Retrieves a single job application by ID."""
    return db.query(JobApplication).filter(JobApplication.id == job_id).first()

def create_job(db: Session, data: JobCreate) -> JobApplication:
    """Creates a new job application."""
    job = JobApplication(
        company=data.company,
        position=data.position,
        status=data.status,
        applied_date=data.applied_date,
        notes=data.notes
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def update_job(db: Session, job_id: int, data: JobUpdate) -> Optional[JobApplication]:
    """Updates an existing job application."""
    job = get_job(db, job_id)
    if not job:
        return None
    job.company = data.company
    job.position = data.position
    job.status = data.status
    job.applied_date = data.applied_date
    job.notes = data.notes
    db.commit()
    db.refresh(job)
    return job

def delete_job(db: Session, job_id: int) -> bool:
    """Deletes a job application by ID. Returns True if deleted, False otherwise."""
    job = get_job(db, job_id)
    if not job:
        return False
    db.delete(job)
    db.commit()
    return True

def get_job_stats(db: Session) -> dict:
    """Returns statistics about job applications."""
    total = db.query(JobApplication).count()
    applied = db.query(JobApplication).filter(JobApplication.status == "Applied").count()
    interviews = db.query(JobApplication).filter(JobApplication.status == "Interview").count()
    offers = db.query(JobApplication).filter(JobApplication.status == "Offer").count()
    return {
        "total": total,
        "applied": applied,
        "interviews": interviews,
        "offers": offers
    }
