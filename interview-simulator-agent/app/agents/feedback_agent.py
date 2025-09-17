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
FeedbackAgent: Provides constructive feedback on interview answers.

This agent analyzes candidate responses to interview questions and provides
helpful feedback on how to improve their answers.
"""

import json
from typing import Dict, List, Any

import google.auth
import vertexai
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class AnswerFeedback(BaseModel):
    """Feedback for a single interview answer."""
    
    question_id: str = Field(description="ID of the question being evaluated")
    question_text: str = Field(description="The original question text")
    answer_text: str = Field(description="The candidate's answer")
    
    # Feedback components
    strengths: List[str] = Field(description="What the candidate did well")
    areas_for_improvement: List[str] = Field(description="Areas that need improvement")
    specific_suggestions: List[str] = Field(description="Specific actionable suggestions")
    overall_score: int = Field(description="Overall score from 1-10")
    score_breakdown: Dict[str, int] = Field(description="Breakdown of scores by criteria")
    
    # Additional context
    question_type: str = Field(description="Type of question (technical, behavioral, etc.)")
    difficulty_level: str = Field(description="Difficulty level of the question")
    skills_assessed: List[str] = Field(description="Skills this question was meant to assess")


class InterviewFeedback(BaseModel):
    """Complete feedback for an interview session."""
    
    session_id: str = Field(description="Interview session ID")
    candidate_name: str = Field(description="Name of the candidate")
    position: str = Field(description="Position being interviewed for")
    
    # Overall assessment
    overall_performance: Dict[str, Any] = Field(description="Overall performance summary")
    total_score: float = Field(description="Average score across all questions")
    key_strengths: List[str] = Field(description="Overall strengths demonstrated")
    main_improvement_areas: List[str] = Field(description="Main areas for improvement")
    
    # Individual feedback
    question_feedback: List[AnswerFeedback] = Field(description="Feedback for each question")
    
    # Recommendations
    next_steps: List[str] = Field(description="Recommended next steps for improvement")
    resources: List[str] = Field(description="Suggested resources for improvement")


class SynchronousFeedbackAgent:
    """Synchronous FeedbackAgent for providing interview feedback."""
    
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
    
    def _create_feedback_prompt(self, questions: List[Dict], answers: List[Dict], 
                              vacancy_info: Dict, evaluation_criteria: List[str]) -> str:
        """Create the feedback generation prompt."""
        
        # Format questions and answers - handle different answer structures
        qa_pairs = []
        for i, question in enumerate(questions):
            if i < len(answers):
                answer = answers[i]
                # Handle different answer formats
                if isinstance(answer, dict):
                    answer_text = answer.get("answer_text", answer.get("text", "No answer provided"))
                else:
                    answer_text = str(answer)
            else:
                answer_text = "No answer provided"
            
            qa_pairs.append({
                "question": question,
                "answer": {"answer_text": answer_text}
            })
        
        return f"""
You are an expert interview coach and HR professional. Provide constructive, actionable feedback on this interview performance.

JOB CONTEXT:
- Position: {vacancy_info.get('job_title', 'N/A')}
- Company: {vacancy_info.get('company_name', 'N/A')}
- Seniority Level: {vacancy_info.get('seniority_level', 'N/A')}
- Required Skills: {', '.join(vacancy_info.get('required_skills', []))}

EVALUATION CRITERIA:
{chr(10).join(f"- {criteria}" for criteria in evaluation_criteria)}

INTERVIEW QUESTIONS AND ANSWERS:
{json.dumps(qa_pairs, indent=2)}

Provide comprehensive feedback following this structure:

Return ONLY a valid JSON object with this exact structure:

{{
    "overall_performance": {{
        "total_score": 7.5,
        "summary": "Overall performance summary",
        "key_strengths": ["strength1", "strength2"],
        "main_improvement_areas": ["area1", "area2"]
    }},
    "question_feedback": [
        {{
            "question_id": "q1",
            "question_text": "Original question text",
            "answer_text": "Candidate's answer",
            "strengths": ["What they did well"],
            "areas_for_improvement": ["Areas to improve"],
            "specific_suggestions": ["Actionable suggestions"],
            "overall_score": 8,
            "score_breakdown": {{
                "clarity": 8,
                "relevance": 7,
                "depth": 9,
                "examples": 6
            }},
            "question_type": "technical",
            "difficulty_level": "intermediate",
            "skills_assessed": ["skill1", "skill2"]
        }}
    ],
    "next_steps": [
        "Specific actionable next step 1",
        "Specific actionable next step 2"
    ],
    "resources": [
        "Suggested resource 1",
        "Suggested resource 2"
    ]
}}

