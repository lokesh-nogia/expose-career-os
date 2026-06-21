import os
import json
import urllib.request
import urllib.error
from typing import Optional

class AIProvider:
    """
    Abstract interface defining LLM capabilities for resume parsing,
    job description analysis, cover letter generation, and interview feedback.
    """
    def analyze_resume(self, resume_text: str, target_role: str) -> dict:
        raise NotImplementedError("Resume analysis is not implemented.")

    def analyze_job_description(self, job_description: str) -> dict:
        raise NotImplementedError("Job Description analysis is not implemented.")

    def generate_cover_letter(self, resume_text: str, job_description: str, company_info: str) -> dict:
        raise NotImplementedError("Cover Letter generation is not implemented.")

    def interview_feedback(self, question: str, response: str) -> dict:
        raise NotImplementedError("Interview Feedback is not implemented.")

    def skill_gap_analysis(self, user_skills: list, job_skills: list) -> dict:
        raise NotImplementedError("Skill Gap Analysis is not implemented.")

    def forecast_outcomes(self, profile: dict, history: list) -> dict:
        raise NotImplementedError("Outcome forecasting is not implemented.")

    def analyze_strategy(self, profile: dict, market_trends: dict) -> dict:
        raise NotImplementedError("Strategy analysis is not implemented.")

    def recommend_priorities(self, profile: dict, choices: list) -> dict:
        raise NotImplementedError("Priority recommendation is not implemented.")

    def simulate_career_paths(self, profile: dict, paths: list) -> dict:
        raise NotImplementedError("Career path simulation is not implemented.")


class GeminiProvider(AIProvider):
    """Google Gemini Pro / Flash API provider with zero external package dependencies."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def _call_gemini(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")
        
        # Using gemini-1.5-flash for cost-effective, high-speed processing
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                text = res_json["contents"][0]["parts"][0]["text"]
                return text
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")

    def _clean_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)

    def analyze_resume(self, resume_text: str, target_role: str) -> dict:
        prompt = (
            f"Analyze this resume against the target role '{target_role}'. Critique formatting, "
            f"experience bullets, and suggest improvements. Do not fabricate experience.\n\n"
            f"Resume Text:\n{resume_text}\n\n"
            f"Return ONLY a JSON object with keys:\n"
            f"- 'critique': list of suggestions/critiques\n"
            f"- 'bullet_suggestions': list of dicts with keys 'original' and 'suggested' rephrasings\n"
            f"- 'overall_score': integer from 0 to 100 representing resume strength."
        )
        res = self._call_gemini(prompt)
        return self._clean_json(res)

    def analyze_job_description(self, job_description: str) -> dict:
        prompt = (
            f"Analyze this job description. Extract skills and salary estimates if available.\n\n"
            f"Job Description:\n{job_description}\n\n"
            f"Return ONLY a JSON object with keys:\n"
            f"- 'skills': list of required/demanded skill names\n"
            f"- 'seniority': estimated seniority string (e.g. Junior, Mid, Senior, Lead)\n"
            f"- 'salary_estimate': float estimated salary in LPA (or 0.0 if not extractable)."
        )
        res = self._call_gemini(prompt)
        return self._clean_json(res)

    def generate_cover_letter(self, resume_text: str, job_description: str, company_info: str) -> dict:
        prompt = (
            f"Generate a professional cover letter. Acknowledge skill gaps if any, highlight strengths, "
            f"and tailor it to the role and company.\n\n"
            f"Resume Text:\n{resume_text}\n\n"
            f"Job Description:\n{job_description}\n\n"
            f"Company Info:\n{company_info}\n\n"
            f"Return ONLY a JSON object with keys:\n"
            f"- 'letter': full text of the cover letter\n"
            f"- 'confidence_score': integer from 0 to 100 matching profile compatibility."
        )
        res = self._call_gemini(prompt)
        return self._clean_json(res)

    def interview_feedback(self, question: str, response: str) -> dict:
        prompt = (
            f"Evaluate this interview response to the question '{question}'.\n\n"
            f"User Response:\n{response}\n\n"
            f"Return ONLY a JSON object with keys:\n"
            f"- 'score': integer from 1 to 10\n"
            f"- 'critique': concise feedback text\n"
            f"- 'improved_version': optimized rephrasing of the answer using STAR method."
        )
        res = self._call_gemini(prompt)
        return self._clean_json(res)

    def skill_gap_analysis(self, user_skills: list, job_skills: list) -> dict:
        prompt = (
            f"Compare user skills {user_skills} with job skills {job_skills}.\n\n"
            f"Return ONLY a JSON object with keys:\n"
            f"- 'matched': list of overlapping skills\n"
            f"- 'missing': list of missing skills demanded by the job\n"
            f"- 'recommendations': list of action recommendations to close the gap."
        )
        res = self._call_gemini(prompt)
        return self._clean_json(res)


class ClaudeProvider(AIProvider):
    """Placeholder provider for Anthropic Claude API integration."""
    pass


class OpenAIProvider(AIProvider):
    """Placeholder provider for OpenAI GPT API integration."""
    pass


class AIProviderFactory:
    """Factory to fetch active AI provider if available, or fall back to deterministic logic."""
    @staticmethod
    def get_provider() -> Optional[AIProvider]:
        if os.environ.get("GEMINI_API_KEY"):
            return GeminiProvider()
        return None
