from agent.nodes.discard_invoke import discard_invoke
from langgraph.graph import StateGraph, START, END
from models.graph_message import GraphMessage
from agent.nodes.decide_segment import decide_segment
from agent.nodes.build_clip import build_clip
from service.llm_router import LLMClient
from agent.nodes.get_video import VideoInfo
from agent.nodes.extract_frames import ExtractFramesNode
from agent.nodes.analyse_frame import AnalyseFrameNode


def start_graph(
    path: str | None = None,
    client: LLMClient | None = None,
    video_info: VideoInfo | None = None,
    extract_frames: ExtractFramesNode | None = None,
    analyse_frames: AnalyseFrameNode | None = None,
):
    graph = StateGraph(GraphMessage)

    def decide_segment_node(state: GraphMessage):
        c = client or LLMClient()
        return decide_segment(state, c)

    def build_clip_node(state: GraphMessage):
        c = client or LLMClient()
        return build_clip(state, c)

    graph.add_node("discard_invoke", discard_invoke)
    graph.add_node("get_video_frames", video_info.get_video_frames)
    graph.add_node("extract_frames", extract_frames.extract_frames)
    graph.add_node("analyse_frames", analyse_frames.analyse_frames)
    graph.add_node("decide_segment", decide_segment_node)
    graph.add_node("build_clip", build_clip_node)

    graph.add_conditional_edges(
        "discard_invoke",
        lambda state: (
            "skip"
            if (state.get("messages") or [])
            and state.get("messages")[-1].content == "skip message"
            else "continue"
        ),
        {
            "skip": END,
            "continue": "get_video_frames",
        },
    )

    graph.add_edge(START, "discard_invoke")
    graph.add_edge("get_video_frames", "extract_frames")
    graph.add_edge("extract_frames", "analyse_frames")
    graph.add_edge("analyse_frames", "decide_segment")
    graph.add_edge("decide_segment", "build_clip")
    graph.add_edge("build_clip", END)

    return graph.compile()
