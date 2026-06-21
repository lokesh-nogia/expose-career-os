from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.database.connection import Base

# ==========================================
# 1. User Profile & Skills Models
# ==========================================

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False, default="")
    current_role = Column(String, nullable=False, default="")
    experience_years = Column(Integer, nullable=False, default=0)
    current_salary = Column(Float, nullable=False, default=0.0)  # Absolute number or LPA
    target_role = Column(String, nullable=False, default="")
    target_salary = Column(Float, nullable=False, default=0.0)
    target_timeline = Column(String, nullable=False, default="6 Months")
    is_onboarded = Column(Boolean, nullable=False, default=False)

    skills = relationship("UserSkill", back_populates="profile", cascade="all, delete-orphan")

class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    level = Column(String, nullable=False)  # Beginner, Intermediate, Advanced

    profile = relationship("UserProfile", back_populates="skills")
    evidence = relationship("UserSkillEvidence", back_populates="skill", cascade="all, delete-orphan")

class UserSkillEvidence(Base):
    __tablename__ = "user_skill_evidences"

    id = Column(Integer, primary_key=True, index=True)
    user_skill_id = Column(Integer, ForeignKey("user_skills.id"), nullable=False)
    evidence_type = Column(String, nullable=False)  # Project, Interview, Certification, Work Experience
    title = Column(String, nullable=False)
    notes = Column(Text, nullable=True, default="")

    skill = relationship("UserSkill", back_populates="evidence")

# ==========================================
# 2. Market Job Postings & Demands
# ==========================================

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    source = Column(String, nullable=False)  # e.g., "CSV Import"
    salary = Column(Float, nullable=True, default=0.0)
    description = Column(Text, nullable=True, default="")
    posted_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    review_status = Column(String, nullable=False, default="pending")  # pending, approved, rejected, saved

    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")

class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    skill_name = Column(String, nullable=False)

    job = relationship("JobPosting", back_populates="skills")

# ==========================================
# 3. User's Manual Job Application Funnel & Practice Questions
# ==========================================

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    position = Column(String, nullable=False)
    status = Column(String, nullable=False)  # Wishlist, Applied, Interview, Offer, Rejected
    applied_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True, default="")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # Easy, Medium, Hard
    personal_answer = Column(Text, nullable=True, default="")
    score = Column(Integer, nullable=True, default=0)  # 0 to 10 scale
    feedback = Column(Text, nullable=True, default="")

# ==========================================
# 4. Ingestion Auditing & Historical Snapshots
# ==========================================

class ImportRun(Base):
    __tablename__ = "import_runs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    imported_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False)  # Success, Failed, Partial
    error_message = Column(Text, nullable=True, default="")

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("MarketSkillSnapshot", back_populates="snapshot", cascade="all, delete-orphan")

class MarketSkillSnapshot(Base):
    __tablename__ = "market_skill_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("market_snapshots.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    frequency = Column(Integer, nullable=False, default=0)
    demand_score = Column(Float, nullable=False, default=0.0)  # Percentage score

    snapshot = relationship("MarketSnapshot", back_populates="skills")

# ==========================================
# 5. Company Insights
# ==========================================

class CompanyInsight(Base):
    __tablename__ = "company_insights"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True, nullable=False)
    industry = Column(String, nullable=True, default="")
    rating = Column(Float, nullable=True, default=0.0)
    interview_difficulty = Column(String, nullable=True, default="Medium")  # Easy, Medium, Hard
    hiring_status = Column(String, nullable=True, default="Hiring")  # Hiring, Slow, Freeze
    notes = Column(Text, nullable=True, default="")

# ==========================================
# 5.5. Career OS Refactor Core Tables
# ==========================================

class DiscoveryRun(Base):
    __tablename__ = "discovery_runs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # Success, Failed, Running
    records_found = Column(Integer, nullable=False, default=0)
    records_imported = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False, default="")
    skills = Column(Text, nullable=False, default="")  # Comma-separated list of skills
    experience = Column(Text, nullable=False, default="[]")  # JSON serialized achievements/experience items
    match_score = Column(Float, nullable=True)
    target_job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ResumeDiff(Base):
    __tablename__ = "resume_diffs"

    id = Column(Integer, primary_key=True, index=True)
    resume_version_id = Column(Integer, ForeignKey("resume_versions.id"), nullable=False)
    parent_version_id = Column(Integer, ForeignKey("resume_versions.id"), nullable=True)
    diff_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ApplicationOutcome(Base):
    __tablename__ = "application_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    opportunity_score = Column(Float, nullable=False, default=0.0)
    result = Column(String, nullable=False)  # Applied, Rejected, Interview, Offer, Withdrawn
    notes = Column(Text, nullable=True)

