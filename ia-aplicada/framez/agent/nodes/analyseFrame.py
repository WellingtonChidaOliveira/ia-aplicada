from agent.prompts.v1.imagePrompt import image_prompt
from service.ollama import send_image_ollama
import base64
import os
import time
from models.GraphMessage import GraphMessage


def carregar_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analise_frame(
    frame_path: str, frame_name: str, frame_num: int, total: int, retries: int = 3
) -> str:
    img_b64 = carregar_base64(frame_path)

    # extrai o timestamp do nome do arquivo: frame_0001_t006.25.jpg -> 6.25s
    try:
        t = frame_name.split("_t")[1].replace(".jpg", "")
        timestamp_label = f"t={float(t):.2f}s"
    except Exception:
        timestamp_label = f"frame {frame_num}"

    for tentativa in range(1, retries + 1):
        try:
            response = send_image_ollama(
                img_b64,
                image_prompt(frame_num, total, timestamp_label),
            )
            content = response.message.content.strip()
            if len(content) >= 30:
                return content
            print(
                f"    Tentativa {tentativa} insuficiente ({len(content)} chars), repetindo..."
            )
        except Exception as e:
            print(f"    Tentativa {tentativa} falhou: {e}")

        time.sleep(2)

    return "[análise indisponível]"


def analyse_frames(state: GraphMessage) -> GraphMessage:
    frames = sorted(state.get("frames"))
    total = len(frames)
    print(f"Analisando {total} frames...")

    analises = []
    for i, frame_name in enumerate(frames, start=1):
        frame_path = os.path.join(state.get("frames_dir"), frame_name)
        print(f"  Frame {i}/{total}: {frame_name}")
        resultado = analise_frame(frame_path, frame_name, i, total)
        analises.append(f"[Frame {i} - {frame_name}] {resultado}")
        time.sleep(1)

    analysis = "\n\n".join(analises)
    print("\nAnálise completa:")
    print(analysis)

    return {"analysis": analysis}
