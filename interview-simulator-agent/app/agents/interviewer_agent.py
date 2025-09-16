from google.genai import types

def get_config():
    """Returns the configuration for the interviewer agent."""
    
    tool_functions = {}  # No specific tools needed for this agent

    live_connect_config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(
            parts=[
                types.Part(
                    text="""You are an interviewer. You will be given a list of questions. Ask the questions one by one and wait for the user's response. Do not deviate from the questions."""
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
    
    return live_connect_config, tool_functions
