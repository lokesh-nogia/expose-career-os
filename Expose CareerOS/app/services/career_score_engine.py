from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import UserProfile, JobPosting, JobSkill, InterviewQuestion, UserSkill
from app.models.contracts import CareerScoreResult

def calculate_career_score(db: Session, profile: UserProfile) -> CareerScoreResult:
    """
    Computes a weighted 0-100 Career Score tracking professional strength:
    - Market Alignment: 40% (Top 10 demanded skills owned by user)
    - Skill Depth: 30% (Average proficiency level of user skills)
    - Interview Readiness: 20% (Average score of interview prep questions)
    - Learning Progress: 10% (Ratio of skills validated by project evidence)
    """
    breakdown = {}
    quick_wins = []
    
    # --------------------------------------------------
    # 1. Market Alignment (40%)
    # --------------------------------------------------
    total_jobs = db.query(JobPosting).count()
    if total_jobs > 0:
        # Get top 10 skills demanded
        top_skills_query = db.query(
            JobSkill.skill_name,
            func.count(JobSkill.id)
        ).group_by(JobSkill.skill_name).order_by(
            func.count(JobSkill.id).desc()
        ).limit(10).all()
        
        top_10_skills = [s[0] for s in top_skills_query]
        user_skill_names = [s.skill_name.lower() for s in profile.skills]
        
        if top_10_skills:
            matched = [s for s in top_10_skills if s.lower() in user_skill_names]
            alignment_pct = len(matched) / len(top_10_skills)
            alignment_score = alignment_pct * 40.0
            
            # Suggest adding missing top demanded skills as quick wins
            missing_top = [s for s in top_10_skills if s.lower() not in user_skill_names]
            for s in missing_top[:2]:
                quick_wins.append(f"Add '{s}' skill to your profile (estimated +4.0 points)")
        else:
            alignment_score = 20.0
    else:
        alignment_score = 20.0  # Neutral fallback when no jobs exist
        
    breakdown["market_alignment"] = round(alignment_score, 1)

    # --------------------------------------------------
    # 2. Skill Depth (30%)
    # --------------------------------------------------
    # Advanced = 30 pts, Intermediate = 18 pts, Beginner = 9 pts
    if profile.skills:
        skill_points = 0.0
        for sk in profile.skills:
            if sk.level == "Advanced":
                skill_points += 30.0
            elif sk.level == "Intermediate":
                skill_points += 18.0
            else:
                skill_points += 9.0
        avg_depth = skill_points / len(profile.skills)
        depth_score = (avg_depth / 30.0) * 30.0
        
        # Suggest upgrading Beginner/Intermediate skills
        for sk in profile.skills:
            if sk.level in ["Beginner", "Intermediate"]:
                quick_wins.append(f"Upgrade '{sk.skill_name}' skill level to Advanced (estimated +1.5 points)")
                break
    else:
        depth_score = 0.0
        quick_wins.append("Add your first core skill to initialize Skill Depth scoring.")
        
    breakdown["skill_depth"] = round(depth_score, 1)

    # --------------------------------------------------
    # 3. Interview Readiness (20%)
    # --------------------------------------------------
    questions = db.query(InterviewQuestion).all()
    if questions:
        avg_interview = sum(q.score for q in questions) / len(questions)
        interview_score = (avg_interview / 10.0) * 20.0
        
        # Suggest practicing low scored questions
        low_score_q = db.query(InterviewQuestion).filter(InterviewQuestion.score < 7).first()
        if low_score_q:
            quick_wins.append(f"Practice and score '{low_score_q.question[:25]}...' question (estimated +2.0 points)")
    else:
        interview_score = 0.0
        quick_wins.append("Solve your first Interview Practice question to score readiness (estimated +5.0 points)")
        
    breakdown["interview_readiness"] = round(interview_score, 1)

    # --------------------------------------------------
    # 4. Learning Progress (10%)
    # --------------------------------------------------
    # % of skills containing at least 1 evidence entry
    if profile.skills:
        skills_with_evidence = sum(1 for s in profile.skills if len(s.evidence) > 0)
        progress_pct = skills_with_evidence / len(profile.skills)
        learning_score = progress_pct * 10.0
        
        # Suggest adding evidence to a skill
        for sk in profile.skills:
            if not sk.evidence:
                quick_wins.append(f"Link a project project evidence for '{sk.skill_name}' (estimated +1.0 points)")
                break
    else:
        learning_score = 0.0
        
    breakdown["learning_progress"] = round(learning_score, 1)

    # Calculate overall total score
    total_score = round(alignment_score + depth_score + interview_score + learning_score, 1)

    return CareerScoreResult(
        score=total_score,
        breakdown=breakdown,
        quick_wins=quick_wins[:3]  # Limit to top 3 quick wins
    )
