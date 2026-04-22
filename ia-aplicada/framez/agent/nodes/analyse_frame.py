from agent.prompts.v1.image_prompt import image_prompt
from service.ollama import send_image_ollama
import base64
import os
import time
from models.graph_message import GraphMessage

MIN_CONTENT_LENGTH = 30
RETRY_SLEEP_SECONDS = 2
FRAME_SLEEP_SECONDS = 1
UNAVAILABLE_LABEL = "[analysis unavailable]"


def load_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyse_frame(
    frame_path: str, frame_name: str, frame_num: int, total: int, retries: int = 3
) -> str:
    img_b64 = load_base64(frame_path)

    # extract timestamp from filename: frame_0001_t006.25.jpg -> 6.25s
    try:
        t = frame_name.split("_t")[1].replace(".jpg", "")
        timestamp_label = f"t={float(t):.2f}s"
    except Exception:
        timestamp_label = f"frame {frame_num}"

    for attempt in range(1, retries + 1):
        try:
            response = send_image_ollama(
                img_b64,
                image_prompt(frame_num, total, timestamp_label),
            )
            content = response.message.content.strip()
            if len(content) >= MIN_CONTENT_LENGTH:
                return content
            print(
                f"    Attempt {attempt} insufficient ({len(content)} chars), retrying..."
            )
        except Exception as e:
            print(f"    Attempt {attempt} failed: {e}")

        time.sleep(RETRY_SLEEP_SECONDS)

    return UNAVAILABLE_LABEL


def analyse_frames(state: GraphMessage) -> GraphMessage:
    frames = sorted(state.get("frames"))
    total = len(frames)
    print(f"Analysing {total} frames...")

    analyses = []
    for i, frame_name in enumerate(frames, start=1):
        frame_path = os.path.join(state.get("frames_dir"), frame_name)
        print(f"  Frame {i}/{total}: {frame_name}")
        result = analyse_frame(frame_path, frame_name, i, total)
        analyses.append(f"[Frame {i} - {frame_name}] {result}")
        time.sleep(FRAME_SLEEP_SECONDS)

    analysis = "\n\n".join(analyses)
    print("\nAnalysis complete:")
    print(analysis)

    return {"analysis": analysis}
