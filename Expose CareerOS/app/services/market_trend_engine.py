from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import JobPosting, JobSkill, MarketSnapshot, MarketSkillSnapshot

def analyze_market_trends(db: Session) -> Dict[str, Any]:
    """
    Analyzes job postings to extract demanded, trending, and emerging skills.
    """
    total_jobs = db.query(JobPosting).count()
    if total_jobs == 0:
        return {
            "demanded": [],
            "emerging": [],
            "trending": []
        }

    # Query all skills and their counts
    skills_query = db.query(
        JobSkill.skill_name,
        func.count(JobSkill.id)
    ).group_by(JobSkill.skill_name).order_by(
        func.count(JobSkill.id).desc()
    ).all()

    demanded_list = []
    for skill_name, count in skills_query:
        score = (count / total_jobs) * 100.0
        demanded_list.append({
            "skill_name": skill_name,
            "frequency": count,
            "demand_score": round(score, 1)
        })

    # Emerging Skills: Demanded skills with moderate counts but high salary premium (e.g. OpenSearch, Kafka, System Design)
    # Let's flag them if they occur in top 20% of high paying jobs
    high_pay_threshold = db.query(func.avg(JobPosting.salary)).scalar() or 0.0
    
    emerging_query = db.query(
        JobSkill.skill_name,
        func.count(JobSkill.id)
    ).join(JobPosting).filter(
        JobPosting.salary >= high_pay_threshold
    ).group_by(JobSkill.skill_name).order_by(
        func.count(JobSkill.id).desc()
    ).all()
    
    # Filter for skills that are mostly represented in high paying jobs
    emerging_skills = []
    for skill_name, count in emerging_query[:4]:
        # If it is not the top absolute dominant (like general Java), it's emerging
        if skill_name.lower() not in ["java", "spring boot", "rest apis"]:
            emerging_skills.append(skill_name)

    # Trending Skills: Skills that have the highest frequency growth in recent listings
    # Since it is a snapshot, let's select skills from the last 5 posted jobs
    recent_jobs = db.query(JobPosting).order_by(JobPosting.posted_date.desc()).limit(5).all()
    recent_job_ids = [j.id for j in recent_jobs]
    
    trending_query = db.query(
        JobSkill.skill_name,
        func.count(JobSkill.id)
    ).filter(
        JobSkill.job_posting_id.in_(recent_job_ids)
    ).group_by(JobSkill.skill_name).order_by(
        func.count(JobSkill.id).desc()
    ).limit(3).all()
    
    trending_skills = [s[0] for s in trending_query]

    return {
        "demanded": demanded_list,
        "emerging": emerging_skills,
        "trending": trending_skills
    }

def record_historical_snapshot(db: Session) -> MarketSnapshot:
    """
    Aggregates current metrics and saves them to the snapshot tables
    to enable historical trend comparisons in the future.
    """
    total_jobs = db.query(JobPosting).count()
    if total_jobs == 0:
        # Save empty snapshot
        snap = MarketSnapshot(created_at=datetime.utcnow())
        db.add(snap)
        db.commit()
        return snap

    skills_query = db.query(
        JobSkill.skill_name,
        func.count(JobSkill.id)
    ).group_by(JobSkill.skill_name).all()

    snap = MarketSnapshot(created_at=datetime.utcnow())
    db.add(snap)
    db.flush()

    for skill_name, count in skills_query:
        score = (count / total_jobs) * 100.0
        item = MarketSkillSnapshot(
            snapshot_id=snap.id,
            skill_name=skill_name,
            frequency=count,
            demand_score=round(score, 1)
        )
        db.add(item)
        
    db.commit()
    db.refresh(snap)
    return snap
