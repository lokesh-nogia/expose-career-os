import sys
from datetime import date, datetime
from fastapi.testclient import TestClient

# Ensure current directory is in search path
sys.path.insert(0, ".")

try:
    from app.main import app
    from app.database.connection import SessionLocal
    from app.models.domain import (
        UserProfile, UserSkill, JobPosting, ImportRun, 
        MarketSnapshot, DiscoveryRun, Resume, ResumeVersion, 
        ResumeDiff, ApplicationOutcome, Notification, 
        CompanyQuestionPattern, QuestionBank, InterviewQuestion,
        AgentState, RecommendationHistory
    )
    from app.services import (
        discovery_scheduler, resume_intelligence, job_match_agent,
        quiz_intelligence, career_coach_agent, interview_academy,
        notification_service, ai_provider
    )
    from app import agents
except ImportError as e:
    print(f"ImportError: Could not import app modules. Detail: {e}")
    sys.exit(1)

client = TestClient(app)

def test_health():
    """Verifies health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_onboarding_redirection():
    """Verifies that non-onboarded profile redirects to the wizard page."""
    # Reset is_onboarded to False to ensure redirect occurs
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if profile:
            profile.is_onboarded = False
            db.commit()
    finally:
        db.close()

    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 303, 307]
    assert response.headers.get("location") == "/onboarding"

def test_onboarding_wizard_page():
    """Verifies onboarding wizard page loading."""
    response = client.get("/onboarding")
    assert response.status_code == 200
    assert "setup" in response.text.lower() or "wizard" in response.text.lower() or "onboarding" in response.text.lower()

def test_onboarding_submission():
    """Verifies submitting onboarding details succeeds and initializes user parameters."""
    form_data = {
        "full_name": "Lokesh Nogia",
        "current_role": "SDE - Java",
        "experience_years": 4,
        "current_salary": 8.5,
        "target_role": "Senior Java Backend Engineer",
        "target_salary": 18.0,
        "target_timeline": "6 Months",
        "skill_check_Java": "on",
        "level_Java": "Advanced",
        "skill_check_SpringBoot": "on",
        "level_SpringBoot": "Advanced",
        "skill_check_PostgreSQL": "on",
        "level_PostgreSQL": "Intermediate",
    }
    response = client.post("/onboarding/submit", data=form_data, follow_redirects=False)
    assert response.status_code in [302, 303]
    
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        assert profile.is_onboarded is True
        assert profile.full_name == "Lokesh Nogia"
        assert profile.current_salary == 8.5
        assert profile.target_salary == 18.0
        
        skills = db.query(UserSkill).filter(UserSkill.user_profile_id == profile.id).all()
        assert len(skills) == 3
    finally:
        db.close()

def test_onboarded_dashboard():
    """Verifies dashboard loading after onboarding wizard has run successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Workstation" in response.text
    assert "Lokesh Nogia" in response.text
    assert "Senior Java Backend Engineer" in response.text

def test_profile_update_flow():
    """Verifies that the profile edit form can be loaded and successfully submitted."""
    response = client.get("/profile")
    assert response.status_code == 200
    assert "Lokesh Nogia" in response.text

    response = client.get("/profile/edit")
    assert response.status_code == 200
    assert "Edit Profile" in response.text or "Profile" in response.text

    # Submit profile update
    form_data = {
        "full_name": "Lokesh Nogia Edited",
        "current_role": "SDE III - Java",
        "experience_years": 5,
        "current_salary": 9.5,
        "target_role": "Lead Java Backend Engineer",
        "target_salary": 20.0,
        "target_timeline": "12 Months",
        "skills": "Java, Spring Boot, PostgreSQL, Docker, AWS"
    }
    response = client.post("/profile", data=form_data)
    assert response.status_code == 200
    assert "Lokesh Nogia Edited" in response.text
    assert "Lead Java Backend Engineer" in response.text

    # Check view mode
    response = client.get("/profile/view")
    assert response.status_code == 200
    assert "Lokesh Nogia Edited" in response.text

    # Revert to clean state for subsequent tests
    form_data_original = {
        "full_name": "Lokesh Nogia",
        "current_role": "SDE - Java",
        "experience_years": 4,
        "current_salary": 8.5,
        "target_role": "Senior Java Backend Engineer",
        "target_salary": 18.0,
        "target_timeline": "6 Months",
        "skills": "Java, SpringBoot, PostgreSQL"
    }
    client.post("/profile", data=form_data_original)

