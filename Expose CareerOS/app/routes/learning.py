from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.helpers import render_template
from app.services import roadmap_engine, market_trend_engine
from app.services.profile_service import get_profile

router = APIRouter()

@router.get("/learning")
def get_learning_page(request: Request, db: Session = Depends(get_db)):
    """Serves the dynamic Career Roadmap path page, reflecting skill gaps."""
    profile = get_profile(db)
    
    # Calculate skill gaps dynamically
    trends = market_trend_engine.analyze_market_trends(db)
    demanded_skills = [s["skill_name"] for s in trends["demanded"]]
    user_skills = [sk.skill_name for sk in profile.skills]
    missing_skills = [s for s in demanded_skills if s.lower() not in [u.lower() for u in user_skills]]
    
    # Generate dynamic learning roadmap
    roadmap = roadmap_engine.generate_roadmap(db, profile, missing_skills)
    
    return render_template(
        "pages/learning.html",
        request=request,
        db=db,
        active_page="learning",
        profile=profile,
        roadmap=roadmap
    )
