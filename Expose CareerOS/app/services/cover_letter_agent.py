from sqlalchemy.orm import Session
from app.models.domain import UserProfile, JobPosting, CompanyInsight

def generate_cover_letter(db: Session, profile: UserProfile, job: JobPosting) -> str:
    """
    Generates a professional, customized cover letter from:
    - User Profile (name, current role, experience years)
    - Job Posting (title, company, description, location)
    - Company Information (industry, rating, hiring status from CompanyInsight)
    """
    # 1. Fetch Company Insight details if available
    insight = db.query(CompanyInsight).filter(
        CompanyInsight.company_name.ilike(job.company)
    ).first()

    company_detail = ""
    if insight:
        company_detail = f"I have been following {job.company}'s work in the {insight.industry or 'tech'} sector, and I am excited by your organization's reputation"
        if insight.rating and insight.rating > 4.0:
            company_detail += f" (consistently recognized for corporate excellence)"
        company_detail += ". "
    else:
        company_detail = f"I am deeply familiar with {job.company}'s market footprint and technical leadership. "

    # 2. Map core user skills matching job postings
    user_skills = [s.skill_name for s in profile.skills]
    job_skills_query = job.skills
    job_skill_names = [sk.skill_name for sk in job_skills_query]
    
    shared_skills = [s for s in user_skills if s.lower() in [j.lower() for j in job_skill_names]]
    if not shared_skills:
        shared_skills = user_skills[:3]  # fallback to top user skills

    skills_phrase = ", ".join(shared_skills[:3])

    # 3. Assemble cover letter paragraphs
    date_str = datetime_to_date_str()
    
    letter = f"""{profile.full_name or 'Applicant'}
Contact Info: Available on Profile
Date: {date_str}

Hiring Team
{job.company}
{job.location or 'Remote'}

Subject: Application for {job.title}

Dear Hiring Committee,

I am writing to express my strong interest in the {job.title} position at {job.company}. {company_detail}With {profile.experience_years} years of professional experience as a {profile.current_role or 'Software Engineer'}, I am confident that my specialized skills in {skills_phrase} align perfectly with the engineering demands of this role.

In my previous projects, I have focused heavily on designing stable backend services, scaling transactional databases, and maintaining reliable systems. The opportunity to deploy these capabilities to solve low-latency infrastructure problems at {job.company} is highly motivating to me.

Specifically, your job description highlights the need for robust software engineering practices. Throughout my career, I have prioritized clean code, writing comprehensive tests, and deploying containerized microservices. I look forward to bringing this engineering discipline to your growing development team.

Thank you for your time and consideration. I have attached my customized resume detailing my project outcomes and technical background. I welcome the opportunity to discuss how my background can help {job.company} achieve its technical goals.

Sincerely,

{profile.full_name or 'Applicant'}"""
    return letter

def datetime_to_date_str() -> str:
    from datetime import date
    return date.today().strftime("%B %d, %Y")

def generate_cover_letter_v2(db: Session, profile: UserProfile, job: JobPosting) -> tuple[str, int]:
    """
    Generates a cover letter featuring:
    - Company-specific tailoring
    - Role-specific positioning
    - Gap acknowledgement
    - Strength highlighting
    Returns a tuple: (letter_text, confidence_score)
    """
    from app.services.ai_provider import AIProviderFactory
    provider = AIProviderFactory.get_provider()
    
    if provider:
        try:
            resume_text = (
                f"Candidate: {profile.full_name}\n"
                f"Role: {profile.current_role}\n"
                f"Experience: {profile.experience_years} years.\n"
                f"Skills: {', '.join([s.skill_name for s in profile.skills])}"
            )
            job_desc = f"Title: {job.title}\nCompany: {job.company}\nDescription: {job.description}"
            
            insight = db.query(CompanyInsight).filter(
                CompanyInsight.company_name.ilike(job.company)
            ).first()
            company_info = ""
            if insight:
                company_info = f"Industry: {insight.industry or ''}. Rating: {insight.rating or ''}."
            
            res = provider.generate_cover_letter(resume_text, job_desc, company_info)
            return res.get("letter", ""), int(res.get("confidence_score", 80))
        except Exception:
            pass  # Fallback to local rule builder

    # Local fallback
    letter_text = generate_cover_letter(db, profile, job)
    
    # Calculate deterministic confidence
    user_skills = [s.skill_name.lower() for s in profile.skills]
    job_skills = [sk.skill_name.lower() for sk in job.skills]
    if not job_skills:
        confidence = 70
    else:
        shared = [s for s in user_skills if s in job_skills]
        confidence = int((len(shared) / len(job_skills)) * 100)
        
    return letter_text, min(100, max(40, confidence))
