import time
from langchain.tools import tool
from google import genai
from google.genai import types
from utils.config import Config


@tool
def analyse_video_gemini(video_path: str, duration: float) -> dict:
    """
    Analyses the full video using Gemini vision model.
    Replaces extract_frames + analyse_frames entirely.

    Call after get_video_info.
    Input: video_path and duration from get_video_info.
    Returns: analysis text and top 3 suggested segments with start_time, end_time and reason.
    """
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    print(f"Uploading video to Gemini: {video_path}")
    video_file = client.files.upload(file=video_path)

    # aguarda o processamento do vídeo
    print("Waiting for Gemini to process video...")
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(f"Gemini failed to process video: {video_file.state.name}")

    print("Video processed. Analysing...")

    prompt = f"""You are analysing a gym workout video of {duration:.1f} seconds.

Analyse the full video and identify the TOP 3 best segments for a dark cinematic TikTok clip.

For each segment consider:
- Peak muscle effort and intensity
- Athlete expression and focus
- Visual composition and lighting quality
- Movement fluidity

Each segment must be between 20 and 45 seconds.
Timestamps must be within 0 and {duration:.1f} seconds.

Respond ONLY with this exact JSON, no text before or after:
{{
  "analysis": "brief overall description of the video content",
  "segments": [
    {{"rank": 1, "start_time": 0.0, "end_time": 0.0, "reason": "why this is the best segment"}},
    {{"rank": 2, "start_time": 0.0, "end_time": 0.0, "reason": "why this is the second best"}},
    {{"rank": 3, "start_time": 0.0, "end_time": 0.0, "reason": "why this is the third best"}}
  ]
}}"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=video_file.uri,
                        mime_type=video_file.mime_type,
                    ),
                    types.Part.from_text(text=prompt),
                ],
            )
        ],
    )

    content = response.text.strip()
    print(f"Gemini response:\n{content}")

    # limpa o arquivo do Gemini após uso
    try:
        client.files.delete(name=video_file.name)
    except Exception:
        pass

    return {"gemini_analysis": content}
