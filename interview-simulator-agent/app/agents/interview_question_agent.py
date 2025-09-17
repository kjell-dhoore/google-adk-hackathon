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
InterviewQuestionAgent: Generates interview questions based on job vacancy information.

This agent takes structured vacancy information and generates relevant interview
questions that assess the candidate's fit for the role.
"""

import json
from typing import Dict, List

import google.auth
import vertexai
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    """A single interview question with context."""
    
    question: str = Field(description="The interview question text")
    question_type: str = Field(
        description="Type of question: technical, behavioral, situational, or general"
    )
    difficulty_level: str = Field(
        description="Difficulty: beginner, intermediate, or advanced"
    )
    skills_assessed: List[str] = Field(description="Skills this question evaluates")
    expected_answer_focus: str = Field(description="What the answer should focus on")
    follow_up_suggestions: List[str] = Field(description="Potential follow-up questions")


class InterviewQuestions(BaseModel):
    """Collection of interview questions for a role."""
    
    questions: List[InterviewQuestion] = Field(description="List of interview questions")
    interview_focus: Dict[str, str] = Field(description="Focus areas for the interview")
    evaluation_criteria: List[str] = Field(description="What to evaluate in responses")


class SynchronousInterviewQuestionAgent:
    """Synchronous InterviewQuestionAgent for generating interview questions."""

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

    def _create_question_generation_prompt(self, vacancy_info: Dict, interview_context: Dict) -> str:
        """Create the question generation prompt."""
        return f"""
You are an expert technical interviewer and HR professional. Generate exactly 3 high-quality interview questions for this job role.

Job Information:
- Title: {vacancy_info.get('job_title', 'N/A')}
- Company: {vacancy_info.get('company_name', 'N/A')}
- Seniority: {vacancy_info.get('seniority_level', 'N/A')}
- Required Skills: {', '.join(vacancy_info.get('required_skills', []))}
- Technologies: {', '.join(vacancy_info.get('technologies', []))}
- Key Responsibilities: {', '.join(vacancy_info.get('key_responsibilities', []))}
- Experience Required: {vacancy_info.get('experience_years', 'N/A')} years

Generate 3 diverse questions that cover:
1. One technical question (assessing core technical skills)
2. One behavioral/situational question (assessing soft skills and experience)
3. One role-specific question (assessing understanding of the position)

Return ONLY a valid JSON object with this exact structure:

{{
    "questions": [
        {{
            "question": "Question text here",
            "question_type": "technical|behavioral|situational|general",
            "difficulty_level": "beginner|intermediate|advanced",
            "skills_assessed": ["skill1", "skill2"],
            "expected_answer_focus": "What the answer should focus on",
            "follow_up_suggestions": ["follow-up 1", "follow-up 2"]
        }},
        {{
            "question": "Question text here",
            "question_type": "technical|behavioral|situational|general",
            "difficulty_level": "beginner|intermediate|advanced",
            "skills_assessed": ["skill1", "skill2"],
            "expected_answer_focus": "What the answer should focus on",
            "follow_up_suggestions": ["follow-up 1", "follow-up 2"]
        }},
        {{
            "question": "Question text here",
            "question_type": "technical|behavioral|situational|general",
            "difficulty_level": "beginner|intermediate|advanced",
            "skills_assessed": ["skill1", "skill2"],
            "expected_answer_focus": "What the answer should focus on",
            "follow_up_suggestions": ["follow-up 1", "follow-up 2"]
        }}
    ],
    "interview_focus": {{
        "technical_assessment": "Focus area for technical evaluation",
        "behavioral_assessment": "Focus area for behavioral evaluation",
        "role_fit": "Focus area for role-specific evaluation"
    }},
    "evaluation_criteria": [
        "Specific criteria 1",
        "Specific criteria 2",
        "Specific criteria 3"
    ]
}}

Guidelines:
- Make questions specific to the role and seniority level
- Ensure questions are practical and interview-appropriate
- Vary difficulty based on seniority level
- Focus on skills and technologies mentioned in the job description
- Make questions actionable and measurable
"""

    def generate_questions(self, vacancy_info: Dict, interview_context: Dict) -> Dict:
        """Generate interview questions based on vacancy information."""
        try:
            prompt = self._create_question_generation_prompt(vacancy_info, interview_context)

            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=[types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )],
                config=types.GenerateContentConfig(
                    temperature=0.3,
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
            questions_data = json.loads(response_text.strip())

            return {
                "success": True,
                "questions": questions_data.get("questions", []),
                "interview_focus": questions_data.get("interview_focus", {}),
                "evaluation_criteria": questions_data.get("evaluation_criteria", []),
                "summary": {
                    "total_questions": len(questions_data.get("questions", [])),
                    "question_types": [q.get("question_type") for q in questions_data.get("questions", [])],
                    "difficulty_levels": [q.get("difficulty_level") for q in questions_data.get("questions", [])],
                }
            }

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON parsing error: {e}", "raw_response": response_text}
        except Exception as e:
            return {"success": False, "error": f"Question generation error: {e}"}

    def generate_questions_from_vacancy_result(self, vacancy_result: Dict) -> Dict:
        """Generate questions directly from vacancy agent result."""
        if not vacancy_result.get("success"):
            return {"success": False, "error": "Invalid vacancy analysis result"}
        
        vacancy_info = vacancy_result.get("vacancy_info", {})
        interview_context = vacancy_result.get("interview_context", {})
        
        return self.generate_questions(vacancy_info, interview_context)


# Create default instance
interview_question_agent = SynchronousInterviewQuestionAgent()


def generate_interview_questions_sync(vacancy_info: Dict, interview_context: Dict) -> Dict:
    """Synchronous function to generate interview questions."""
    return interview_question_agent.generate_questions(vacancy_info, interview_context)
