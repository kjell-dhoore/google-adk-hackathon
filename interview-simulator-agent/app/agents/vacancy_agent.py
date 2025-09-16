# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
VacancyAgent: Extracts relevant information from job applications/descriptions.

This agent processes job vacancy texts to extract structured information
that can be used by downstream agents for interview question generation.
"""

import json
import os
from typing import Dict, List, Optional

import google.auth
import vertexai
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class VacancyInfo(BaseModel):
    """Structured information extracted from a job vacancy."""

    job_title: str = Field(description="The title of the position")
    company_name: Optional[str] = Field(description="Name of the hiring company")
    department: Optional[str] = Field(description="Department or team within the company")
    seniority_level: str = Field(
        description="Level of seniority: junior, mid, senior, lead, executive"
    )
    employment_type: str = Field(
        description="Type of employment: full-time, part-time, contract, internship, temporary"
    )
    location: Optional[str] = Field(description="Job location")
    remote_work: bool = Field(description="Whether remote work is available")

    # Key requirements
    required_skills: List[str] = Field(description="Must-have technical and soft skills")
    preferred_skills: List[str] = Field(description="Nice-to-have skills")
    education_requirements: List[str] = Field(description="Educational requirements")
    experience_years: Optional[int] = Field(description="Required years of experience")
    certifications: List[str] = Field(description="Required or preferred certifications")

    # Job details
    key_responsibilities: List[str] = Field(description="Main job responsibilities")
    team_size: Optional[int] = Field(description="Size of the team")
    reporting_to: Optional[str] = Field(description="Who the role reports to")
    technologies: List[str] = Field(description="Technologies, tools, and frameworks used")
    industry_sector: Optional[str] = Field(description="Industry or sector")

    # Additional context
    company_culture: List[str] = Field(description="Company culture values and traits")
    benefits: List[str] = Field(description="Benefits and perks offered")
    growth_opportunities: List[str] = Field(description="Career growth opportunities")
    challenges: List[str] = Field(description="Key challenges in the role")


class InterviewContext(BaseModel):
    """Interview context derived from vacancy information."""

    role_overview: dict = Field(description="High-level role information")
    technical_focus: dict = Field(description="Technical skills and requirements")
    experience_expectations: dict = Field(description="Experience and responsibility expectations")
    company_context: dict = Field(description="Company culture and industry context")
    logistics: dict = Field(description="Location, benefits, and employment details")


class SynchronousVacancyAgent:
    """Synchronous VacancyAgent for job posting analysis."""

    def __init__(self, use_vertexai: bool = True, model: str = "gemini-2.0-flash-exp"):
        """Initialize the agent."""
        self.use_vertexai = use_vertexai
        self.model = model

        # Initialize Gemini client
        if use_vertexai:
            credentials, project_id = google.auth.default()
            vertexai.init(project=project_id, location="us-central1")
            self.client = genai.Client(project=project_id, location="us-central1", vertexai=True)
        else:
            self.client = genai.Client(http_options={"api_version": "v1alpha"})

    def _create_extraction_prompt(self, job_description: str) -> str:
        """Create the extraction prompt."""
        return f"""
You are an expert HR analyst. Analyze this job posting and extract structured information in JSON format.

Job Description:
{job_description}

Return ONLY a valid JSON object with this exact structure:

{{
    "job_title": "string",
    "company_name": "string or null",
    "department": "string or null",
    "seniority_level": "junior|mid|senior|lead|executive",
    "employment_type": "full-time|part-time|contract|internship|temporary",
    "location": "string or null",
    "remote_work": true/false,
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1", "skill2"],
    "education_requirements": ["requirement1"],
    "experience_years": number_or_null,
    "certifications": ["cert1"],
    "key_responsibilities": ["responsibility1", "responsibility2"],
    "team_size": number_or_null,
    "reporting_to": "string or null",
    "technologies": ["tech1", "tech2"],
    "industry_sector": "string or null",
    "company_culture": ["value1", "value2"],
    "benefits": ["benefit1", "benefit2"],
    "growth_opportunities": ["opportunity1"],
    "challenges": ["challenge1"]
}}

Guidelines:
- Use null for missing information
- Extract only explicitly mentioned information
- Focus on interview-relevant details
- Be concise but comprehensive
"""

    def analyze_vacancy(self, job_description: str) -> Dict:
        """Analyze a job vacancy and return structured information."""
        try:
            prompt = self._create_extraction_prompt(job_description)

            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=[types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                )
            )

            # Extract and parse response
            response_text = response.candidates[0].content.parts[0].text

            # Clean up response (remove markdown formatting if present)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1]

            # Parse JSON
            vacancy_info = json.loads(response_text.strip())

            # Generate interview context
            interview_context = self._generate_interview_context(vacancy_info)

            return {
                "success": True,
                "vacancy_info": vacancy_info,
                "interview_context": interview_context,
                "summary": {
                    "title": vacancy_info.get("job_title"),
                    "company": vacancy_info.get("company_name"),
                    "seniority": vacancy_info.get("seniority_level"),
                    "key_skills": vacancy_info.get("required_skills", [])[:5],
                    "technologies": vacancy_info.get("technologies", [])[:5],
                }
            }

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON parsing error: {e}", "raw_response": response_text}
        except Exception as e:
            return {"success": False, "error": f"Analysis error: {e}"}

    def _generate_interview_context(self, vacancy_info: Dict) -> Dict:
        """Generate interview context from vacancy info."""
        return {
            "role_overview": {
                "title": vacancy_info.get("job_title"),
                "company": vacancy_info.get("company_name"),
                "seniority": vacancy_info.get("seniority_level"),
                "department": vacancy_info.get("department"),
            },
            "technical_focus": {
                "required_skills": vacancy_info.get("required_skills", []),
                "preferred_skills": vacancy_info.get("preferred_skills", []),
                "technologies": vacancy_info.get("technologies", []),
                "certifications": vacancy_info.get("certifications", []),
            },
            "experience_expectations": {
                "years_required": vacancy_info.get("experience_years"),
                "key_responsibilities": vacancy_info.get("key_responsibilities", []),
                "team_context": {
                    "team_size": vacancy_info.get("team_size"),
                    "reporting_to": vacancy_info.get("reporting_to"),
                },
            },
            "company_context": {
                "industry": vacancy_info.get("industry_sector"),
                "culture_values": vacancy_info.get("company_culture", []),
                "growth_opportunities": vacancy_info.get("growth_opportunities", []),
                "challenges": vacancy_info.get("challenges", []),
            },
            "logistics": {
                "location": vacancy_info.get("location"),
                "remote_work": vacancy_info.get("remote_work"),
                "employment_type": vacancy_info.get("employment_type"),
                "benefits": vacancy_info.get("benefits", []),
            },
        }


# Create default instance
vacancy_agent = SynchronousVacancyAgent()


def analyze_job_vacancy_sync(job_description: str) -> Dict:
    """Synchronous function to analyze job vacancies."""
    return vacancy_agent.analyze_vacancy(job_description)