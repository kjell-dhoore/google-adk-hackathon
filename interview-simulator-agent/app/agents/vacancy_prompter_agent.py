from google.genai import types

def get_config():
    """Returns the configuration for the vacancy prompter agent."""
    
    tool_functions = {}  # No tools needed for this agent

    live_connect_config = types.LiveConnectConfig(
        response_modalities=[types.Modality.TEXT],
        system_instruction=types.Content(
            parts=[
                types.Part(
                    text="""You are the first agent in a three-agent workflow. Your only job is to greet the user and ask them to paste the job vacancy description. Do not say anything else."""
                )
            ]
        ),
    )
    
    return live_connect_config, tool_functions
