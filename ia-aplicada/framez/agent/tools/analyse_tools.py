import os
import time
from langchain.tools import tool
from utils.config import Config
from utils.helper import load_base64
from service.ollama import send_image_ollama
from agent.prompts.v2.image_prompt import image_prompt


def _analyse_single_frame(
    frame_path: str,
    frame_name: str,
    frame_num: int,
    total: int,
) -> str:
    """Analisa um único frame — função interna, não exposta ao LLM."""
    img_b64 = load_base64(frame_path)

    try:
        t = frame_name.split("_t")[1].replace(".jpg", "")
        timestamp_label = f"t={float(t):.2f}s"
    except Exception:
        timestamp_label = f"frame {frame_num}"

    for attempt in range(1, Config.RETRIES_ANALYSE + 1):
        try:
            response = send_image_ollama(
                img_b64,
                image_prompt(frame_num, total, timestamp_label),
            )
            content = response.message.content.strip()
            if len(content) >= Config.MIN_CONTENT_LENGTH:
                return content
            print(
                f"    Attempt {attempt} insufficient ({len(content)} chars), retrying..."
            )
        except Exception as e:
            print(f"    Attempt {attempt} failed: {e}")

        time.sleep(Config.RETRY_SLEEP_SECONDS)

    return Config.UNAVAILABLE_LABEL


@tool
def analyse_frames(frames_dir: str, frames: list[str]) -> dict:
    """
    Analyses video frames using a local vision model to describe exercise intensity,
    athlete expression and visual quality of each frame.

    Call after extract_frames.
    Input: frames_dir and frames list from extract_frames output.
    Returns: analysis text describing each frame with timestamps.
    """
    sorted_frames = sorted(frames)
    total = len(sorted_frames)
    print(f"Analysing {total} frames...")

    analyses = []
    for i, frame_name in enumerate(sorted_frames, start=1):
        frame_path = os.path.join(frames_dir, frame_name)
        print(f"  Frame {i}/{total}: {frame_name}")
        result = _analyse_single_frame(frame_path, frame_name, i, total)
        analyses.append(f"[Frame {i} - {frame_name}] {result}")
        time.sleep(Config.FRAME_SLEEP_SECONDS)

    analysis = "\n\n".join(analyses)
    print(f"\nAnalysis complete: {len(analyses)} frames processed")

    return {"analysis": analysis}
