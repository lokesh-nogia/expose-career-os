from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from app.models.domain import CompanyQuestionPattern, QuestionBank, InterviewQuestion

ACADEMY_CATEGORIES = [
    "Java Core", "Collections", "Concurrency", "Spring Boot", 
    "Microservices", "Kafka", "Docker", "AWS", 
    "System Design", "Behavioral"
]

def get_academy_status(db: Session) -> List[Dict[str, Any]]:
    """
    Computes completion stats for each of the 10 subjects:
    - Total curated questions available in QuestionBank
    - Total solved/practiced questions in InterviewQuestion (matching category)
    - Average score (0 to 10 scale)
    - Calculated readiness percentage
    """
    stats = []
    for category in ACADEMY_CATEGORIES:
        # Total in bank
        bank_count = db.query(QuestionBank).filter(
            QuestionBank.category == category
        ).count()
        
        # User solved
        user_solved = db.query(InterviewQuestion).filter(
            InterviewQuestion.category.ilike(category)
        ).all()
        
        solved_count = len(user_solved)
        
        if solved_count > 0:
            avg_score = sum(q.score for q in user_solved) / solved_count
            # Readiness % is calculated as (solved_ratio * 50) + (avg_score_ratio * 50)
            solved_ratio = min(1.0, solved_count / max(1, bank_count))
            score_ratio = avg_score / 10.0
            readiness_pct = round((solved_ratio * 50.0) + (score_ratio * 50.0))
        else:
            avg_score = 0.0
            readiness_pct = 0

        stats.append({
            "category": category,
            "bank_count": bank_count,
            "solved_count": solved_count,
            "average_score": round(avg_score, 1),
            "readiness_pct": readiness_pct
        })
    return stats

def get_company_patterns(db: Session, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves frequency and difficulty trends of questions asked by specific companies."""
    query = db.query(CompanyQuestionPattern)
    if company_name:
        query = query.filter(CompanyQuestionPattern.company.ilike(company_name))
    
    patterns = query.order_by(CompanyQuestionPattern.frequency.desc()).all()
    
    return [
        {
            "company": p.company,
            "category": p.category,
            "frequency": p.frequency,
            "difficulty": p.difficulty
        }
        for p in patterns
    ]
