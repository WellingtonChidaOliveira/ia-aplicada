import base64


def calculate_max_frames(duration: float) -> int:
    """
    Quantity of frames to sample based on duration.
    Logic: 1 frame every ~6s, minimum 8, maximum 20.
    """
    calculated = int(duration / 6)
    return max(8, min(calculated, 20))


def load_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
