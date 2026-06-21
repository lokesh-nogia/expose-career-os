from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.helpers import render_template, templates
from app.services import interview_service, interview_academy, quiz_intelligence, profile_service
from app.models.domain import InterviewCreate, InterviewUpdate, InterviewQuestion, QuestionBank

router = APIRouter()

@router.get("/interviews")
def get_interviews_page(
    request: Request,
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Serves the interview questions library, returning lists for HTMX filters."""
    questions = interview_service.list_interviews(db, search=search, difficulty=difficulty)
    
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            request=request,
            name="components/interview_list.html",
            context={
                "questions": questions
            }
        )
        
    return render_template(
        "pages/interviews.html",
        request=request,
        db=db,
        active_page="interviews",
        questions=questions,
        selected_difficulty=difficulty or "",
        search_query=search or ""
    )

@router.post("/interviews")
def create_interview(
    request: Request,
    company: str = Form(...),
    question: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    personal_answer: Optional[str] = Form(""),
    score: Optional[int] = Form(0),
    feedback: Optional[str] = Form(""),
    db: Session = Depends(get_db)
):
    """Creates a new interview prep card and returns the refreshed library list."""
    question_data = InterviewCreate(
        company=company,
        question=question,
        category=category,
        difficulty=difficulty,
        personal_answer=personal_answer,
        score=score,
        feedback=feedback
    )
    interview_service.create_interview(db, question_data)
    
    questions = interview_service.list_interviews(db)
    
    headers = {"HX-Trigger": "interviewAdded"}
    
    return templates.TemplateResponse(
        request=request,
        name="components/interview_list.html",
        context={
            "questions": questions
        },
        headers=headers
    )

@router.get("/interviews/{question_id}/edit")
def get_edit_card(request: Request, question_id: int, db: Session = Depends(get_db)):
    """Returns the editing interface for a question card."""
    question = interview_service.get_interview(db, question_id)
    if not question:
        return Response(status_code=404)
        
    return templates.TemplateResponse(
        request=request,
        name="components/interview_edit_card.html",
        context={
            "question": question
        }
    )

@router.get("/interviews/{question_id}/cancel")
def cancel_edit_card(request: Request, question_id: int, db: Session = Depends(get_db)):
    """Cancels editing and returns the read-only card view."""
    question = interview_service.get_interview(db, question_id)
    if not question:
        return Response(status_code=404)
        
    return templates.TemplateResponse(
        request=request,
        name="components/interview_card.html",
        context={
            "question": question
        }
    )

@router.post("/interviews/{question_id}/edit")
def update_interview(
    request: Request,
    question_id: int,
    company: str = Form(...),
    question: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    personal_answer: Optional[str] = Form(""),
    score: Optional[int] = Form(0),
    feedback: Optional[str] = Form(""),
    db: Session = Depends(get_db)
):
    """Updates a question and returns its default card view."""
    question_data = InterviewUpdate(
        company=company,
        question=question,
        category=category,
        difficulty=difficulty,
        personal_answer=personal_answer,
        score=score,
        feedback=feedback
    )
    
    updated_question = interview_service.update_interview(db, question_id, question_data)
    if not updated_question:
        return Response(status_code=404)
        
    return templates.TemplateResponse(
        request=request,
        name="components/interview_card.html",
        context={
            "question": updated_question
        }
    )

@router.delete("/interviews/{question_id}")
def delete_interview(question_id: int, db: Session = Depends(get_db)):
    """Removes a question and deletes its card element from DOM."""
    success = interview_service.delete_interview(db, question_id)
    if not success:
        return Response(status_code=404)
    return Response(content="")

# ==========================================
# Phase 3 Academy & Quiz Endpoints
# ==========================================

@router.get("/interviews/academy/data")
def get_academy_report(request: Request, db: Session = Depends(get_db)):
    """Returns HTMX fragment showing Academy Completion Status and Company Patterns."""
    stats = interview_academy.get_academy_status(db)
    patterns = interview_academy.get_company_patterns(db)
    
    return templates.TemplateResponse(
        request=request,
        name="components/academy_dashboard.html",
        context={
            "stats": stats,
            "patterns": patterns
        }
    )

@router.get("/interviews/quiz/generate")
def generate_quiz_view(request: Request, quiz_type: str = "daily", db: Session = Depends(get_db)):
    """Generates an adaptive quiz session and returns the HTML layout."""
    profile = profile_service.get_profile(db)
    # Get skill gaps
    from app.services import market_trend_engine
    trends = market_trend_engine.analyze_market_trends(db)
    demanded_skills = [s["skill_name"] for s in trends["demanded"]]
    user_skills = [sk.skill_name for sk in profile.skills]
    missing_skills = [s for s in demanded_skills if s.lower() not in [u.lower() for u in user_skills]]

    quiz_questions = quiz_intelligence.generate_adaptive_quiz(db, profile, missing_skills, quiz_type)
    
    return templates.TemplateResponse(
        request=request,
        name="components/quiz_session.html",
        context={
            "questions": quiz_questions,
            "quiz_type": quiz_type
        }
    )

@router.post("/interviews/quiz/submit")
def submit_quiz_answer(
    request: Request,
    question_id: int = Form(...),
    personal_answer: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Submits a quiz response, evaluates it deterministically,
    and creates a practiced question entry in the library.
    """
    q_bank_item = db.query(QuestionBank).filter(QuestionBank.id == question_id).first()
    if not q_bank_item:
        return Response("Question not found in bank", status_code=404)
        
    # Evaluate Answer
    # Simple deterministic evaluation checking for keyword inclusions and length
    score = 5
    feedback = "Answer submitted. Add more technical details and vocabulary."
    
    tags = q_bank_item.tags.split(",") if q_bank_item.tags else []
    matched_tags = [t for t in tags if t.strip().lower() in personal_answer.lower()]
    
    if len(personal_answer) > 100:
        score += 2
        
    if matched_tags:
        score += min(3, len(matched_tags))
        feedback = f"Good technical coverage of concepts: {', '.join(matched_tags)}."
        
    score = min(10, score)
    if score >= 8:
        feedback += " Strong answer meeting senior production standards."
        
    # Create InterviewQuestion practice card
    prep_card = InterviewQuestion(
        company="Academy Quiz",
        question=q_bank_item.question,
        category=q_bank_item.category,
        difficulty=q_bank_item.difficulty,
        personal_answer=personal_answer,
        score=score,
        feedback=feedback
    )
    db.add(prep_card)
    db.commit()
    db.refresh(prep_card)
    
    return templates.TemplateResponse(
        request=request,
        name="components/quiz_result.html",
        context={
            "question": q_bank_item,
            "score": score,
            "feedback": feedback
        }
    )
