from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from app.models.domain import QuestionBank, InterviewQuestion, UserProfile
from app.services.interview_academy import ACADEMY_CATEGORIES

def get_weak_categories(db: Session) -> List[str]:
    """Finds interview categories with the lowest average score in user practices."""
    averages = []
    for category in ACADEMY_CATEGORIES:
        solved = db.query(InterviewQuestion).filter(
            InterviewQuestion.category.ilike(category)
        ).all()
        if solved:
            avg_score = sum(q.score for q in solved) / len(solved)
            averages.append((category, avg_score))
        else:
            # High priority to select since never practiced
            averages.append((category, -1.0))
            
    # Sort by score ascending (-1 first, then lowest scores)
    averages.sort(key=lambda x: x[1])
    return [item[0] for item in averages]

def generate_adaptive_quiz(
    db: Session, 
    profile: UserProfile, 
    missing_skills: List[str], 
    quiz_type: str = "daily"
) -> List[Dict[str, Any]]:
    """
    Selects curated questions adaptively from QuestionBank:
    - Prioritizes skills missing from the user's target profile/roadmap.
    - Focuses on categories identified as the user's interview weaknesses.
    - Limits to user seniority level appropriate questions.
    """
    # 1. Determine target difficulty range based on experience_years
    if profile.experience_years >= 8:
        target_diffs = ["Senior", "Staff", "Advanced"]
    elif profile.experience_years >= 5:
        target_diffs = ["Advanced", "Senior", "Intermediate"]
    elif profile.experience_years >= 2:
        target_diffs = ["Intermediate", "Advanced", "Easy"]
    else:
        target_diffs = ["Beginner", "Easy", "Intermediate"]

    # 2. Get weak categories
    weak_categories = get_weak_categories(db)
    
    # 3. Gather candidate categories from roadmap gaps (missing skills)
    roadmap_categories = []
    for skill in missing_skills:
        # Match skill strings to our category names
        for cat in ACADEMY_CATEGORIES:
            if skill.lower() in cat.lower() or cat.lower() in skill.lower():
                roadmap_categories.append(cat)
                
    # Combine candidate categories prioritizing roadmap gaps, then weak areas
    preferred_categories = roadmap_categories + [c for c in weak_categories if c not in roadmap_categories]

    # 4. Fetch questions from bank
    # Select from QuestionBank that fit preferred categories and target difficulty
    candidates = []
    
    # Check what questions the user has already answered with a high score to exclude them
    well_solved = db.query(InterviewQuestion.question).filter(
        InterviewQuestion.score >= 8
    ).all()
    solved_questions_texts = [q[0].lower().strip() for q in well_solved]

    for cat in preferred_categories:
        query = db.query(QuestionBank).filter(
            QuestionBank.category == cat,
            QuestionBank.difficulty.in_(target_diffs)
        )
        cat_q = query.all()
        for q in cat_q:
            if q.question.lower().strip() not in solved_questions_texts:
                candidates.append(q)

    # Fallback to any difficulty/category if candidate list is too small
    if len(candidates) < 10:
        all_q = db.query(QuestionBank).all()
        for q in all_q:
            if q.question.lower().strip() not in solved_questions_texts and q not in candidates:
                candidates.append(q)

    # 5. Select quiz size
    if quiz_type == "weekly":
        limit = 10
    elif quiz_type == "monthly":
        limit = 15
    else:
        limit = 5  # daily

    selected = candidates[:limit]

    return [
        {
            "id": q.id,
            "question": q.question,
            "category": q.category,
            "difficulty": q.difficulty,
            "tags": q.tags
        }
        for q in selected
    ]
