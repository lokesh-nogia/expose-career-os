from typing import List
from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting, JobSkill
from app.models.contracts import RoadmapResult, RoadmapPhase

def generate_roadmap(
    db: Session, 
    profile: UserProfile, 
    missing_skills: List[str]
) -> RoadmapResult:
    """
    Generates a progressive learning roadmap dynamically from missing skills.
    Maps top skill gaps to structured study phases.
    """
    phases = []
    
    # Calculate demand percentage dynamically for each missing skill to customize explanations
    total_jobs = db.query(JobPosting).count()
    skill_percentages = {}
    
    if total_jobs > 0:
        for skill in missing_skills:
            count = db.query(JobSkill).filter(JobSkill.skill_name.ilike(skill)).count()
            skill_percentages[skill] = int((count / total_jobs) * 100)
    else:
        # Default fallback
        for skill in missing_skills:
            skill_percentages[skill] = 50

    # Sort missing skills by frequency/importance
    sorted_missing = sorted(missing_skills, key=lambda s: skill_percentages.get(s, 0), reverse=True)

    # 1. Generate skill-focused roadmap phases dynamically
    for idx, skill in enumerate(sorted_missing[:3]):
        phase_num = idx + 1
        pct = skill_percentages.get(skill, 50)
        
        # Determine confidence level & impact dynamically
        if pct > 60:
            confidence = "High"
            impact = "+2 to +4 LPA"
        elif pct > 30:
            confidence = "Medium"
            impact = "+1.5 to +3 LPA"
        else:
            confidence = "Low"
            impact = "+1 to +2 LPA"
            
        phase = RoadmapPhase(
            title=f"Phase {phase_num}: Master {skill}",
            objective=f"Learn core capabilities, syntax, and deployment standards of {skill}.",
            estimated_duration="3 Weeks",
            required_skills=[skill],
            reason=f"Found in {pct}% of active target SDE job listings.",
            confidence_level=confidence,
            impact_range=impact
        )
        phases.append(phase)

    # 2. Add System Design Capstone Phase if skills were empty or to complete 4 phases
    if len(phases) < 4:
        phase_num = len(phases) + 1
        phases.append(
            RoadmapPhase(
                title=f"Phase {phase_num}: System Design & Scale Capstone",
                objective="Build and design low-latency, scalable backend architectures.",
                estimated_duration="4 Weeks",
                required_skills=["System Design", "Microservices"],
                reason="System design interviews represent the primary gatekeeper for senior SDE roles.",
                confidence_level="High",
                impact_range="+3 to +5 LPA"
            )
        )
        
    return RoadmapResult(phases=phases)
