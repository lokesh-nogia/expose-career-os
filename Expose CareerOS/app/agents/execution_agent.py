from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting
from app.services import resume_intelligence, cover_letter_agent

class PreparedAction:
    def __init__(self, action_type: str, title: str, details: str, status: str = "Ready For Review"):
        self.action_type = action_type
        self.title = title
        self.details = details
        self.status = status

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "title": self.title,
            "details": self.details,
            "status": self.status
        }

def prepare_resume_variant_action(db: Session, profile: UserProfile, job: JobPosting) -> PreparedAction:
    """Creates a custom resume variant mapped to the target job and wraps it in a reviewable action."""
    version = resume_intelligence.create_resume_variant(db, profile, job, f"Resume for {job.company} - {job.title}")
    details = f"Optimized resume version {version.version_number} with Match Score: {version.match_score}%. Reordered skills: {version.skills}."
    return PreparedAction(
        action_type="Prepare Resume Variant",
        title=f"Resume Variant: {job.title} at {job.company}",
        details=details
    )

def prepare_cover_letter_action(db: Session, profile: UserProfile, job: JobPosting) -> PreparedAction:
    """Generates a customized cover letter for the target job and wraps it in a reviewable action."""
    letter_text = cover_letter_agent.generate_cover_letter(db, profile, job)
    return PreparedAction(
        action_type="Prepare Cover Letter",
        title=f"Cover Letter: {job.title} at {job.company}",
        details=letter_text
    )

def prepare_application_package_action(db: Session, profile: UserProfile, job: JobPosting) -> PreparedAction:
    """Assembles a combined Resume and Cover Letter package for the target job and wraps it in a reviewable action."""
    version = resume_intelligence.create_resume_variant(db, profile, job, f"Resume for {job.company} - {job.title}")
    letter_text = cover_letter_agent.generate_cover_letter(db, profile, job)
    details = f"Resume Match Score: {version.match_score}%\n\nCover Letter Draft:\n{letter_text}"
    return PreparedAction(
        action_type="Prepare Application Package",
        title=f"Application Package: {job.title} at {job.company}",
        details=details
    )

def prepare_learning_plan_action(db: Session, profile: UserProfile, skill_name: str) -> PreparedAction:
    """Constructs a progressive learning plan for a missing skill and wraps it in a reviewable action."""
    details = (
        f"3-Week Study Plan to Master {skill_name}:\n"
        f"- Week 1: Basic concepts, CLI instructions, and foundational architectures.\n"
        f"- Week 2: Build active projects and integrated tests showcasing skill competency.\n"
        f"- Week 3: Deploy scalable, microservice architectures using {skill_name} and add evidence log."
    )
    return PreparedAction(
        action_type="Prepare Learning Plan",
        title=f"Learning Plan: Master {skill_name}",
        details=details
    )