Guidelines:
- Be constructive and encouraging while being honest about areas for improvement
- Provide specific, actionable suggestions
- Score fairly based on the candidate's level and question difficulty
- Focus on interview-relevant feedback that will help them improve
- Consider the job requirements and seniority level in your assessment
- Make feedback practical and implementable
"""

    def provide_feedback(self, questions: List[Dict], answers: List[Dict], 
                        vacancy_info: Dict, evaluation_criteria: List[str],
                        session_id: str = "default", candidate_name: str = "Candidate") -> Dict:
        """Provide comprehensive feedback on interview performance."""
        try:
            # Validate input data
            if not questions:
                return {"success": False, "error": "No questions provided for feedback"}
            
            if not answers:
                return {"success": False, "error": "No answers provided for feedback"}
            
            if not vacancy_info:
                return {"success": False, "error": "No vacancy information provided"}
            
            # Log data for debugging
            print(f"DEBUG: Processing feedback for session {session_id}")
            print(f"DEBUG: Questions count: {len(questions)}")
            print(f"DEBUG: Answers count: {len(answers)}")
            print(f"DEBUG: Vacancy: {vacancy_info.get('job_title', 'N/A')}")
            print(f"DEBUG: Evaluation criteria count: {len(evaluation_criteria)}")
            
            prompt = self._create_feedback_prompt(questions, answers, vacancy_info, evaluation_criteria)
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=[types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
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
            feedback_data = json.loads(response_text.strip())
            
            # Add session metadata
            feedback_data["session_id"] = session_id
            feedback_data["candidate_name"] = candidate_name
            feedback_data["position"] = vacancy_info.get("job_title", "Unknown Position")
            
            # Format feedback for voice output
            voice_feedback = self._format_feedback_for_voice(feedback_data)
            
            return {
                "success": True,
                "feedback": feedback_data,
                "voice_feedback": voice_feedback,
                "summary": {
                    "total_questions": len(questions),
                    "total_answers": len(answers),
                    "overall_score": feedback_data.get("overall_performance", {}).get("total_score", 0),
                    "key_strengths_count": len(feedback_data.get("overall_performance", {}).get("key_strengths", [])),
                    "improvement_areas_count": len(feedback_data.get("overall_performance", {}).get("main_improvement_areas", []))
                }
            }
            
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON parsing error: {e}", "raw_response": response_text}
        except Exception as e:
            return {"success": False, "error": f"Feedback generation error: {e}"}
    
    def _format_feedback_for_voice(self, feedback_data: Dict) -> str:
        """Format feedback data for voice output to the candidate."""
        try:
            overall = feedback_data.get("overall_performance", {})
            question_feedback = feedback_data.get("question_feedback", [])
            next_steps = feedback_data.get("next_steps", [])
            
            # Create voice-friendly feedback
            voice_text = f"""
Great job completing the interview! Let me share your feedback with you.

Overall Performance:
You scored {overall.get('total_score', 'N/A')} out of 10 overall. {overall.get('summary', 'Good work!')}

Your Key Strengths:
{chr(10).join(f"• {strength}" for strength in overall.get('key_strengths', []))}

Areas for Improvement:
{chr(10).join(f"• {area}" for area in overall.get('main_improvement_areas', []))}

Question-by-Question Feedback:
"""
            
            for i, q_feedback in enumerate(question_feedback, 1):
                voice_text += f"""
Question {i} - {q_feedback.get('question_type', 'General')} Question:
You scored {q_feedback.get('overall_score', 'N/A')} out of 10.

What you did well:
{chr(10).join(f"• {strength}" for strength in q_feedback.get('strengths', []))}

Areas to improve:
{chr(10).join(f"• {area}" for area in q_feedback.get('areas_for_improvement', []))}

Specific suggestions:
{chr(10).join(f"• {suggestion}" for suggestion in q_feedback.get('specific_suggestions', []))}
"""
            
            if next_steps:
                voice_text += f"""
Next Steps for Improvement:
{chr(10).join(f"• {step}" for step in next_steps)}
"""
            
            voice_text += """
Remember, practice makes perfect! Keep working on these areas and you'll continue to improve your interview skills.

Would you like to practice again with a different job description, or do you have any questions about this feedback?
"""
            
            return voice_text.strip()
            
        except Exception as e:
            return f"Feedback generated successfully, but there was an issue formatting it for voice output: {str(e)}"


# Create default instance
feedback_agent = SynchronousFeedbackAgent()


def provide_feedback_sync(questions: List[Dict], answers: List[Dict], 
                         vacancy_info: Dict, evaluation_criteria: List[str],
                         session_id: str = "default", candidate_name: str = "Candidate") -> Dict:
    """Synchronous function to provide interview feedback."""
    return feedback_agent.provide_feedback(questions, answers, vacancy_info, evaluation_criteria, session_id, candidate_name)
