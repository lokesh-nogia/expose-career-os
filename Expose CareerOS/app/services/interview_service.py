from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.domain import InterviewQuestion, InterviewCreate, InterviewUpdate

def list_interviews(db: Session, search: Optional[str] = None, difficulty: Optional[str] = None) -> List[InterviewQuestion]:
    """Lists all interview questions, with optional search and difficulty filters."""
    query = db.query(InterviewQuestion)
    
    if difficulty and difficulty.strip():
        query = query.filter(InterviewQuestion.difficulty == difficulty)
        
    if search and search.strip():
        search_term = f"%{search}%"
        query = query.filter(
            (InterviewQuestion.company.ilike(search_term)) | 
            (InterviewQuestion.question.ilike(search_term)) | 
            (InterviewQuestion.category.ilike(search_term)) |
            (InterviewQuestion.personal_answer.ilike(search_term))
        )
        
    return query.order_by(InterviewQuestion.id.desc()).all()

def get_interview(db: Session, question_id: int) -> Optional[InterviewQuestion]:
    """Retrieves a single interview question by ID."""
    return db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()

def create_interview(db: Session, data: InterviewCreate) -> InterviewQuestion:
    """Creates a new interview question record."""
    question = InterviewQuestion(
        company=data.company,
        question=data.question,
        category=data.category,
        difficulty=data.difficulty,
        personal_answer=data.personal_answer,
        score=data.score,
        feedback=data.feedback
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question

def update_interview(db: Session, question_id: int, data: InterviewUpdate) -> Optional[InterviewQuestion]:
    """Updates the details of an existing interview question."""
    question = get_interview(db, question_id)
    if not question:
        return None
    question.company = data.company
    question.question = data.question
    question.category = data.category
    question.difficulty = data.difficulty
    question.personal_answer = data.personal_answer
    question.score = data.score
    question.feedback = data.feedback
    db.commit()
    db.refresh(question)
    return question

def update_score(db: Session, question_id: int, score: int, feedback: Optional[str] = None) -> Optional[InterviewQuestion]:
    """Updates the score and feedback for an interview question."""
    question = get_interview(db, question_id)
    if not question:
        return None
    question.score = max(0, min(10, score))
    if feedback is not None:
        question.feedback = feedback
    db.commit()
    db.refresh(question)
    return question

def delete_interview(db: Session, question_id: int) -> bool:
    """Deletes an interview question record."""
    question = get_interview(db, question_id)
    if not question:
        return False
    db.delete(question)
    db.commit()
    return True
