import time
from langchain.tools import tool
from google import genai
from google.genai import types
from utils.config import Config
import subprocess
import json
import re
import os


def _compress_for_gemini(video_path: str) -> str:
    """Comprime o vídeo para análise — não afeta o clip final."""
    compressed_path = video_path.replace(".mp4", "_gemini.mp4").replace(
        ".mov", "_gemini.mp4"
    )

    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        "scale=1280:-2",  # reduz para 720p
        "-c:v",
        "libx264",
        "-crf",
        "28",  # qualidade menor, arquivo menor
        "-preset",
        "fast",
        "-c:a",
        "aac",
        "-b:a",
        "64k",
        compressed_path,
        "-y",
    ]

    subprocess.run(cmd, capture_output=True)

    size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
    print(f"Vídeo comprimido: {size_mb:.1f}MB → {compressed_path}")

    return compressed_path


@tool
def analyse_video_gemini(video_path: str, duration: float) -> dict:
    """
    Analyses the full video using Gemini vision model.
    Replaces extract_frames + analyse_frames entirely.

    Call after get_video_info.
    Input: video_path and duration from get_video_info.
    Returns: analysis text and top 3 suggested segments with start_time, end_time and reason.
    """
    #     client = genai.Client(api_key=Config.GEMINI_API_KEY)

    #     compressed_path = _compress_for_gemini(video_path)

    #     print(f"Uploading video to Gemini: {compressed_path}")
    #     video_file = client.files.upload(file=compressed_path)

    #     # aguarda o processamento do vídeo
    #     print("Waiting for Gemini to process video...")
    #     while video_file.state.name == "PROCESSING":
    #         time.sleep(2)
    #         video_file = client.files.get(name=video_file.name)

    #     if video_file.state.name == "FAILED":
    #         raise ValueError(f"Gemini failed to process video: {video_file.state.name}")

    #     print("Video processed. Analysing...")

    #     prompt = f"""You are analysing a gym workout video of {duration:.1f} seconds.

    # Analyse the full video and identify the TOP 3 best segments for a dark cinematic TikTok clip.

    # IMPORTANT: All timestamps must be in SECONDS, not normalized values.
    # The video is {duration:.1f} seconds long, so timestamps must be between 0 and {duration:.1f}.
    # Each segment must be between 20 and 45 seconds long.

    # For each segment consider:
    # - Peak muscle effort and intensity
    # - Athlete expression and focus
    # - Visual composition and lighting quality

    # Respond ONLY with valid JSON, no markdown, no code blocks, no extra text:
    # {{
    #   "analysis": "brief description",
    #   "segments": [
    #     {{"rank": 1, "start_time": 5.0, "end_time": 35.0, "reason": "..."}},
    #     {{"rank": 2, "start_time": 36.0, "end_time": 62.0, "reason": "..."}},
    #     {{"rank": 3, "start_time": 15.0, "end_time": 45.0, "reason": "..."}}
    #   ]
    # }}"""

    #     response = client.models.generate_content(
    #         model="gemini-2.5-flash",
    #         contents=[
    #             types.Content(
    #                 role="user",
    #                 parts=[
    #                     types.Part.from_uri(
    #                         file_uri=video_file.uri,
    #                         mime_type=video_file.mime_type,
    #                     ),
    #                     types.Part.from_text(text=prompt),
    #                 ],
    #             )
    #         ],
    #     )

    #     content = response.text.strip()
    #     print(f"Gemini response:\n{content}")

    #     # limpa o arquivo do Gemini após uso
    #     try:
    #         client.files.delete(name=video_file.name)
    #     except Exception:
    #         pass

    content = """```json
        {
        "analysis": "A male bodybuilder records himself posing in a gym, showcasing various muscle groups and transitions between poses in front of a mirror.",
        "segments": [
            {
            "rank": 1,
            "start_time": 5.0,
            "end_time": 35.0,
            "reason": "This segment features a powerful sequence of upper body poses, including double biceps, side chest, side lateral, and overhead triceps, demonstrating peak muscle definition and athlete focus suitable for a cinematic clip."
            },
            {
            "rank": 2,
            "start_time": 36.0,
            "end_time": 66.0,
            "reason": "This segment offers a comprehensive view of the athlete's physique, starting with a clear quad flex and transitioning into multiple upper body poses such as double biceps, side lateral, back double biceps, and front lat spread, showcasing both leg and back development with intensity."
            },
            {
            "rank": 3,
            "start_time": 22.0,
            "end_time": 52.0,
            "reason": "This segment effectively showcases the deltoids with the lateral raise, transitions to overhead triceps, then a powerful quad flex for leg definition, and finally ends with another strong double biceps pose, highlighting diverse muscle groups and transitions."
            }
        ]
        }
        ```"""

    return {"gemini_analysis": content}


@tool
def parse_gemini_analysis(gemini_analysis: str, duration: float = 0.0) -> dict:
    """
    Parses the JSON response from analyse_video_gemini into structured segments.

    Call after analyse_video_gemini and before build_clip.
    Input: gemini_analysis string and video duration from get_video_info.
    Returns: segments list ready for build_clip.
    """
    # remove markdown code blocks
    cleaned = re.sub(r"```json\s*", "", gemini_analysis)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()

    try:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
            segments = data.get("segments", [])

            # detecta se timestamps são normalizados (0-1) em vez de segundos
            max_end = max(s["end_time"] for s in segments) if segments else 0
            is_normalized = max_end <= 1.5 and duration > 10

            if is_normalized and duration > 0:
                print(
                    f"  Timestamps normalizados detectados — convertendo para segundos (duration={duration:.1f}s)"
                )
                for seg in segments:
                    seg["start_time"] = round(seg["start_time"] * duration, 2)
                    seg["end_time"] = round(seg["end_time"] * duration, 2)

            # valida e filtra segmentos inválidos
            valid_segments = []
            for seg in segments:
                seg_duration = seg["end_time"] - seg["start_time"]
                if seg_duration >= 15:
                    valid_segments.append(seg)
                else:
                    print(
                        f"  Segmento inválido ignorado: {seg['start_time']}s → {seg['end_time']}s ({seg_duration:.1f}s)"
                    )

            print(f"  Segmentos válidos: {len(valid_segments)}/3")
            for s in valid_segments:
                print(
                    f"    rank {s['rank']}: {s['start_time']}s → {s['end_time']}s ({s['end_time'] - s['start_time']:.1f}s)"
                )

            return {
                "segments": valid_segments,
                "analysis": data.get("analysis", ""),
            }
    except Exception as e:
        print(f"Erro ao parsear: {e}")

    return {"segments": [], "analysis": ""}
