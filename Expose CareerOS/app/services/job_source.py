import csv
import os
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Dict, Any

class JobSource(ABC):
    @abstractmethod
    def discover_jobs(self) -> List[Dict[str, Any]]:
        """Scans the source for raw job posting payloads."""
        pass

    @abstractmethod
    def fetch_job_details(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches full detail of a discovered job payload."""
        pass

    @abstractmethod
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Translates raw job payload to unified schema format."""
        pass

class CSVSource(JobSource):
    def __init__(self, filepath: str = "jobs_import.csv"):
        self.filepath = filepath

    def discover_jobs(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            return []
        
        jobs = []
        with open(self.filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(row)
        return jobs

    def fetch_job_details(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        return raw_job

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        title = raw_job.get("title", "").strip()
        company = raw_job.get("company", "").strip()
        location = raw_job.get("location", "").strip()
        source = raw_job.get("source", "").strip() or "CSV Import"
        
        try:
            salary = float(raw_job.get("salary", 0.0))
        except ValueError:
            salary = 0.0
            
        description = raw_job.get("description", "").strip()
        
        try:
            posted_date = date.fromisoformat(raw_job.get("posted_date", "").strip())
        except ValueError:
            posted_date = date.today()
            
        skills_str = raw_job.get("skills", "").strip()
        skills = [s.strip() for s in skills_str.split(",") if s.strip()] if skills_str else []
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "source": source,
            "salary": salary,
            "description": description,
            "posted_date": posted_date,
            "skills": skills
        }

class ManualImportSource(JobSource):
    def discover_jobs(self) -> List[Dict[str, Any]]:
        # Manual imports do not discover batches
        return []

    def fetch_job_details(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        return raw_job

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        # Expects standard dictionary structure matching schema
        title = raw_job.get("title", "").strip()
        company = raw_job.get("company", "").strip()
        location = raw_job.get("location", "").strip()
        source = raw_job.get("source", "").strip() or "Manual Import"
        
        try:
            salary = float(raw_job.get("salary", 0.0))
        except ValueError:
            salary = 0.0
            
        description = raw_job.get("description", "").strip()
        
        posted_date = raw_job.get("posted_date")
        if isinstance(posted_date, str):
            try:
                posted_date = date.fromisoformat(posted_date)
            except ValueError:
                posted_date = date.today()
        elif not isinstance(posted_date, date):
            posted_date = date.today()
            
        skills = raw_job.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
            
        return {
            "title": title,
            "company": company,
            "location": location,
            "source": source,
            "salary": salary,
            "description": description,
            "posted_date": posted_date,
            "skills": skills
        }

# ==========================================
# Future Integrations Placeholders
# ==========================================

class PortalSource(JobSource):
    def discover_jobs(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Real-time Job Portal scraping is not implemented.")

    def fetch_job_details(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Real-time Job Portal API is not implemented.")

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Real-time Job Portal normalization is not implemented.")

class CareerPageSource(JobSource):
    def discover_jobs(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Company Career Page scraping is not implemented.")

    def fetch_job_details(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Company Career Page scraping is not implemented.")

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Company Career Page normalization is not implemented.")

class APIJobSource(JobSource):
    def discover_jobs(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("External API Job sourcing is not implemented.")

    def fetch_job_details(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("External API Job Sourcing is not implemented.")

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("External API Job normalization is not implemented.")