def test_csv_ingestion_pipeline():
    """Verifies triggering the CSV Ingestion Pipeline, creating snapshot logs and score updates."""
    response = client.post("/dashboard/import-csv")
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/"
    
    db = SessionLocal()
    try:
        postings = db.query(JobPosting).all()
        assert len(postings) > 0
        
        audit = db.query(ImportRun).first()
        assert audit is not None
        assert audit.status == "Success"
        
        snap = db.query(MarketSnapshot).first()
        assert snap is not None
        assert len(snap.skills) > 0

        disc = db.query(DiscoveryRun).first()
        assert disc is not None
        assert disc.status == "Success"
        assert disc.records_imported > 0
    finally:
        db.close()

def test_onboarded_dashboard_with_scores():
    """Verifies that after CSV ingestion, the dashboard correctly computes intelligence metrics."""
    response = client.get("/")
    assert response.status_code == 200
    
    assert "Career Score Rating" in response.text
    assert "Target Role Readiness" in response.text
    assert "Matched Skills" in response.text
    assert "Core Skill Gaps" in response.text
    assert "Salary Intelligence" in response.text
    assert "Market Average" in response.text

def test_discovery_scheduler():
    """Tests discovery scheduler freshness calculation."""
    db = SessionLocal()
    try:
        freshness = discovery_scheduler.check_data_freshness(db)
        assert freshness["last_run"] is not None
        assert freshness["refresh_recommended"] in [True, False]
        assert "Fresh" in freshness["status_label"] or "Stale" in freshness["status_label"]
    finally:
        db.close()

def test_resume_versioning_and_diff():
    """Tests resume variant compilation, versioning, and diff tracking."""
    db = SessionLocal()
    try:
        db.query(ResumeDiff).delete()
        db.query(ResumeVersion).delete()
        db.query(Resume).delete()
        db.commit()

        profile = db.query(UserProfile).first()
        job = db.query(JobPosting).first()
        assert profile is not None
        assert job is not None
        
        # Create first variant version
        v1 = resume_intelligence.create_resume_variant(db, profile, job, "Test Specific Resume")
        assert v1.version_number == 1
        assert v1.match_score is not None
        
        # Create second variant version
        v2 = resume_intelligence.create_resume_variant(db, profile, job, "Test Specific Resume")
        assert v2.version_number == 2
        
        # Check diff exists
        diff = db.query(ResumeDiff).filter(ResumeDiff.resume_version_id == v2.id).first()
        assert diff is not None
        assert diff.diff_text is not None
    finally:
        db.close()

def test_opportunity_learning():
    """Verifies application outcome tracking to check correlation metrics."""
    db = SessionLocal()
    try:
        db.query(ApplicationOutcome).delete()
        db.commit()

        job = db.query(JobPosting).first()
        assert job is not None
        
        outcome = ApplicationOutcome(
            job_posting_id=job.id,
            opportunity_score=85.0,
            result="Interview",
            notes="Outcome logged for test cases."
        )
        db.add(outcome)
        db.commit()
        
        saved = db.query(ApplicationOutcome).filter(ApplicationOutcome.job_posting_id == job.id).first()
        assert saved is not None
        assert saved.result == "Interview"
        assert saved.opportunity_score == 85.0
    finally:
        db.close()

def test_notification_system():
    """Verifies custom notification creation and clearing APIs."""
    db = SessionLocal()
    try:
        # Create Notification
        notif = notification_service.create_notification(db, "test_alert", "This is an alert integration test message.")
        assert notif.read is False
        
        # List notifications
        unread = notification_service.list_notifications(db, unread_only=True)
        assert len(unread) > 0
        
        # Mark single read
        success = notification_service.mark_as_read(db, notif.id)
        assert success is True
        assert notif.read is True
    finally:
        db.close()

