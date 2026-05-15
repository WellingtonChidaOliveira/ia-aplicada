import os
import time
from langchain.tools import tool
import json
from agent.tools.ffmpeg_tools import (
    _generate_and_execute,
    _prepare_text_file,
)


@tool
def build_clip(
    video_path: str, segments_json: str, phrase: str, color_grade_json: str = "{}"
) -> dict:
    """
    Renders final video clips using color grading decided by Gemini.
    Call ONCE after generate_phrase with all segments.

    Args:
        video_path: from get_video_info
        segments_json: JSON string from parse_video_analysis
        phrase: from generate_phrase ONLY
        color_grade_json: JSON string of color_grade from parse_video_analysis
    """
    try:
        if isinstance(segments_json, str):
            segments = json.loads(segments_json)
        elif isinstance(segments_json, dict):
            segments = segments_json.get("segments", [])
        else:
            segments = segments_json
    except Exception as e:
        return {
            "success": False,
            "error": f"Invalid segments_json: {e}",
            "output_paths": [],
        }

    if isinstance(phrase, dict):
        phrase = phrase.get("phrase", "")
    phrase = str(phrase).strip()

    try:
        if isinstance(color_grade_json, str):
            color_grade = json.loads(color_grade_json) if color_grade_json != "{}" else {}
        elif isinstance(color_grade_json, dict):
            color_grade = color_grade_json
        else:
            color_grade = {}
    except Exception:
        color_grade = {}

    # fallback se color_grade vazio
    if not color_grade:
        color_grade = {
            "brightness": -0.20,
            "contrast": 1.40,
            "saturation": 0.40,
            "gamma": 0.80,
            "teal_intensity": 0.18,
            "vignette_angle": "PI/4",
            "fontsize": 72,
            "text_y": "h*0.78",
            "blur_duration": 3.0,
        }

    if not segments:
        return {
            "success": False,
            "error": "No valid segments to render",
            "output_paths": [],
            "output_path": "",
        }

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    base_timestamp = int(time.time())
    text_file_path = _prepare_text_file(phrase, output_dir, base_timestamp)

    output_paths = []
    errors = []

    try:
        for seg in segments:
            rank = seg.get("rank", len(output_paths) + 1)
            start_time = seg["start_time"]
            end_time = seg["end_time"]
            duration = end_time - start_time

            print(f"\n── Gerando clipe top{rank} ─────────────────────────────")
            print(f"   Trecho: {start_time:.2f}s → {end_time:.2f}s ({duration:.1f}s)")
            print(f"   Frase: {phrase}")

            output_path = os.path.join(
                output_dir, f"{base_timestamp}_{video_name}_top{rank}.mp4"
            )

            result = _generate_and_execute(
                video_path=video_path,
                start_time=start_time,
                duration=duration,
                text_file_path=text_file_path,
                rank=rank,
                output_path=output_path,
                params=color_grade,
            )

            if result["success"]:
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"   ✓ Salvo em: {output_path} ({size_mb:.1f}MB)")
                output_paths.append(output_path)
            else:
                print(f"   ✗ Erro no top{rank}: {result['error'][:200]}")
                errors.append(result["error"])

    finally:
        try:
            if text_file_path and os.path.exists(text_file_path):
                os.remove(text_file_path)
        except Exception:
            pass

    print(f"\n══ {len(output_paths)}/{len(segments)} clipes gerados ══")

    return {
        "success": len(output_paths) > 0,
        "output_paths": output_paths,
        "output_path": output_paths[0] if output_paths else "",
        "error": "; ".join(errors) if errors else "",
    }
