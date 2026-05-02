import os
import time
from langchain.tools import tool
import json
from agent.tools.ffmpeg_tools import (
    _generate_ffmpeg_command_internal,
    _execute_ffmpeg_internal,
    _prepare_text_file,
)


@tool
def build_clip(video_path: str, segments_json: str, phrase: str) -> dict:
    """
    Renders final video clips using LLM-generated FFmpeg commands.
    Call ONCE after generate_phrase with all segments.

    Args:
        video_path: from get_video_info
        segments_json: JSON string from parse_gemini_analysis
        phrase: from generate_phrase ONLY
    """
    try:
        segments = json.loads(segments_json)
    except Exception as e:
        return {
            "success": False,
            "error": f"Invalid segments_json: {e}",
            "output_paths": [],
        }

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    base_timestamp = int(time.time())

    # cria o arquivo de texto UMA VEZ para todos os clipes
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

            command = _generate_ffmpeg_command_internal(
                video_path=video_path,
                start_time=start_time,
                duration=duration,
                text_file_path=text_file_path,
                phrase=phrase,
                rank=rank,
                output_path=output_path,
                style_hint="dark cinematic gym motivation",
            )

            result = _execute_ffmpeg_internal(
                command,
                output_path,
                text_file_path,
            )

            if result["success"]:
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"   ✓ Salvo em: {output_path} ({size_mb:.1f}MB)")
                output_paths.append(output_path)
            else:
                print(f"   ✗ Erro no top{rank}: {result['error'][:200]}")
                errors.append(result["error"])

    finally:
        # deleta o txt apenas no final, depois de todos os clipes
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
