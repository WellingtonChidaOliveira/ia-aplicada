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
    frames_dir: str = ""
    frames: list[str] = []
    analysis: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    motivation_phrase: str = ""
    output_path: str = ""
