from google.genai import types

def get_config():
    """Returns the configuration for the interview agent."""
    
    tool_functions = {}  # No specific tools needed for this agent

    live_connect_config = types.LiveConnectConfig(
        response_modalities=[types.Modality.TEXT],
        tools=list(tool_functions.values()),
        system_instruction=types.Content(
            parts=[
                types.Part(
                    text="""You are an expert interviewer. Your role is to analyze a job vacancy description provided to you and generate a list of insightful interview questions that would help assess a candidate's suitability for the role. The questions should cover technical skills, soft skills, and cultural fit."""
                )
            ]
        ),
    )
    
    return live_connect_config, tool_functions
