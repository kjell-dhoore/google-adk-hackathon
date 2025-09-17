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

import os

import google.auth
import vertexai
from google import genai
from google.genai import types

# Constants
VERTEXAI = os.getenv("VERTEXAI", "true").lower() == "true"
LOCATION = "us-central1"
MODEL_ID = "gemini-live-2.5-flash-preview-native-audio"

# Initialize Google Cloud clients
credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=LOCATION)


if VERTEXAI:
    genai_client = genai.Client(project=project_id, location=LOCATION, vertexai=True)
else:
    # API key should be set using GOOGLE_API_KEY environment variable
    genai_client = genai.Client(http_options={"api_version": "v1alpha"})

def analyze_job_vacancy(job_description: str) -> dict:
    """Analyzes a job vacancy description and extracts structured information.

    Args:
        job_description: The job posting or vacancy description text to analyze.

    Returns:
        A dictionary containing structured information about the job including:
        - Basic job details (title, company, location, etc.)
        - Required and preferred skills
        - Key responsibilities
        - Interview context for question generation
    """
    try:
        from .agents.vacancy_agent import analyze_job_vacancy_sync

        # Use the synchronous VacancyAgent
        result = analyze_job_vacancy_sync(job_description)

        if result.get("success"):
            vacancy_info = result.get("vacancy_info", {})
            job_title = vacancy_info.get('job_title', 'Unknown Position')
            return {
                "output": f"Successfully analyzed job posting for: {job_title}",
                "vacancy_info": vacancy_info,
                "interview_context": result.get("interview_context", {}),
                "summary": result.get("summary", {})
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            return {
                "output": f"Error analyzing job vacancy: {error_msg}",
                "error": error_msg
            }

    except Exception as e:
        return {
            "output": f"Error analyzing job vacancy: {str(e)}",
            "error": str(e)
        }


def generate_interview_questions(
    vacancy_info: dict, interview_context: dict
) -> dict:
    """Generates interview questions based on analyzed job vacancy information.

    Args:
        vacancy_info: Structured job information from vacancy analysis
        interview_context: Interview context derived from vacancy information

    Returns:
        A dictionary containing generated interview questions and evaluation
        criteria
    """
    try:
        from .agents.interview_question_agent import generate_interview_questions_sync

        # Use the synchronous InterviewQuestionAgent
        result = generate_interview_questions_sync(vacancy_info, interview_context)

        if result.get("success"):
            questions = result.get("questions", [])
            return {
                "output": f"Successfully generated {len(questions)} interview "
                f"questions for the position",
                "questions": questions,
                "interview_focus": result.get("interview_focus", {}),
                "evaluation_criteria": result.get("evaluation_criteria", []),
                "summary": result.get("summary", {})
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            return {
                "output": f"Error generating interview questions: {error_msg}",
                "error": error_msg
            }

    except Exception as e:
        return {
            "output": f"Error generating interview questions: {str(e)}",
            "error": str(e)
        }


def analyze_job_and_generate_questions(job_description: str) -> dict:
    """Analyzes a job vacancy and generates interview questions in one step.

    Args:
        job_description: The job posting or vacancy description text to analyze.

    Returns:
        A dictionary containing both job analysis and interview questions.
    """
    try:
        from .agents.vacancy_agent import analyze_job_vacancy_sync
        from .agents.interview_question_agent import generate_interview_questions_sync

        # Step 1: Analyze the job vacancy
        vacancy_result = analyze_job_vacancy_sync(job_description)
        
        if not vacancy_result.get("success"):
            return {
                "output": f"Error analyzing job vacancy: {vacancy_result.get('error', 'Unknown error')}",
                "error": vacancy_result.get('error', 'Unknown error')
            }

        vacancy_info = vacancy_result.get("vacancy_info", {})
        interview_context = vacancy_result.get("interview_context", {})
        job_title = vacancy_info.get('job_title', 'Unknown Position')

        # Step 2: Generate interview questions
        questions_result = generate_interview_questions_sync(vacancy_info, interview_context)
        
        if not questions_result.get("success"):
            return {
                "output": f"Job analysis successful for {job_title}, but error generating questions: {questions_result.get('error', 'Unknown error')}",
                "vacancy_info": vacancy_info,
                "interview_context": interview_context,
                "error": questions_result.get('error', 'Unknown error')
            }

        questions = questions_result.get("questions", [])
        
        return {
            "output": f"Successfully analyzed {job_title} and generated {len(questions)} interview questions",
            "vacancy_info": vacancy_info,
            "interview_context": interview_context,
            "questions": questions,
            "interview_focus": questions_result.get("interview_focus", {}),
            "evaluation_criteria": questions_result.get("evaluation_criteria", []),
            "summary": {
                "job_title": job_title,
                "company": vacancy_info.get("company_name"),
                "seniority": vacancy_info.get("seniority_level"),
                "total_questions": len(questions),
                "question_types": [q.get("question_type") for q in questions]
            }
        }

    except Exception as e:
        return {
            "output": f"Error in combined analysis: {str(e)}",
            "error": str(e)
        }


# Configure tools available to the agent and live connection
tool_functions = {
    "analyze_job_vacancy": analyze_job_vacancy,
    "generate_interview_questions": generate_interview_questions,
    "analyze_job_and_generate_questions": analyze_job_and_generate_questions
}

live_connect_config = types.LiveConnectConfig(
    response_modalities=[types.Modality.AUDIO],
    tools=list(tool_functions.values()),
    system_instruction=types.Content(
        parts=[
            types.Part(
                text="""You are an Interview Simulator Agent, designed to help users 
practice job interviews and improve their interview skills.

CONVERSATION FLOW:
1. INTRODUCTION: When the conversation starts, introduce yourself and 
   explain your purpose:
   "Hello! I'm your Interview Simulator Agent. I'm here to help you 
   practice for job interviews. To get started, please provide me with 
   the job description or posting you'd like to interview for. You can 
   paste it in the text box below or tell me about the role."

2. JOB ANALYSIS AND QUESTION GENERATION: When a user provides a job 
   description (either via voice or text):
   - In ONE CONTINUOUS TURN, do the following WITHOUT ending the turn:
     a) Say: "Thank you! Let me analyze this job posting to understand the 
        role requirements and generate interview questions."
     b) IMMEDIATELY call the analyze_job_and_generate_questions tool with 
        the job description (do NOT wait for user input or end the turn)
     c) After the tool completes, provide a comprehensive summary: "Analysis 
        complete! I've successfully analyzed the position for [job title] at 
        [company]. This is a [seniority level] role requiring expertise in 
        [key skills]. I've also generated 3 tailored interview questions for 
        you."
     d) Present the questions clearly: "Here are your 3 interview questions: 
        [present each question with its type, difficulty, and what it assesses]"
     e) Explain the evaluation criteria and what to focus on in answers
     f) Offer to help with practice or clarification
   - CRITICAL: Do NOT call server.send.TurnComplete until ALL steps above 
     are finished in the same turn

Key Capabilities:
- Job Analysis: Extract structured information from job postings including 
  skills, responsibilities, company culture, and requirements
- Interview Question Generation: Create tailored questions (technical, 
  behavioral, role-specific) based on job analysis
- Professional Communication: Maintain a helpful, encouraging, and 
  professional tone
- Clear Process Flow: Guide users through each step of the preparation 
  process

IMPORTANT: Use the analyze_job_and_generate_questions tool when analyzing a job posting.
This tool automatically performs both job analysis and question generation in one step.

Always be encouraging and professional. When presenting questions, explain 
what each question assesses and provide guidance on how to approach the 
answers."""
            )
        ]
    ),
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
    enable_affective_dialog=True,
)
