from agent.nodes.discardInvoke import discard_invoke
from langgraph.graph import StateGraph, START, END
from models.GraphMessage import GraphMessage
from agent.nodes.getVideo import get_video_frames
from agent.nodes.extractFrames import extract_frames
from agent.nodes.analyseFrame import analyse_frames
from agent.nodes.decideSegment import decide_segment
from agent.nodes.buildClip import build_clip
from service.llmRouter import LLMClient


def start_graph(path: str, client: LLMClient):
    graph = StateGraph(GraphMessage)

    def get_video_info_node(state: GraphMessage):
        return get_video_frames(path)

    def decide_segment_node(state: GraphMessage):
        return decide_segment(state, client)

    def build_clip_node(state: GraphMessage):
        return build_clip(state, client)

    graph.add_node("discard_invoke", discard_invoke)
    graph.add_node("get_video_frames", get_video_info_node)
    graph.add_node("extract_frames", extract_frames)
    graph.add_node("analyse_frames", analyse_frames)
    graph.add_node("decide_segment", decide_segment_node)
    graph.add_node("build_clip", build_clip_node)

    graph.add_conditional_edges(
        "discard_invoke",
        lambda state: (
            "skip"
            if state.get("messages")[-1].content == "skip message"
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

