from sqlalchemy.orm import Session
from app.models.domain import UserProfile, UserProfileUpdate, UserSkill

def get_profile(db: Session) -> UserProfile:
    """Retrieves the user profile, creating a default one if it doesn't exist."""
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile(
            full_name="",
            current_role="",
            experience_years=0,
            current_salary=0.0,
            target_role="",
            target_salary=0.0,
            target_timeline="6 Months",
            is_onboarded=False
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def update_profile(db: Session, update_data: UserProfileUpdate) -> UserProfile:
    """Updates the user profile and updates the related UserSkill records."""
    profile = get_profile(db)
    profile.full_name = update_data.full_name
    profile.current_role = update_data.current_role
    profile.experience_years = update_data.experience_years
    profile.current_salary = update_data.current_salary
    profile.target_salary = update_data.target_salary
    profile.target_role = update_data.target_role
    profile.target_timeline = update_data.target_timeline

    # Parse and update skills relational mapping
    db.query(UserSkill).filter(UserSkill.user_profile_id == profile.id).delete()
    
    if update_data.skills:
        for sk in update_data.skills.split(","):
            sk_name = sk.strip()
            if sk_name:
                user_sk = UserSkill(
                    user_profile_id=profile.id,
                    skill_name=sk_name,
                    level="Intermediate"  # default to Intermediate upon inline text updates
                )
                db.add(user_sk)
                
    db.commit()
    db.refresh(profile)
    return profile
