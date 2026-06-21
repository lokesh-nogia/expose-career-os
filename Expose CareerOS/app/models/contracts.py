from typing import List
from pydantic import BaseModel, Field

# ==========================================
# 1. Career Roadmap Engine Contracts
# ==========================================

class RoadmapPhase(BaseModel):
    title: str = Field(..., description="Name of the roadmap phase")
    objective: str = Field(..., description="Core learning target")
    estimated_duration: str = Field(..., description="Target study timeline (e.g. 2 Weeks)")
    required_skills: List[str] = Field(..., description="Skills focused on in this phase")
    reason: str = Field(..., description="Why this step is critical")
    confidence_level: str = Field(..., description="Salary impact confidence: High, Medium, Low")
    impact_range: str = Field(..., description="Estimated LPA salary premium impact bracket")

class RoadmapResult(BaseModel):
    phases: List[RoadmapPhase] = Field(..., description="List of ordered phases")

# ==========================================
# 2. Salary Intelligence Engine Contracts
# ==========================================

class SalaryImpactDetail(BaseModel):
    skill_name: str
    confidence_level: str  # High, Medium, Low
    estimated_impact: str  # e.g., "+2 to +4 LPA"

class SalaryAnalysisResult(BaseModel):
    estimated_market_salary: float = Field(..., description="Determined dynamic salary baseline")
    salary_gap: float = Field(..., description="Delta target vs market estimates")
    missing_high_value_skills: List[str] = Field(..., description="Missing skills linked to top pay scales")
    salary_impact_breakdown: List[SalaryImpactDetail] = Field(..., description="Valuations per skill gap")

# ==========================================
# 3. Readiness Engine Contracts
# ==========================================

class ReadinessResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Readiness percentage matching role")
    target_role: str = Field(..., description="The role evaluated against")
    matched_skills: List[str] = Field(..., description="User skills that match core requirements")
    missing_skills: List[str] = Field(..., description="Skills demanded but missing")
    explanation: str = Field(..., description="Calculation description summary")

# ==========================================
# 4. Daily Mission Engine Contracts
# ==========================================

class DailyMissionTask(BaseModel):
    description: str = Field(..., description="Actionable task instruction")
    linked_to: str = Field(..., description="Target category trigger (e.g. Skill Gap, Target Role)")

class DailyMissionResult(BaseModel):
    tasks: List[DailyMissionTask] = Field(..., description="Today's actionable task logs")

# ==========================================
# 5. Opportunity Scoring Engine Contracts
# ==========================================

class OpportunityResult(BaseModel):
    job_posting_id: int
    title: str
    company: str
    score: float = Field(..., ge=0.0, le=100.0, description="Match score of job posting")
    reasons: List[str] = Field(..., description="Primary match score drivers list")

# ==========================================
# 6. Career Score Engine Contracts
# ==========================================

class CareerScoreResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Overall career progress score")
    breakdown: dict = Field(..., description="Scores per category weight")
    quick_wins: List[str] = Field(..., description="Specific target items to upgrade the score")