def test_career_coach():
    """Verifies Career Coach action plans formulation."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        plan = career_coach_agent.generate_weekly_career_plan(db, profile, ["Java", "Docker"])
        assert plan["weekly_objective"] is not None
        assert len(plan["tasks"]) == 3
        assert "+2.0 Points in Academy" in plan["expected_interview_readiness"]
    finally:
        db.close()

def test_interview_academy():
    """Verifies Interview Academy subject-level completions tracking."""
    db = SessionLocal()
    try:
        stats = interview_academy.get_academy_status(db)
        assert len(stats) == 10
        categories = [s["category"] for s in stats]
        assert "Java Core" in categories
        assert "Concurrency" in categories
        
        patterns = interview_academy.get_company_patterns(db)
        assert len(patterns) > 0
        assert patterns[0]["company"] in ["Amazon", "Google", "Stripe", "Atlassian", "Uber", "Microsoft"]
    finally:
        db.close()

def test_adaptive_quiz_selection():
    """Verifies Quiz Intelligence adaptive curated questions selection."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        quiz_q = quiz_intelligence.generate_adaptive_quiz(db, profile, ["Java", "Concurrency"], "daily")
        assert len(quiz_q) <= 5
        for q in quiz_q:
            assert q["category"] in ["Java Core", "Collections", "Concurrency", "Spring Boot", "Microservices", "Kafka", "Docker", "AWS", "System Design", "Behavioral"]
    finally:
        db.close()

def test_orchestrator_loop_and_agent_state():
    """Verifies that the orchestrator loop completes successfully and saves the AgentState."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        assert profile is not None
        
        # Clear previous agent state
        db.query(AgentState).delete()
        db.commit()
        
        result = agents.run_orchestration_loop(db, profile)
        assert result.observation is not None
        assert result.weekly_plan is not None
        assert result.daily_plan is not None
        assert result.recommendations is not None
        assert result.daily_mission is not None
        
        # Verify AgentState record created
        state = db.query(AgentState).filter(AgentState.user_profile_id == profile.id).order_by(AgentState.id.desc()).first()
        assert state is not None
        assert state.current_readiness == result.observation.current_readiness
        assert state.current_salary_estimate == result.observation.salary_estimate
    finally:
        db.close()

def test_recommendation_history_filtering():
    """Verifies that rejected recommendations are not suggested again by the recommendation agent."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        assert profile is not None
        
        # Clear recommendation history
        db.query(RecommendationHistory).delete()
        db.commit()
        
        # Record a rejection memory for Kafka
        agents.record_recommendation_history(db, recommendation_text="Learn Kafka", accepted=False, rejected=True)
        
        snapshot = agents.observe_career_state(db, profile)
        # Ensure Kafka is in snapshot missing skills to test filtering
        if "Kafka" not in snapshot.missing_skills:
            snapshot.missing_skills.append("Kafka")
            
        weekly_plan, _ = agents.plan_career_actions(snapshot)
        recommendations = agents.generate_recommendations(db, weekly_plan)
        
        # Kafka should NOT be in the recommendations list
        recommended_topics = [r.topic.lower() for r in recommendations]
        assert "kafka" not in recommended_topics
    finally:
        db.close()

def test_dummy_ai_providers_failure():
    """Verifies that the stub AI providers correctly raise NotImplementedError and Gemini checks keys."""
    gemini = ai_provider.GeminiProvider(api_key=None)
    claude = ai_provider.ClaudeProvider()
    openai = ai_provider.OpenAIProvider()
    
    import pytest
    with pytest.raises(ValueError):
        gemini.analyze_resume("text", "role")
    with pytest.raises(NotImplementedError):
        claude.analyze_job_description("jd")
    with pytest.raises(NotImplementedError):
        openai.generate_cover_letter("text", "jd", "info")

def test_ai_provider_factory_and_gemini_fallback():
    """Asserts that the factory correctly instantiates Gemini if key exists, else falls back to deterministic critiques."""
    from app.services.ai_provider import AIProviderFactory, GeminiProvider
    import os
    
    # Save original key
    original_key = os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = "dummy_key"
        prov = AIProviderFactory.get_provider()
        assert isinstance(prov, GeminiProvider)
        
        del os.environ["GEMINI_API_KEY"]
        prov_none = AIProviderFactory.get_provider()
        assert prov_none is None
    finally:
        if original_key is not None:
            os.environ["GEMINI_API_KEY"] = original_key

