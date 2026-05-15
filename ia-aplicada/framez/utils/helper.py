import base64
import os


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


def load_base64_files(directory: str, filenames: list[str]) -> list[str]:
    """Load a sorted list of files from a directory as base64 strings."""
    images = []
    for filename in sorted(filenames):
        images.append(load_base64(os.path.join(directory, filename)))
    return images
