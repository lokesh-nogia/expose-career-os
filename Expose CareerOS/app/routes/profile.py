from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.helpers import render_template, templates
from app.services import profile_service
from app.models.domain import UserProfileUpdate

router = APIRouter()

@router.get("/profile")
def get_profile(request: Request, db: Session = Depends(get_db)):
    """Serves the user profile dashboard page."""
    profile = profile_service.get_profile(db)
    return render_template(
        "pages/profile.html",
        request=request,
        db=db,
        active_page="profile",
        profile=profile
    )

@router.get("/profile/edit")
def edit_profile(request: Request, db: Session = Depends(get_db)):
    """Returns the profile edit form component."""
    profile = profile_service.get_profile(db)
    return templates.TemplateResponse(
        request=request,
        name="components/profile_card.html",
        context={
            "profile": profile,
            "edit_mode": True
        }
    )

@router.get("/profile/view")
def view_profile(request: Request, db: Session = Depends(get_db)):
    """Returns the standard read-only profile view component."""
    profile = profile_service.get_profile(db)
    return templates.TemplateResponse(
        request=request,
        name="components/profile_card.html",
        context={
            "profile": profile,
            "edit_mode": False
        }
    )

@router.post("/profile")
def update_profile(
    request: Request,
    full_name: str = Form(...),
    current_role: str = Form(...),
    experience_years: int = Form(...),
    current_salary: float = Form(...),
    target_salary: float = Form(...),
    target_role: str = Form(...),
    target_timeline: str = Form(...),
    skills: str = Form(...),
    db: Session = Depends(get_db)
):
    """Saves profile modifications and returns updated component (incorporating topbar updates)."""
    update_data = UserProfileUpdate(
        full_name=full_name,
        current_role=current_role,
        experience_years=experience_years,
        current_salary=current_salary,
        target_salary=target_salary,
        target_role=target_role,
        target_timeline=target_timeline,
        skills=skills
    )
    profile = profile_service.update_profile(db, update_data)
    
    # Render profile card with edit_mode=False
    # Includes Out-of-Band (OOB) HTML snippets to update the top navigation bar header profile
    return templates.TemplateResponse(
        request=request,
        name="components/profile_card.html",
        context={
            "profile": profile,
            "edit_mode": False,
            "oob_update": True
        }
    )