class CompanyQuestionPattern(Base):
    __tablename__ = "company_question_patterns"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    category = Column(String, nullable=False)
    frequency = Column(Integer, nullable=False, default=1)
    difficulty = Column(String, nullable=False)  # Easy, Medium, Hard

class QuestionBank(Base):
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # Beginner, Intermediate, Advanced, Senior, Staff
    tags = Column(String, nullable=True)  # Comma-separated tags

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # job_imported, roadmap_updated, quiz_due, etc.
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, nullable=False, default=False)

class AgentState(Base):
    __tablename__ = "agent_states"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    current_goal = Column(String, nullable=False, default="")
    current_roadmap = Column(Text, nullable=False, default="[]")
    current_readiness = Column(Float, nullable=False, default=0.0)
    current_salary_estimate = Column(Float, nullable=False, default=0.0)
    current_recommendations = Column(Text, nullable=False, default="[]")
    last_observation = Column(Text, nullable=False, default="{}")
    last_plan = Column(Text, nullable=False, default="{}")
    last_outcome = Column(Text, nullable=False, default="{}")

    profile = relationship("UserProfile")

class RecommendationHistory(Base):
    __tablename__ = "recommendation_histories"

    id = Column(Integer, primary_key=True, index=True)
    recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted = Column(Boolean, nullable=False, default=False)
    rejected = Column(Boolean, nullable=False, default=False)
    outcome = Column(String, nullable=False, default="Pending")
    result = Column(String, nullable=True, default="Pending")
    readiness_gain = Column(Float, nullable=True, default=0.0)
    salary_gain = Column(Float, nullable=True, default=0.0)
    interview_gain = Column(Float, nullable=True, default=0.0)

class ApplicationPackage(Base):
    __tablename__ = "application_packages"

    id = Column(Integer, primary_key=True, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    match_score = Column(Float, nullable=False, default=0.0)
    resume_version_id = Column(Integer, ForeignKey("resume_versions.id"), nullable=True)
    cover_letter = Column(Text, nullable=True, default="")
    missing_skills = Column(Text, nullable=True, default="[]")
    salary_analysis = Column(Text, nullable=True, default="{}")
    status = Column(String, nullable=False, default="Draft")  # Draft, Approved, Submitted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("JobPosting")
    resume_version = relationship("ResumeVersion")

# ==========================================
# 6. Pydantic Schemas for Input Validation
# ==========================================

class ProfileOnboard(BaseModel):
    full_name: str = Field(..., min_length=1)
    current_role: str = Field(..., min_length=1)
    experience_years: int = Field(..., ge=0)
    current_salary: float = Field(..., ge=0.0)
    target_role: str = Field(..., min_length=1)
    target_salary: float = Field(..., ge=0.0)
    target_timeline: str = Field(..., min_length=1)

class UserProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=1)
    current_role: str = Field(..., min_length=1)
    experience_years: int = Field(..., ge=0)
    current_salary: float = Field(..., ge=0.0)
    target_role: str = Field(..., min_length=1)
    target_salary: float = Field(..., ge=0.0)
    target_timeline: str = Field(..., min_length=1)
    skills: str = Field(..., description="Comma-separated skills list")

class SkillCreate(BaseModel):
    skill_name: str = Field(..., min_length=1)
    level: str = Field("Beginner", pattern="^(Beginner|Intermediate|Advanced)$")

class EvidenceCreate(BaseModel):
    evidence_type: str = Field(..., pattern="^(Project|Interview|Certification|Work Experience)$")
    title: str = Field(..., min_length=1)
    notes: Optional[str] = ""

class InterviewCreate(BaseModel):
    company: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    difficulty: str = Field(..., pattern="^(Easy|Medium|Hard)$")
    personal_answer: Optional[str] = ""
    score: Optional[int] = Field(0, ge=0, le=10)
    feedback: Optional[str] = ""

class InterviewUpdate(BaseModel):
    company: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    difficulty: str = Field(..., pattern="^(Easy|Medium|Hard)$")
    personal_answer: Optional[str] = ""
    score: Optional[int] = Field(0, ge=0, le=10)
    feedback: Optional[str] = ""

class JobCreate(BaseModel):
    company: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    status: str = Field(..., pattern="^(Wishlist|Applied|Interview|Offer|Rejected)$")
    applied_date: date
    notes: Optional[str] = ""

class JobUpdate(BaseModel):
    company: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    status: str = Field(..., pattern="^(Wishlist|Applied|Interview|Offer|Rejected)$")
    applied_date: date
    notes: Optional[str] = ""
