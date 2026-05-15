import json
import os
import re
import shutil
import subprocess

from langchain.tools import tool

from service import ollama
from utils import helper
from utils.config import Config


def _segment(start_time: float, duration: float, rank: int, reason: str) -> dict:
    clip_duration = min(30.0, max(15.0, duration - start_time))
    end_time = min(duration, start_time + clip_duration)
    if end_time - start_time < 15.0:
        start_time = max(0.0, duration - 15.0)
        end_time = duration
    return {
        "rank": rank,
        "start_time": round(start_time, 2),
        "end_time": round(end_time, 2),
        "reason": reason,
    }


def _timestamp_from_frame(frame_name: str) -> float:
    try:
        return float(frame_name.split("_t")[1].replace(".jpg", ""))
    except Exception:
        return 0.0


def _json_from_text(text: str) -> dict:
    cleaned = re.sub(r"```json\s*", "", text)
    cleaned = re.sub(r"```\s*", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group())


def _extract_frames(video_path: str, duration: float) -> dict:
    """Extrai frames do vídeo em intervalos regulares."""
    frames_dir = f"./tmp/gym_frames_{os.getpid()}"
    os.makedirs(frames_dir, exist_ok=True)

    calculated = int(duration / 6)
    max_frames = max(8, min(calculated, 12))

    start, end = 2.0, max(2.1, duration - 2.0)
    interval = (end - start) / (max_frames - 1)
    timestamps = [start + i * interval for i in range(max_frames)]

    frames = []
    for i, t in enumerate(timestamps, start=1):
        filename = f"frame_{i:04d}_t{t:07.2f}.jpg"
        output_path = os.path.join(frames_dir, filename)

        subprocess.run(
            [
                "ffmpeg",
                "-ss",
                str(t),
                "-i",
                video_path,
                "-vframes",
                "1",
                "-vf",
                "scale=min(1280\\,iw):min(720\\,ih):force_original_aspect_ratio=decrease",
                "-q:v",
                "2",
                output_path,
                "-y",
            ],
            capture_output=True,
        )

        if os.path.exists(output_path):
            frames.append(filename)

    print(f"Frames extraídos: {len(frames)}/{max_frames}")
    return {"frames_dir": frames_dir, "frames": sorted(frames)}


def _build_contact_sheet(frames_dir: str, frames: list[str]) -> str:
    """Builds a single grid image from sampled frames for local VLM stability."""
    rows = 2 if len(frames) <= 8 else 3
    cols = 4
    contact_sheet_path = os.path.join(frames_dir, "contact_sheet.jpg")

    subprocess.run(
        [
            "ffmpeg",
            "-pattern_type",
            "glob",
            "-i",
            os.path.join(frames_dir, "frame_*.jpg"),
            "-vf",
            f"scale=640:-1,tile={cols}x{rows}",
            "-frames:v",
            "1",
            "-q:v",
            "2",
            contact_sheet_path,
            "-y",
        ],
        capture_output=True,
    )

    if not os.path.exists(contact_sheet_path):
        raise ValueError("Failed to build contact sheet from extracted frames")

    return contact_sheet_path


