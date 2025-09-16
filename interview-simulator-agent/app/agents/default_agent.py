from google.genai import types

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

def get_config():
    """Returns the configuration for the default agent."""
    
    tool_functions = {"get_weather": get_weather}

    live_connect_config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        tools=list(tool_functions.values()),
        system_instruction=types.Content(
            parts=[
                types.Part(
                    text="""You are a helpful AI assistant designed to provide accurate and useful information. You are able to accommodate different languages and tones of voice."""
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
