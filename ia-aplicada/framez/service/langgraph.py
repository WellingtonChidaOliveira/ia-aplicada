from langgraph.graph import StateGraph, START, END
from models.GraphMessage import GraphMessage
from agent.nodes.getVideo import get_video_frames
from agent.nodes.extractFrames import extract_frames
from agent.nodes.analyseFrame import analyse_frames
from agent.nodes.decideSegment import decide_segment
from agent.nodes.generatePhrase import generate_phrase
from agent.nodes.buildClip import build_clip


def start_graph(path: str):
    graph = StateGraph(GraphMessage)

    def get_video_info_node(state: GraphMessage):
        return get_video_frames(path)

    graph.add_node("get_video_frames", get_video_info_node)
    graph.add_node("extract_frames", lambda s: extract_frames(s))
    graph.add_node("analyse_frames", lambda s: analyse_frames(s))
    graph.add_node("decide_segment", lambda s: decide_segment(s))
    graph.add_node("generate_phrase", lambda s: generate_phrase(s))
    graph.add_node("build_clip", lambda s: build_clip(s))

    graph.add_edge(START, "get_video_frames")
    graph.add_edge("get_video_frames", "extract_frames")
    graph.add_edge("extract_frames", "analyse_frames")
    graph.add_edge("analyse_frames", "decide_segment")
    graph.add_edge("decide_segment", "generate_phrase")
    graph.add_edge("generate_phrase", "build_clip")
    graph.add_edge("build_clip", END)

    return graph.compile()