def test_application_package_workflow():
    """Tests Draft -> Approved -> Submitted lifecycle of ApplicationPackages."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        job = db.query(JobPosting).first()
        assert profile is not None
        assert job is not None
        
        from app.models.domain import ApplicationPackage
        db.query(ApplicationPackage).delete()
        db.commit()
        
        from app.services.resume_intelligence import create_resume_variant
        resume_ver = create_resume_variant(db, profile, job, "Workflow Resume")
        
        package = ApplicationPackage(
            job_posting_id=job.id,
            match_score=85.0,
            resume_version_id=resume_ver.id,
            cover_letter="Cover letter body details",
            status="Draft"
        )
        db.add(package)
        db.commit()
        db.refresh(package)
        
        assert package.status == "Draft"
        
        # Test Approve
        response_approve = client.post(f"/dashboard/packages/{package.id}/approve")
        assert response_approve.status_code == 200
        assert "Approved" in response_approve.text
        
        db.refresh(package)
        assert package.status == "Approved"
        
        # Test Export
        from app.services.execution_service import export_package
        exported = export_package(db, package.id)
        assert exported["job_title"] == job.title
        assert "Cover letter body details" in exported["cover_letter"]
        
        # Test Submit
        response_submit = client.post(f"/dashboard/packages/{package.id}/submit")
        assert response_submit.status_code == 200
        
        db.refresh(package)
        assert package.status == "Submitted"
    finally:
        db.query(ApplicationPackage).delete()
        db.query(ApplicationOutcome).delete()
        db.commit()
        db.close()

def test_outcome_analyzer_metrics():
    """Verifies OutcomeAnalyzer output stats and success predictors calculations."""
    db = SessionLocal()
    try:
        from app.services.outcome_analyzer import analyze_outcomes
        res = analyze_outcomes(db)
        assert "funnel" in res
        assert "success_predictors" in res
        assert len(res["success_predictors"]) > 0
        assert res["success_predictors"][0]["likelihood_multiplier"] > 0
    finally:
        db.close()

def test_readiness_prediction_forecasting():
    """Verifies 30, 60, and 90-day role readiness predictions."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        assert profile is not None
        
        from app.services.readiness_prediction import predict_readiness
        res = predict_readiness(db, profile)
        assert "current_role_readiness" in res
        assert "target_role_readiness" in res
        assert "projections" in res
        assert res["projections"]["days_30"] > 0
        assert res["projections"]["days_90"] >= res["projections"]["days_30"]
    finally:
        db.close()

