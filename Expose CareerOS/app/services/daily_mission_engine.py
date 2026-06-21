from typing import List, Any
from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting, InterviewQuestion
from app.models.contracts import DailyMissionResult, DailyMissionTask, RoadmapResult

def generate_daily_mission(
    db: Session, 
    profile: UserProfile, 
    roadmap: RoadmapResult,
    opportunities: List[Any] = None
) -> DailyMissionResult:
    """
    Dynamically generates 3-4 daily task items tailored to 
    active skill gaps, roadmap objectives, and target job vacancies.
    """
    tasks = []
    
    # 1. Action item linked to the active Roadmap Phase
    if roadmap.phases:
        top_phase = roadmap.phases[0]
        # Find the main skill in this phase
        main_skill = top_phase.required_skills[0] if top_phase.required_skills else "Backend"
        tasks.append(
            DailyMissionTask(
                description=f"Study {main_skill} foundations: {top_phase.objective}",
                linked_to=f"Roadmap Gap ({top_phase.title})"
            )
        )

    # 2. Action item linked to Interview Practice
    # Check for unscored or low-scoring questions in the library
    question = db.query(InterviewQuestion).filter(
        (InterviewQuestion.score == 0) | (InterviewQuestion.score < 7)
    ).first()
    
    if question:
        tasks.append(
            DailyMissionTask(
                description=f"Draft or improve your answer for: '{question.question[:40]}...' ({question.company})",
                linked_to="Interview Readiness"
            )
        )
    else:
        tasks.append(
            DailyMissionTask(
                description="Review core backend concurrency notes or Java Hashmap implementation details.",
                linked_to="Interview Readiness"
            )
        )

    # 3. Action item linked to high matching Job Opportunities
    # Suggest applying to the top matching opportunity
    if opportunities:
        top_job = opportunities[0]
        tasks.append(
            DailyMissionTask(
                description=f"Apply to matching position: {top_job.title} at {top_job.company} (Match: {int(top_job.score)}%)",
                linked_to="Goal Alignment"
            )
        )
    else:
        tasks.append(
            DailyMissionTask(
                description="Import latest industry listings via CSV or search for active target role postings.",
                linked_to="Market Intake"
            )
        )

    # 4. Action item for building Skill Evidence
    # Find a user skill that doesn't have evidence yet
    skill_without_evidence = None
    for sk in profile.skills:
        if not sk.evidence:
            skill_without_evidence = sk
            break
            
    if skill_without_evidence:
        tasks.append(
            DailyMissionTask(
                description=f"Document a project or certificate as evidence for your '{skill_without_evidence.skill_name}' skill.",
                linked_to="Skill Depth"
            )
        )

    return DailyMissionResult(tasks=tasks)
