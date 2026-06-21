from sqlalchemy.orm import Session
from app.models.domain import RecommendationHistory, JobPosting, JobSkill
from app.agents.planner_agent import WeeklyPlan

class CareerRecommendation:
    def __init__(self, priority: int, topic: str, reason: str, salary_impact: str, confidence: str):
        self.priority = priority
        self.topic = topic
        self.reason = reason
        self.salary_impact = salary_impact
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "priority": self.priority,
            "topic": self.topic,
            "reason": self.reason,
            "salary_impact": self.salary_impact,
            "confidence": self.confidence
        }

def generate_recommendations(db: Session, weekly_plan: WeeklyPlan) -> list[CareerRecommendation]:
    """
    Translates weekly plan topics into concrete recommendations.
    Filters out any recommendation topics that have been previously rejected
    in the RecommendationHistory table.
    """
    # 1. Fetch previously rejected recommendation texts/keywords
    rejected_records = db.query(RecommendationHistory).filter(RecommendationHistory.rejected == True).all()
    rejected_keywords = [r.recommendation.lower() for r in rejected_records]

    recommendations = []
    priority_counter = 1

    total_jobs = db.query(JobPosting).count()

    for topic in weekly_plan.topics:
        # Check memory to see if we rejected learning this topic previously
        is_rejected = False
        for kw in rejected_keywords:
            if topic.lower() in kw:
                is_rejected = True
                break

        if is_rejected:
            continue

        # Calculate demand percentage dynamically
        if total_jobs > 0:
            count = db.query(JobSkill).filter(JobSkill.skill_name.ilike(topic)).count()
            percentage = int((count / total_jobs) * 100)
        else:
            percentage = 45

        # Determine salary impact and confidence dynamically based on demand percentage
        if percentage > 60:
            salary_impact = "High"
            confidence = "High"
        elif percentage > 30:
            salary_impact = "Medium"
            confidence = "High"
        else:
            salary_impact = "Low"
            confidence = "Medium"

        reason = f"Present in {percentage}% of matching jobs"
        if percentage == 0:
            reason = "Emerging market capability matching target roles"

        rec = CareerRecommendation(
            priority=priority_counter,
            topic=topic,
            reason=reason,
            salary_impact=salary_impact,
            confidence=confidence
        )
        recommendations.append(rec)
        priority_counter += 1

    return recommendations