def test_cognitive_intelligence_layer():
    """Verifies all engines of the Phase 5.5 Career Cognitive Intelligence Layer."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        assert profile is not None
        
        # 1. Forecasting Engine
        from app.cognitive.forecasting_engine import forecast_outcomes
        forecasts = forecast_outcomes(db, profile)
        assert "readiness" in forecasts
        assert "salary" in forecasts
        assert "interview" in forecasts
        assert forecasts["readiness"]["days_90"] >= forecasts["readiness"]["current"]

        # 2. ROI Engine
        from app.cognitive.roi_engine import calculate_skills_roi
        roi_res = calculate_skills_roi(db, ["Kafka", "Docker", "AWS"])
        assert len(roi_res) == 3
        assert roi_res[0]["roi_score"] >= roi_res[2]["roi_score"]
        
        # 3. Prioritization Engine
        from app.cognitive.prioritization_engine import prioritize_opportunities
        priorities = prioritize_opportunities(db, profile)
        assert len(priorities) > 0
        assert priorities[0]["priority_score"] >= priorities[-1]["priority_score"]
        
        # 4. Constraint Engine
        from app.cognitive.constraint_engine import evaluate_constraints
        constraints = evaluate_constraints(db, profile)
        assert "hours_available" in constraints
        assert "weak_areas" in constraints
        assert len(constraints["weak_areas"]) > 0
        
        # 5. Scenario Engine
        from app.cognitive.scenario_engine import simulate_scenarios
        scenarios = simulate_scenarios(db, profile)
        assert len(scenarios) == 3
        assert scenarios[0]["name"] == "Backend Engineer"
        
        # 6. Strategy Engine
        from app.cognitive.career_strategy_engine import generate_strategy
        strategy = generate_strategy(db, profile)
        assert "timeline" in strategy
        assert "months_6" in strategy["timeline"]
        assert "months_12" in strategy["timeline"]
        assert "months_18" in strategy["timeline"]

        # 7. Decision Engine
        from app.cognitive.decision_engine import make_decisions
        decisions = make_decisions(db, profile)
        assert "recommendations" in decisions
        assert "risks" in decisions
        assert len(decisions["recommendations"]) > 0
        
        # 8. Career Brief Generator
        from app.cognitive.career_brief_generator import generate_weekly_career_brief
        brief = generate_weekly_career_brief(db, profile)
        assert brief["current_market_value"] == forecasts["salary"]["current"]
        assert len(brief["highest_roi_skills"]) <= 3
        
        # 9. HTTP GET /dashboard/executive-report
        response = client.get("/dashboard/executive-report")
        assert response.status_code == 200
        assert "Cognitive Trajectory Forecasts" in response.text
        assert "Career Path Scenario Simulation" in response.text
        assert "Explainable Decision Matrix" in response.text
        assert "Prioritized Activity Queue" in response.text
        assert "Missing Skill ROI Matrix" in response.text
        assert "Long-Term Strategic Milestones" in response.text
    finally:
        db.close()

if __name__ == "__main__":
    print("==================================================")
    print("RUNNING REFACTORED EXPOSE AUTOSPY INTEGRATION TESTS")
    print("==================================================")
    
    try:
        test_health()
        print("[PASS] 1. Health check endpoint verified.")
        
        test_onboarding_redirection()
        print("[PASS] 2. First-run onboarding redirection reset and verified.")
        
        test_onboarding_wizard_page()
        print("[PASS] 3. Onboarding wizard page loading verified.")
        
        test_onboarding_submission()
        print("[PASS] 4. Onboarding wizard submission verified.")
        
        test_onboarded_dashboard()
        print("[PASS] 5. Onboarded dashboard rendering verified.")
        
        test_profile_update_flow()
        print("[PASS] 5b. Profile update workflow verified.")
        
        test_csv_ingestion_pipeline()
        print("[PASS] 6. Job Discovery pipeline and audits verified.")
        
        test_onboarded_dashboard_with_scores()
        print("[PASS] 7. Score calculations, Matched Skills, and Market Average verified.")
 
        test_discovery_scheduler()
        print("[PASS] 8. Discovery Scheduler freshness audits verified.")
 
        test_resume_versioning_and_diff()
        print("[PASS] 9. Resume version control, variant generation and diffs verified.")
 
        test_opportunity_learning()
        print("[PASS] 10. Opportunity Learning outcome logging verified.")
 
        test_notification_system()
        print("[PASS] 11. Notification alerts pipeline verified.")
 
        test_career_coach()
        print("[PASS] 12. Career Coach weekly action planner verified.")
 
        test_interview_academy()
        print("[PASS] 13. Interview Academy subject stats and patterns verified.")
 
        test_adaptive_quiz_selection()
        print("[PASS] 14. Quiz Intelligence adaptive selection verified.")
 
        test_orchestrator_loop_and_agent_state()
        print("[PASS] 15. Orchestrator loop and AgentState updates verified.")
        
        test_recommendation_history_filtering()
        print("[PASS] 16. Recommendation rejection filtering verified.")
        
        test_dummy_ai_providers_failure()
        print("[PASS] 17. Dummy AI Provider NotImplementedError assertions verified.")
 
        test_ai_provider_factory_and_gemini_fallback()
        print("[PASS] 18. AI provider factory and fallbacks verified.")
 
        test_application_package_workflow()
        print("[PASS] 19. ApplicationPackage workflow state transitions verified.")
 
        test_outcome_analyzer_metrics()
        print("[PASS] 20. OutcomeAnalyzer success predictors verified.")
 
        test_readiness_prediction_forecasting()
        print("[PASS] 21. Readiness prediction timelines verified.")
        
        test_cognitive_intelligence_layer()
        print("[PASS] 22. Phase 5.5 Career Cognitive Intelligence Layer verified.")
        
        print("\nSUCCESS: All integration tests executed and passed successfully!")
    except AssertionError as ae:
        print(f"\nFAILURE: Verification assertion failed: {ae}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as ex:
        print(f"\nERROR: Unexpected validation exception occurred: {ex}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
