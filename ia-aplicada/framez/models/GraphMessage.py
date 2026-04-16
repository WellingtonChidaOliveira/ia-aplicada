from langgraph.graph import MessagesState


class GraphMessage(MessagesState):
    datetime: str
    video_path: str
    success: bool
    error: str
    attempt: int
    # video_info: dict
    duration: float
    fps: float
    total_frames: int = 0
    frames_dir: str = ""
    frames: list[str] = []
    analysis: str = ""
    # top-3 segments returned by the decide node
    segments: list[dict] = []
    # legacy single-segment fields (kept for compatibility)
    start_time: float = 0.0
    end_time: float = 0.0
    motivation_phrase: str = ""
    output_path: str = ""
    # all generated clip paths
    output_paths: list[str] = []
