# MCP Server for CareerPilot
# Provides tools for job analysis and resume matching

import json
import re
from typing import Any, Dict, List


def extract_job_requirements(job_description: str) -> Dict[str, Any]:
    """Extract key requirements from job description"""
    skills_pattern = r'(?:required|preferred|minimum|must have)[:\s]+([^\n]+)'
    skills = re.findall(skills_pattern, job_description, re.IGNORECASE)

    action_verbs = ['manage', 'develop', 'implement', 'design', 'lead', 'analyze', 'create', 'coordinate']
    responsibilities = []
    for verb in action_verbs:
        matches = re.findall(f'{verb}[ing]?\\s+[^,\\n]+', job_description, re.IGNORECASE)
        responsibilities.extend(matches[:2])

    keywords = list(set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', job_description)))
    important_words = [k for k in keywords if len(k) > 4][:15]

    required_skills = []
    if 'python' in job_description.lower():
        required_skills.append('Python')
    if 'javascript' in job_description.lower() or 'js' in job_description.lower():
        required_skills.append('JavaScript')
    if 'sql' in job_description.lower():
        required_skills.append('SQL')
    if 'cloud' in job_description.lower() or 'aws' in job_description.lower():
        required_skills.append('Cloud Services')

    return {
        "required_skills": required_skills,
        "preferred_qualifications": skills[:5],
        "key_responsibilities": responsibilities[:5],
        "keywords": important_words
    }


def score_resume_against_job(resume_text: str, job_requirements: Dict) -> Dict[str, Any]:
    """Score how well resume matches job requirements"""
    resume_lower = resume_text.lower()
    required = job_requirements.get('required_skills', [])
    matched = [s for s in required if s.lower() in resume_lower]
    missing = [s for s in required if s.lower() not in resume_lower]
    score = int((len(matched) / max(len(required), 1)) * 100)

    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "suggestions": [f"Consider adding: {s}" for s in missing[:3]]
    }


def find_keyword_gaps(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Find missing keywords from job description"""
    job_words = set(re.findall(r'\b[a-z]{4,}\b', job_description.lower()))
    resume_words = set(re.findall(r'\b[a-z]{4,}\b', resume_text.lower()))
    missing = list(job_words - resume_words)[:10]

    suggestions = []
    important = ['experience', 'team', 'lead', 'manage', 'project', 'develop']
    for word in important:
        if word in job_words and word not in resume_words:
            suggestions.append(f"Add '{word}' if applicable")

    return {"missing_keywords": missing, "suggestions": suggestions}


def generate_cover_letter_outline(candidate_name: str, job_title: str, company_name: str, key_points: List[str] = None) -> Dict:
    """Generate cover letter outline"""
    key_points = key_points or []
    return {
        "outline": {
            "opening": f"Dear Hiring Manager,\n\nI am excited to apply for the {job_title} position at {company_name}.",
            "body_points": [
                f"Highlight my relevant experience in {key_points[0] if key_points else 'the field'}",
                "Demonstrate understanding of company needs",
                "Showcase specific achievements and qualifications"
            ],
            "closing": f"\nThank you for considering my application. I look forward to discussing how I can contribute to {company_name}.\n\nBest regards,\n{candidate_name}"
        }
    }


if __name__ == "__main__":
    import sys
    sys.stdout.write("CareerPilot MCP Server running...")