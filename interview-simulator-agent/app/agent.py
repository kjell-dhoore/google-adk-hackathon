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


def get_weather(query: str) -> dict:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return {"output": "It's 60 degrees and foggy."}
    return {"output": "It's 90 degrees and sunny."}


def analyze_job_vacancy(job_description: str) -> dict:
    """Analyzes a job vacancy description and extracts structured information for interview preparation.

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
            return {
                "output": f"Successfully analyzed job posting for: {vacancy_info.get('job_title', 'Unknown Position')}",
                "vacancy_info": vacancy_info,
                "interview_context": result.get("interview_context", {}),
                "summary": result.get("summary", {})
            }
        else:
            return {
                "output": f"Error analyzing job vacancy: {result.get('error', 'Unknown error')}",
                "error": result.get('error', 'Unknown error')
            }

    except Exception as e:
        return {
            "output": f"Error analyzing job vacancy: {str(e)}",
            "error": str(e)
        }


# Configure tools available to the agent and live connection
tool_functions = {
    "get_weather": get_weather,
    "analyze_job_vacancy": analyze_job_vacancy
}

live_connect_config = types.LiveConnectConfig(
    response_modalities=[types.Modality.AUDIO],
    tools=list(tool_functions.values()),
    system_instruction=types.Content(
        parts=[
            types.Part(
                text="""You are an Interview Simulator Agent, designed to help users practice job interviews and improve their interview skills.

CONVERSATION FLOW:
1. INTRODUCTION: When the conversation starts, introduce yourself and explain your purpose:
   "Hello! I'm your Interview Simulator Agent. I'm here to help you practice for job interviews. To get started, please provide me with the job description or posting you'd like to interview for. You can paste it in the text box below or tell me about the role."

2. JOB ANALYSIS: When a user provides a job description (either via voice or text):
   - Say: "Thank you! Let me analyze this job posting to understand the role requirements. This analysis might take a moment as I need to process all the details..."
   - Use the analyze_job_vacancy tool to extract structured information
   - After analysis, provide a comprehensive summary: "Analysis complete! I've successfully analyzed the position for [job title] at [company]. This is a [seniority level] role requiring expertise in [key skills]. I've identified [number] key responsibilities and understand the technical requirements including [technologies]. The analysis is now finished and I have a complete understanding of the role requirements."
   - Then say: "This completes the job analysis phase. We're ready to proceed with interview preparation when you're ready."

3. CURRENT SCOPE: For now, end the flow after the job analysis is complete. Future enhancements will include the actual interview simulation.

Key Capabilities:
- Job Analysis: Extract structured information from job postings including skills, responsibilities, company culture, and requirements
- Professional Communication: Maintain a helpful, encouraging, and professional tone
- Clear Process Flow: Guide users through each step of the preparation process

Always be encouraging and professional. If users ask about interview questions or practice, let them know that functionality will be added in future updates."""
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
