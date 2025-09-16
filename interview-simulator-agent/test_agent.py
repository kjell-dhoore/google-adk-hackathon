import asyncio
import os

import google.auth
import vertexai
from google import genai

from app.agents.interview_agent import get_config

# --- Configuration ---
# You can change the vacancy description here
VACANCY_DESCRIPTION = """
**Job Title:** Senior Software Engineer (Backend)

**Location:** San Francisco, CA

**Job Description:**

We are looking for a talented and experienced Senior Software Engineer to join our backend development team. In this role, you will be responsible for designing, developing, and maintaining our core backend services. You will work with a team of talented engineers to build scalable, reliable, and high-performance systems.

**Responsibilities:**

* Design, develop, and maintain our core backend services.
* Write clean, maintainable, and well-tested code.
* Collaborate with other engineers to build new features.
* Troubleshoot and debug production issues.
* Mentor junior engineers.

**Qualifications:**

* 5+ years of experience in backend development.
* Strong proficiency in Python, Go, or a similar language.
* Experience with distributed systems and microservices architecture.
* Experience with cloud platforms such as Google Cloud or AWS.
* Excellent problem-solving and communication skills.
"""

# --- Agent and Model Initialization ---

async def main():
    """
    Initializes the Gemini client, loads the agent, and runs the test.
    """
    # Initialize Google Cloud clients
    credentials, project_id = google.auth.default()
    vertexai.init(project=project_id, location="us-central1")
    
    # Get agent configuration
    live_connect_config, _ = get_config()

    # Initialize the Generative Model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", # Or another suitable model
        system_instruction=live_connect_config.system_instruction,
    )

    # --- Run the test ---
    print("--- Sending vacancy description to the agent... ---")
    print(VACANCY_DESCRIPTION)
    
    response = await model.generate_content_async(VACANCY_DESCRIPTION)
    
    print("\n--- Agent's response: ---")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())


