from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.tools.video_tools import get_video_info, extract_frames
from agent.tools.analyse_tools import analyse_frames
from agent.tools.segment_tools import decide_segment
from agent.tools.phrase_tools import generate_phrase
from agent.tools.clip_tools import build_clip
from utils.config import Config


SYSTEM_PROMPT = """You are a video processing agent specialized in creating dark gym motivation clips.

Given a video path, you must execute these steps IN ORDER:
1. get_video_info — get video metadata
2. extract_frames — extract frames for analysis
3. analyse_frames — analyse frames with vision model
4. decide_segment — choose the best 20-45s segment
5. generate_phrase — generate a dark motivational phrase
6. build_clip — render the final clip

Always pass the exact outputs from each tool as inputs to the next tool.
Never skip steps. Never assume values — always use what the tools return.
When build_clip succeeds, report the output_path to the user."""


def create_agent():
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        base_url=Config.OPENROUTER_BASE_URL,
        api_key=Config.OPENROUTER_API_KEY,
        temperature=0,
    )

    tools = [
        get_video_info,
        extract_frames,
        analyse_frames,
        decide_segment,
        generate_phrase,
        build_clip,
    ]

    return create_react_agent(
        llm,
        tools,
        prompt=SYSTEM_PROMPT,
    )
