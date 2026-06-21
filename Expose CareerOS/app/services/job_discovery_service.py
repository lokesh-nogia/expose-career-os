from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional

from app.models.domain import (
    JobPosting, JobSkill, ImportRun, DiscoveryRun, 
    MarketSnapshot, MarketSkillSnapshot
)
from app.services.job_source import (
    CSVSource, ManualImportSource, PortalSource, 
    CareerPageSource, APIJobSource
)

def run_job_discovery(db: Session, source_type: str = "CSV") -> Dict[str, Any]:
    """
    Coordinates the job discovery run for a specific source:
    - Logs a DiscoveryRun audit record
    - Scrapes/reads raw jobs, normalizes, deduplicates, and saves
    - Creates historical MarketSnapshot of skill demands
    - Logs an ImportRun record
    """
    start_time = datetime.utcnow()
    records_found = 0
    records_imported = 0
    error_message = None
    status = "Success"
    
    # 1. Initialize the appropriate JobSource
    source_type_upper = source_type.upper()
    if source_type_upper == "CSV":
        source_inst = CSVSource()
        source_name = "CSV Ingestion Pipeline"
    elif source_type_upper == "MANUAL":
        source_inst = ManualImportSource()
        source_name = "Manual Ingestion"
    elif source_type_upper == "PORTAL":
        source_inst = PortalSource()
        source_name = "Job Portal Scraper"
    elif source_type_upper == "CAREER":
        source_inst = CareerPageSource()
        source_name = "Company Career Scraper"
    elif source_type_upper == "API":
        source_inst = APIJobSource()
        source_name = "API Sourcing Pipeline"
    else:
        raise ValueError(f"Unknown source type: {source_type}")

    # Initialize DiscoveryRun audit
    disc_run = DiscoveryRun(
        source=source_name,
        started_at=start_time,
        status="Running",
        records_found=0,
        records_imported=0
    )
    db.add(disc_run)
    db.commit()
    db.refresh(disc_run)

    # 2. Discover and Normalize Jobs
    try:
        raw_jobs = source_inst.discover_jobs()
        records_found = len(raw_jobs)
        
        for raw_job in raw_jobs:
            normalized = source_inst.normalize_job(raw_job)
            
            # Check for existing duplicate to avoid double-ingesting
            existing = db.query(JobPosting).filter(
                JobPosting.title == normalized["title"],
                JobPosting.company == normalized["company"],
                JobPosting.posted_date == normalized["posted_date"]
            ).first()
            
            if existing:
                continue
                
            # Add JobPosting record
            posting = JobPosting(
                title=normalized["title"],
                company=normalized["company"],
                location=normalized["location"],
                source=normalized["source"],
                salary=normalized["salary"],
                description=normalized["description"],
                posted_date=normalized["posted_date"],
                review_status="pending"  # Enters the review queue
            )
            db.add(posting)
            db.flush()  # Generate posting.id
            
            # Insert skills
            for skill_name in normalized["skills"]:
                job_skill = JobSkill(
                    job_posting_id=posting.id,
                    skill_name=skill_name
                )
                db.add(job_skill)
                
            records_imported += 1
            
        db.commit()
        
        # 3. Create Market Snapshot if new records were added
        if records_imported > 0:
            create_market_snapshot(db)
            
        # Log successful ImportRun
        import_run = ImportRun(
            filename=source_name if source_type_upper != "CSV" else "jobs_import.csv",
            imported_records=records_imported,
            failed_records=0,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            status="Success"
        )
        db.add(import_run)
        db.commit()

    except NotImplementedError as nie:
        db.rollback()
        status = "Failed"
        error_message = str(nie)
        import_run = ImportRun(
            filename=source_name,
            imported_records=0,
            failed_records=0,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            status="Failed",
            error_message=str(nie)
        )
        db.add(import_run)
        db.commit()
    except Exception as ex:
        db.rollback()
        status = "Failed"
        error_message = str(ex)
        import_run = ImportRun(
            filename=source_name,
            imported_records=0,
            failed_records=1,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            status="Failed",
            error_message=str(ex)
        )
        db.add(import_run)
        db.commit()

    # 4. Finalize DiscoveryRun audit
    disc_run.completed_at = datetime.utcnow()
    disc_run.status = status
    disc_run.records_found = records_found
    disc_run.records_imported = records_imported
    disc_run.error_message = error_message
    db.commit()
    db.refresh(disc_run)

    return {
        "discovery_run_id": disc_run.id,
        "source": source_name,
        "status": status,
        "records_found": records_found,
        "records_imported": records_imported,
        "error_message": error_message
    }

def create_market_snapshot(db: Session) -> None:
    """Computes skill demand frequency and saves a historical snapshot."""
    total_jobs = db.query(JobPosting).count()
    if total_jobs == 0:
        return

    # Count skill occurrences
    skill_counts = db.query(
        JobSkill.skill_name, 
        func.count(JobSkill.id)
    ).group_by(JobSkill.skill_name).all()

    # Save Snapshot
    snapshot = MarketSnapshot(created_at=datetime.utcnow())
    db.add(snapshot)
    db.flush()

    for skill_name, count in skill_counts:
        demand_score = (count / total_jobs) * 100.0
        item = MarketSkillSnapshot(
            snapshot_id=snapshot.id,
            skill_name=skill_name,
            frequency=count,
            demand_score=round(demand_score, 1)
        )
        db.add(item)
    db.commit()
