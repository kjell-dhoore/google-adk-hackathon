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

from .agents.vacancy_agent import analyze_job_vacancy_sync
from .agents.interview_question_agent import generate_interview_questions_sync
from .agents.interview_agent import ask_next_interview_question_sync, record_interview_answer_sync
from .agents.feedback_agent import provide_feedback_sync

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

def analyze_job_and_generate_questions(job_description: str) -> dict:
    """Analyzes a job vacancy and generates interview questions in one step.

    Args:
        job_description: The job posting or vacancy description text to analyze.

    Returns:
        A dictionary containing both job analysis and interview questions.
    """
    try:
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

        # Store session data for the interview flow
        session_id = "default"  # In production, this would be generated uniquely
        interview_sessions[session_id] = {
            "vacancy_info": vacancy_info,
            "interview_context": interview_context,
            "questions": questions,
            "interview_focus": questions_result.get("interview_focus", {}),
            "evaluation_criteria": questions_result.get("evaluation_criteria", []),
            "current_question_index": 0,
            "answers": [],
            "status": "ready",
            "candidate_name": "Candidate"  # In production, this would be collected from user
        }

        return {
            "output": f"Successfully analyzed {job_title} and generated {len(questions)} interview questions",
            "vacancy_info": vacancy_info,
            "interview_context": interview_context,
            "questions": questions,
            "interview_focus": questions_result.get("interview_focus", {}),
            "evaluation_criteria": questions_result.get("evaluation_criteria", []),
            "session_id": session_id,
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

# Global session storage (in production, this would be a proper database)
interview_sessions = {}

def ask_next_interview_question(session_id: str = "default") -> dict:
    """Get the next question in the interview sequence.
    
    Args:
        session_id: ID of the interview session
        
    Returns:
        Dictionary with the next question or completion status
    """
    try:
        if session_id not in interview_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found. Please start with job analysis first."
            }
        
        session = interview_sessions[session_id]
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        if current_index >= len(questions):
            return {
                "success": True,
                "status": "completed",
                "message": "Interview completed - no more questions",
                "session_summary": {
                    "total_questions": len(questions),
                    "total_answers": len(session.get("answers", [])),
                    "position": session.get("vacancy_info", {}).get("job_title", "Unknown")
                }
            }
        
        current_question = questions[current_index]
        
        return {
            "success": True,
            "status": "success",
            "question": {
                "id": f"q{current_index + 1}",
                "text": current_question.get("question", ""),
                "type": current_question.get("question_type", "general"),
                "difficulty": current_question.get("difficulty_level", "medium"),
                "skills_assessed": current_question.get("skills_assessed", []),
                "question_number": current_index + 1,
                "total_questions": len(questions)
            },
            "session_info": {
                "session_id": session_id,
                "position": session.get("vacancy_info", {}).get("job_title", "Unknown Position"),
                "current_question": current_index + 1,
                "total_questions": len(questions)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get next question: {str(e)}"
        }

def record_interview_answer(session_id: str, question_id: str, answer_text: str, notes: str = "") -> dict:
    """Record a candidate's answer to an interview question.
    
    Args:
        session_id: ID of the interview session
        question_id: ID of the question being answered
        answer_text: The candidate's answer
        notes: Optional notes about the answer
        
    Returns:
        Dictionary with recording status
    """
    try:
        if session_id not in interview_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = interview_sessions[session_id]
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        if current_index >= len(questions):
            return {
                "success": False,
                "error": "No more questions to answer"
            }
        
        # Record the answer
        if "answers" not in session:
            session["answers"] = []
        
        answer_record = {
            "question_id": question_id,
            "question_text": questions[current_index].get("question", ""),
            "answer_text": answer_text,
            "notes": notes,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "question_type": questions[current_index].get("question_type", "general"),
            "difficulty_level": questions[current_index].get("difficulty_level", "medium"),
            "skills_assessed": questions[current_index].get("skills_assessed", [])
        }
        
        session["answers"].append(answer_record)
        session["current_question_index"] = current_index + 1
        
        # Check if interview is complete
        if session["current_question_index"] >= len(questions):
            session["status"] = "completed"
            return {
                "success": True,
                "status": "completed",
                "message": "Interview completed successfully",
                "session_summary": {
                    "total_questions": len(questions),
                    "total_answers": len(session["answers"]),
                    "position": session.get("vacancy_info", {}).get("job_title", "Unknown")
                }
            }
        
        return {
            "success": True,
            "status": "success",
            "message": "Answer recorded successfully",
            "next_question": ask_next_interview_question(session_id)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to record answer: {str(e)}"
        }

def provide_feedback(session_id: str = "default") -> dict:
    """Provide comprehensive feedback on the completed interview.
    
    Args:
        session_id: ID of the interview session
        
    Returns:
        Dictionary with feedback results
    """
    try:
        if session_id not in interview_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = interview_sessions[session_id]
        
        if session.get("status") != "completed":
            return {
                "success": False,
                "error": "Interview not completed yet. Please finish all questions first."
            }
        
        questions = session.get("questions", [])
        answers = session.get("answers", [])
        vacancy_info = session.get("vacancy_info", {})
        evaluation_criteria = session.get("evaluation_criteria", [])
        
        if not questions or not answers:
            return {
                "success": False,
                "error": "No questions or answers found in session"
            }
        
        # Call the feedback agent
        feedback_result = provide_feedback_sync(
            questions=questions,
            answers=answers,
            vacancy_info=vacancy_info,
            evaluation_criteria=evaluation_criteria,
            session_id=session_id,
            candidate_name=session.get("candidate_name", "Candidate")
        )
        
        if feedback_result.get("success"):
            # Store feedback in session
            session["feedback"] = feedback_result.get("feedback", {})
            session["voice_feedback"] = feedback_result.get("voice_feedback", "")
            session["feedback_status"] = "completed"
            
            return {
                "success": True,
                "feedback": feedback_result.get("feedback", {}),
                "voice_feedback": feedback_result.get("voice_feedback", ""),
                "summary": feedback_result.get("summary", {}),
                "message": "Feedback generated successfully"
            }
        else:
            return {
                "success": False,
                "error": feedback_result.get("error", "Failed to generate feedback")
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to provide feedback: {str(e)}"
        }

# Configure tools available to the agent and live connection
tool_functions = {
    "analyze_job_and_generate_questions": analyze_job_and_generate_questions,
    "ask_next_interview_question": ask_next_interview_question,
    "record_interview_answer": record_interview_answer,
    "provide_feedback": provide_feedback,
}

live_connect_config = types.LiveConnectConfig(
    response_modalities=[types.Modality.AUDIO],
    tools=list(tool_functions.values()),
    system_instruction=types.Content(
        parts=[
            types.Part(
                text="""You are an Interview Simulator Agent, designed to help users 
practice job interviews and improve their interview skills through a complete 
interview simulation process.

COMPLETE INTERVIEW FLOW:
1. INTRODUCTION: When the conversation starts, introduce yourself and 
   explain your purpose:
   "Hello! I'm your Interview Simulator Agent. I'm here to help you 
   practice for job interviews through a complete simulation. To get started, 
   please provide me with the job description or posting you'd like to 
   interview for. You can paste it in the text box below or tell me about the role."

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
     f) Say: "Now let's begin the interview! I'll ask you each question one 
        by one, and you can provide your answers. Are you ready to start?"
   - CRITICAL: Do NOT call server.send.TurnComplete until ALL steps above 
     are finished in the same turn

3. CONDUCTING THE INTERVIEW: Once questions are generated:
   - Ask the first question using ask_next_interview_question tool
   - Wait for the candidate's answer
   - Record their answer using record_interview_answer tool
   - Move to the next question
   - Repeat until all questions are answered
   - When interview is complete, say: "Great! You've completed all the 
     interview questions. Now let me analyze your answers and provide you 
     with detailed feedback."

4. PROVIDING FEEDBACK: After all questions are answered:
   - Call the provide_feedback tool to generate comprehensive feedback
   - Present the feedback in a structured, encouraging way:
     * Overall performance summary
     * Strengths demonstrated
     * Areas for improvement
     * Specific suggestions for each question
     * Next steps and resources
   - End with encouragement and offer to practice again

Key Capabilities:
- Job Analysis: Extract structured information from job postings including 
  skills, responsibilities, company culture, and requirements
- Interview Question Generation: Create tailored questions (technical, 
  behavioral, role-specific) based on job analysis
- Interview Conduct: Ask questions sequentially and record answers
- Comprehensive Feedback: Provide detailed, actionable feedback on performance
- Professional Communication: Maintain a helpful, encouraging, and 
  professional tone throughout

IMPORTANT TOOLS USAGE:
- analyze_job_and_generate_questions: Use when user provides job description
- ask_next_interview_question: Use to get the next question in sequence
- record_interview_answer: Use to record candidate's answer to each question
- provide_feedback: Use after all questions are completed

Always be encouraging and professional. Guide the user through each step 
of the complete interview process, from job analysis to final feedback."""
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
