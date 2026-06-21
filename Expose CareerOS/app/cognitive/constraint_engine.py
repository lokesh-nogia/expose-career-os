from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import UserProfile, InterviewQuestion

def evaluate_constraints(db: Session, profile: UserProfile) -> dict:
    """
    Evaluates real-world limits: weekly hours available, experience level constraints,
    and weak skill retention areas.
    """
    # 1. Available weekly hours calculation
    # Emulate constraint based on target timeline or current role
    is_actively_hunting = "month" in profile.target_timeline.lower() or "immediate" in profile.target_timeline.lower()
    
    if is_actively_hunting:
        hours_available = 25  # High availability
    else:
        hours_available = 12  # Limited hours due to current job

    # 2. Identify weak areas from solved interview questions with score < 7.0
    weak_categories_query = db.query(
        InterviewQuestion.category,
        func.avg(InterviewQuestion.score).label("avg_score")
    ).filter(InterviewQuestion.score > 0)\
     .group_by(InterviewQuestion.category)\
     .having(func.avg(InterviewQuestion.score) < 7.0).all()
     
    weak_areas = [row[0] for row in weak_categories_query]
    if not weak_areas:
        # Fallback if no questions scored yet
        weak_areas = ["System Design"]

    # 3. Experience level constraint
    if profile.experience_years >= 8:
        level_label = "Staff/Lead"
        complexity_limit = "High"
    elif profile.experience_years >= 4:
        level_label = "Senior"
        complexity_limit = "Medium-High"
    else:
        level_label = "Junior/Mid"
        complexity_limit = "Medium"

    return {
        "hours_available": hours_available,
        "weak_areas": weak_areas,
        "experience_level": level_label,
        "complexity_limit": complexity_limit
    }

def filter_tasks_by_constraints(db: Session, profile: UserProfile, tasks: list) -> list:
    """
    Filters and formats weekly tasks to ensure they fit within the weekly hour constraints.
    Each task should be a dict with keys: 'description', 'time_required_hours'.
    """
    limits = evaluate_constraints(db, profile)
    max_hours = limits["hours_available"]
    
    feasible_tasks = []
    total_hours = 0
    
    for task in tasks:
        task_hours = task.get("time_required_hours", 2)
        if total_hours + task_hours <= max_hours:
            feasible_tasks.append(task)
            total_hours += task_hours
            
    return feasible_tasks