def _analyse_frames_local(frames_dir: str, frames: list[str], duration: float) -> dict:
    """
    Envia todos os frames em uma única chamada para o modelo visual local.
    Retorna segments e color_grade prontos para uso.
    """

    # monta lista de timestamps para o prompt
    frame_labels = []
    for frame_name in frames:
        try:
            t = frame_name.split("_t")[1].replace(".jpg", "")
            frame_labels.append(f"t={float(t):.2f}s")
        except Exception:
            frame_labels.append(frame_name)

    timestamps_str = ", ".join(frame_labels)

    if not frames:
        raise ValueError("No frames were extracted from the video")

    contact_sheet_path = _build_contact_sheet(frames_dir, frames)
    images_b64 = [helper.load_base64(contact_sheet_path)]

    prompt = f"""/no_think
Return ONLY valid JSON. No markdown. No explanation.

You are choosing TikTok-ready clips from a bodybuilding gym video.
The image is a contact sheet with {len(frames)} sampled frames.
Read frames left-to-right, top-to-bottom.
Frame timestamps in order: {timestamps_str}.
Video duration: {duration:.1f}s.

Choose the TOP 3 clip segments, 20-45 seconds each.
Prefer moments where the athlete is sharp, visible, centered for a 9:16 crop, in a strong pose or peak effort, and not hidden or blurry.
Avoid idle, badly framed, too dark, obstructed, or crop-unfriendly moments.
Choose a cold dark gym color grade, but keep the athlete visible.

Timestamps must be seconds between 0 and {duration:.1f}.

JSON schema:
{{
  "analysis": "brief description of video content and lighting",
  "color_grade": {{
    "brightness": -0.20,
    "contrast": 1.40,
    "saturation": 0.40,
    "gamma": 0.80,
    "teal_intensity": 0.18,
    "vignette_angle": "PI/4",
    "fontsize": 72,
    "text_y": "h*0.78",
    "blur_duration": 3.0,
    "rationale": "one sentence explaining the grading choice based on actual lighting"
  }},
  "segments": [
    {{"rank": 1, "start_time": 5.0, "end_time": 35.0, "reason": "strongest TikTok-ready moment"}},
    {{"rank": 2, "start_time": 20.0, "end_time": 50.0, "reason": "second strongest option"}},
    {{"rank": 3, "start_time": 35.0, "end_time": 65.0, "reason": "third strongest option"}}
  ]
}}

Use conservative values:
brightness -0.05 to -0.20, contrast 1.0 to 1.45, saturation 0.4 to 0.75, gamma 0.75 to 0.95,
teal_intensity 0.05 to 0.25, vignette_angle "PI/3" or "PI/4", fontsize 60 to 84,
text_y "h*0.70" or "h*0.78", blur_duration 1.5 to 4.0."""

    print(f"Enviando {len(frames)} frames para Ollama {Config.OLLAMA_VISION_MODEL}...")

    response = ollama.send_image_ollama(images_b64, prompt)

    content = response.strip()
    print(f"Resposta Ollama:\n{content[:500]}...")
    return {"raw_response": content}


def _analyse_frames_individually(
    frames_dir: str, frames: list[str], duration: float
) -> dict:
    """Scores individual frames when the contact-sheet response is not parseable."""
    scored_frames = []

    for frame_name in frames:
        timestamp = _timestamp_from_frame(frame_name)
        image_b64 = helper.load_base64(os.path.join(frames_dir, frame_name))
        prompt = f"""/no_think
Return only JSON. Score this gym workout frame for TikTok posting.
Timestamp: {timestamp:.2f}s of a {duration:.1f}s video.
Score 0-100 using: athlete sharpness, visibility, centered 9:16 crop, strong pose/effort, lighting, and no obstruction.
JSON schema:
{{"score": 80, "reason": "short reason"}}"""

        try:
            response = ollama.send_image_ollama([image_b64], prompt, num_predict=512)
            data = _json_from_text(response)
            score = float(data.get("score", 0))
            reason = str(data.get("reason", "visually selected frame"))
        except Exception as e:
            print(f"  Falha ao pontuar {frame_name}: {e}")
            score = 0.0
            reason = "frame scoring failed"

        scored_frames.append(
            {
                "timestamp": timestamp,
                "score": score,
                "reason": reason,
            }
        )

    scored_frames = [item for item in scored_frames if item["score"] > 0]
    scored_frames.sort(key=lambda item: item["score"], reverse=True)
    top_frames = scored_frames[:3]

    if not top_frames or top_frames[0]["score"] <= 0:
        raise ValueError("No usable frame scores returned by local vision model")

    segments = []
    for rank, item in enumerate(top_frames, start=1):
        start_time = max(0.0, item["timestamp"] - 12.0)
        segments.append(
            _segment(
                start_time=start_time,
                duration=duration,
                rank=rank,
                reason=f"score {item['score']:.0f}: {item['reason']}",
            )
        )

    return {
        "analysis": "Local vision model scored sampled workout frames for TikTok suitability.",
        "color_grade": {
            "brightness": -0.15,
            "contrast": 1.30,
            "saturation": 0.55,
            "gamma": 0.85,
            "teal_intensity": 0.14,
            "vignette_angle": "PI/4",
            "fontsize": 72,
            "text_y": "h*0.78",
            "blur_duration": 2.5,
            "rationale": "Conservative dark gym grade that preserves athlete visibility.",
        },
        "segments": segments,
    }


