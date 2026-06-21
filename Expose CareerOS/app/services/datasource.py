import csv
import os
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.domain import (
    JobPosting, JobSkill, InterviewQuestion, ImportRun, 
    MarketSnapshot, MarketSkillSnapshot, UserProfile
)

# --------------------------------------------------
# 1. DataSource Abstract Base Class
# --------------------------------------------------
class DataSource(ABC):
    @abstractmethod
    def fetch_jobs(self, db: Session) -> List[JobPosting]:
        """Fetches job postings from the data source."""
        pass

    @abstractmethod
    def fetch_learning_content(self, db: Session, profile: UserProfile) -> List[dict]:
        """Fetches learning recommendations/topics from the data source."""
        pass

    @abstractmethod
    def fetch_interview_questions(self, db: Session) -> List[InterviewQuestion]:
        """Fetches interview questions from the database library."""
        pass

# --------------------------------------------------
# 2. ManualDataSource Implementation
# --------------------------------------------------
class ManualDataSource(DataSource):
    def fetch_jobs(self, db: Session) -> List[JobPosting]:
        """Returns job postings stored in the database."""
        return db.query(JobPosting).order_by(JobPosting.posted_date.desc()).all()

    def fetch_learning_content(self, db: Session, profile: UserProfile) -> List[dict]:
        """Resolves dynamic recommendations from the roadmap engine (single source of truth)."""
        # Kept abstract to avoid circular imports. Roadmap engine will query skills directly.
        return []

    def fetch_interview_questions(self, db: Session) -> List[InterviewQuestion]:
        """Returns interview questions stored in the database."""
        return db.query(InterviewQuestion).order_by(InterviewQuestion.id.desc()).all()

# --------------------------------------------------
# 3. CSVDataSource Implementation
# --------------------------------------------------
class CSVDataSource(DataSource):
    def __init__(self, filepath: str = "jobs_import.csv"):
        self.filepath = filepath

    def fetch_jobs(self, db: Session) -> List[JobPosting]:
        """Returns currently ingested jobs from database."""
        return db.query(JobPosting).order_by(JobPosting.posted_date.desc()).all()

    def fetch_learning_content(self, db: Session, profile: UserProfile) -> List[dict]:
        return []

    def fetch_interview_questions(self, db: Session) -> List[InterviewQuestion]:
        return db.query(InterviewQuestion).order_by(InterviewQuestion.id.desc()).all()

    def run_import(self, db: Session) -> ImportRun:
        """
        Parses jobs_import.csv, normalizes skills, logs results to ImportRun,
        and saves a historical MarketSnapshot of skill demands.
        """
        start_time = datetime.utcnow()
        imported = 0
        failed = 0
        err_msg = ""
        
        if not os.path.exists(self.filepath):
            # Create a failed import run audit record
            run = ImportRun(
                filename=self.filepath,
                imported_records=0,
                failed_records=0,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                status="Failed",
                error_message=f"File {self.filepath} not found."
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run

        try:
            with open(self.filepath, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        title = row.get("title", "").strip()
                        company = row.get("company", "").strip()
                        location = row.get("location", "").strip()
                        source = row.get("source", "").strip()
                        
                        try:
                            salary = float(row.get("salary", 0.0))
                        except ValueError:
                            salary = 0.0
                            
                        description = row.get("description", "").strip()
                        
                        try:
                            posted_date = date.fromisoformat(row.get("posted_date", "").strip())
                        except ValueError:
                            posted_date = date.today()
                            
                        skills_str = row.get("skills", "").strip()

                        if not title or not company:
                            failed += 1
                            continue

                        # Check for existing duplicate to avoid double-ingesting
                        existing = db.query(JobPosting).filter(
                            JobPosting.title == title,
                            JobPosting.company == company,
                            JobPosting.posted_date == posted_date
                        ).first()

                        if existing:
                            continue

                        # Add JobPosting record
                        posting = JobPosting(
                            title=title,
                            company=company,
                            location=location,
                            source=source,
                            salary=salary,
                            description=description,
                            posted_date=posted_date
                        )
                        db.add(posting)
                        db.flush()  # Flushes to retrieve posting.id

                        # Normalize JobSkills into separate relation records
                        if skills_str:
                            for sk in skills_str.split(","):
                                sk_name = sk.strip()
                                if sk_name:
                                    job_sk = JobSkill(
                                        job_posting_id=posting.id,
                                        skill_name=sk_name
                                    )
                                    db.add(job_sk)
                                    
                        imported += 1
                    except Exception as row_ex:
                        failed += 1
                        err_msg += f"Error parsing row: {row_ex}. "
                        
            status = "Success" if failed == 0 else ("Partial" if imported > 0 else "Failed")
            db.commit()
            
            # 4. Trigger Market Snapshotting
            if imported > 0:
                self._create_market_snapshot(db)
                
            # Log successful/partial run audit
            run = ImportRun(
                filename=self.filepath,
                imported_records=imported,
                failed_records=failed,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                status=status,
                error_message=err_msg if err_msg else None
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run

        except Exception as file_ex:
            db.rollback()
            run = ImportRun(
                filename=self.filepath,
                imported_records=0,
                failed_records=0,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                status="Failed",
                error_message=str(file_ex)
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run

    def _create_market_snapshot(self, db: Session) -> None:
        """Computes skill demand frequency and saves a historical snapshot."""
        # Query total jobs
        total_jobs = db.query(JobPosting).count()
        if total_jobs == 0:
            return

        # Query all skill counts
        from sqlalchemy import func
        skill_counts = db.query(
            JobSkill.skill_name, 
            func.count(JobSkill.id)
        ).group_by(JobSkill.skill_name).all()

        # Create Snapshot header
        snapshot = MarketSnapshot(created_at=datetime.utcnow())
        db.add(snapshot)
        db.flush()

        # Store skill snapshots
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

# Dependency provider
def get_datasource(request: Optional[dict] = None) -> DataSource:
    """FastAPI Dependency to select active DataSource."""
    # Under Phase 2.5, we default to CSVDataSource to pull real market jobs
    return CSVDataSource()
