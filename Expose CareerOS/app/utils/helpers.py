import os
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy.orm import Session
from app.services import profile_service

# Locate templates directory relative to app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

def render_template(template_name: str, request: Request, db: Session, **context):
    """
    Renders a Jinja2 template and injects global context fields:
    - dark_mode (derived from cookie)
    - user_profile (cached profile details for header summary)
    """
    theme = request.cookies.get("theme", "light")
    dark_mode = (theme == "dark")
    
    user_profile = profile_service.get_profile(db)
    
    full_context = {
        "request": request,
        "dark_mode": dark_mode,
        "user_profile": user_profile,
        **context
    }
    
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=full_context
    )