@tool
def analyse_video_local(video_path: str, duration: float) -> dict:
    """
    Analyses video by extracting frames and sending all at once to a local vision model.
    No cloud API needed.

    Call after get_video_info.
    Input: video_path and duration from get_video_info.
    Returns: analysis compatible dict with segments and color_grade.
    """
    # extrai frames
    frame_data = _extract_frames(video_path, duration)
    frames_dir = frame_data["frames_dir"]
    frames = frame_data["frames"]

    try:
        # analisa todos os frames em uma chamada
        result = _analyse_frames_local(frames_dir, frames, duration)
        raw = result["raw_response"]

        # tenta parsear direto
        try:
            data = _json_from_text(raw)
            return {"analysis": json.dumps(data)}
        except Exception as e:
            print(f"  Erro ao parsear resposta do Ollama: {e}")

        try:
            print("  Pontuando frames individualmente com o modelo local...")
            data = _analyse_frames_individually(frames_dir, frames, duration)
            return {"analysis": json.dumps(data)}
        except Exception as e:
            print(f"  Erro ao pontuar frames individualmente: {e}")

        # fallback determinístico se parse falhar
        print("  Usando fallback determinístico...")
        third = duration / 3
        fallback = {
            "analysis": "gym workout video",
            "color_grade": {
                "brightness": -0.20,
                "contrast": 1.40,
                "saturation": 0.40,
                "gamma": 0.80,
                "teal_intensity": 0.18,
                "vignette_angle": "PI/4",
                "fontsize": 72,
                "text_y": "h*0.78",
                "blur_duration": 3.0,
                "rationale": "default Dark Knight grade",
            },
            "segments": [
                _segment(third * 0.2, duration, 1, "first section"),
                _segment(third, duration, 2, "middle section"),
                _segment(third * 1.8, duration, 3, "last section"),
            ],
        }
        return {"analysis": json.dumps(fallback)}

    finally:
        # limpa frames temporários
        try:
            shutil.rmtree(frames_dir)
        except Exception:
            pass


@tool
def parse_video_analysis(analysis: str, duration: float = 0.0) -> dict:
    """
    Parses the JSON response from analyse_video_local into structured segments.

    Call after analyse_video_local and before build_clip.
    Input: analysis string and video duration from get_video_info.
    Returns: segments list ready for build_clip.
    """
    # remove markdown code blocks
    cleaned = re.sub(r"```json\s*", "", analysis)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()

    try:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
            segments = data.get("segments", [])
            color_grade = data.get("color_grade", {})

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
                if duration > 0:
                    seg["start_time"] = max(0.0, min(float(seg["start_time"]), duration))
                    seg["end_time"] = max(0.0, min(float(seg["end_time"]), duration))
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
                "segments_json": json.dumps(valid_segments),
                "color_grade": color_grade,
                "color_grade_json": json.dumps(color_grade),
                "analysis": data.get("analysis", ""),
            }
    except Exception as e:
        print(f"Erro ao parsear: {e}")

    return {
        "segments": [],
        "segments_json": "[]",
        "color_grade": {},
        "color_grade_json": "{}",
        "analysis": "",
    }
