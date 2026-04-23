from agent.prompts.v1.image_prompt import image_prompt
from service.ollama import send_image_ollama
import base64
import os
import time
from models.graph_message import GraphMessage
from utils.config import Config


class AnalyseFrameNode:
    def __init__(self):
        pass

    def load_base64(self, path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def analyse_frame(
        self,
        frame_path: str,
        frame_name: str,
        frame_num: int,
        total: int,
    ) -> str:
        img_b64 = self.load_base64(frame_path)

        # extract timestamp from filename: frame_0001_t006.25.jpg -> 6.25s
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

    def analyse_frames(self, state: GraphMessage) -> GraphMessage:
        frames = sorted(state.get("frames"))
        total = len(frames)
        print(f"Analysing {total} frames...")

        analyses = []
        for i, frame_name in enumerate(frames, start=1):
            frame_path = os.path.join(state.get("frames_dir"), frame_name)
            print(f"  Frame {i}/{total}: {frame_name}")
            result = self.analyse_frame(frame_path, frame_name, i, total)
            analyses.append(f"[Frame {i} - {frame_name}] {result}")
            time.sleep(Config.FRAME_SLEEP_SECONDS)

        analysis = "\n\n".join(analyses)
        print("\nAnalysis complete:")
        print(analysis)

        return {"analysis": analysis}
