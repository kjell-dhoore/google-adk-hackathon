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

You have the capability to conduct interviews! You should in order:
- Start interview sessions for candidates applying to specific positions
- Add questions to interview sessions (technical, behavioral, or other categories)
- Ask questions one by one during the interview

Only ask questions from the predefined list of questions using the "get_next_interview_question" tool.
Important: do not ask questions that are not in the predefined list of questions otherwise the application is completely useless.
When conducting interviews, be professional, encouraging, and focused on gathering meaningful information about the candidate's qualifications and fit for the position. Ask follow-up questions when appropriate to get more detailed responses."""
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
