from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import InterviewQuestion

class LearningAdjustment:
    def __init__(self, category: str, message: str, average_score: float):
        self.category = category
        self.message = message
        self.average_score = average_score

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "message": self.message,
            "average_score": self.average_score
        }

def analyze_learning_progress(db: Session) -> list[LearningAdjustment]:
    """
    Analyzes category scores of solved practice questions in the InterviewQuestion table.
    Flags categories where the average score is below 7.0/10 as having low retention,
    and returns corresponding LearningAdjustments.
    """
    low_retention_categories = db.query(
        InterviewQuestion.category,
        func.avg(InterviewQuestion.score).label("avg_score")
    ).filter(InterviewQuestion.score > 0)\
     .group_by(InterviewQuestion.category)\
     .having(func.avg(InterviewQuestion.score) < 7.0).all()

    adjustments = []
    for category, avg_score in low_retention_categories:
        avg_score_rounded = round(float(avg_score), 1)
        adjustments.append(
            LearningAdjustment(
                category=category,
                message=f"{category} retention low (Avg Score: {avg_score_rounded}/10). Recommend immediate revision and mock practice.",
                average_score=avg_score_rounded
            )
        )

    # If no category falls below 7.0 but we have some solved questions,
    # check if there are unsolved questions (score == 0) and recommend solving them.
    if not adjustments:
        unsolved_count = db.query(InterviewQuestion).filter(InterviewQuestion.score == 0).count()
        if unsolved_count > 0:
            adjustments.append(
                LearningAdjustment(
                    category="General Practice",
                    message=f"You have {unsolved_count} unsolved practice questions. Recommend completing them to baseline readiness.",
                    average_score=0.0
                )
            )

    return adjustments
