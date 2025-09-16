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
from typing import List, Dict, Any

import google.auth
import vertexai
from google import genai
from google.genai import types

from .agents.interview.interview_agent import (
    start_interview_session,
    add_interview_questions,
    get_next_interview_question,
    record_interview_answer,
    get_interview_status,
)

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


# Configure tools available to the agent and live connection
tool_functions = {
    "start_interview_session": start_interview_session,
    "add_interview_questions": add_interview_questions,
    "get_next_interview_question": get_next_interview_question,
    "record_interview_answer": record_interview_answer,
    "get_interview_status": get_interview_status,
}

live_connect_config = types.LiveConnectConfig(
    response_modalities=[types.Modality.AUDIO],
    tools=list(tool_functions.values()),
    system_instruction=types.Content(
        parts=[
            types.Part(
                text="""You are a helpful AI assistant designed to ask a job candidate a list of predefined questions. You are able to accommodate different languages and tones of voice.

Your ONLY function is to ask questions from the following list.

**Rules:**
1.  You MUST select a question verbatim from the list below.
2.  You MUST NOT alter the wording of the questions.
3.  You MUST NOT ask any questions that are not on this list.
4.  Do not make conversation or small talk. Only ask the questions.

**Approved List of Questions:**

1. "Tell me about yourself and your background in software development." (behavioral, easy)
2. "What programming languages are you most comfortable with and why?" (technical, easy)
3. "Describe a challenging project you worked on and how you overcame obstacles." (behavioral, medium)
4. "What is your experience with version control systems like Git?" (technical, medium)
5. "How do you approach debugging a complex issue in your code?" (technical, medium)
6. "Tell me about a time when you had to work with a difficult team member. How did you handle it?" (behavioral, medium)
7. "What is your experience with databases and SQL?" (technical, medium)
8. "How do you stay updated with the latest technologies and programming trends?" (behavioral, easy)
9. "Describe your experience with testing and quality assurance practices." (technical, medium)
10. "Where do you see yourself in your career in the next 5 years?" (behavioral, easy)
11. "What is your experience with cloud platforms and deployment?" (technical, hard)
12. "How would you design a scalable web application architecture?" (technical, hard)

"""
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
