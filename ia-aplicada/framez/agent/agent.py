from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# from langgraph.prebuilt import create_react_agent
from agent.tools.analyse_tools import analyse_video_local, parse_video_analysis
from agent.tools.clip_tools import build_clip
from agent.tools.phrase_tools import generate_phrase
from agent.tools.video_tools import get_video_info
from utils.config import Config

SYSTEM_PROMPT = """You are a video processing agent specialized in creating dark gym motivation clips.

Given a video path, execute these steps IN ORDER:
1. get_video_info — get video metadata
2. analyse_video_local — extract and analyse frames locally with Ollama vision
3. parse_video_analysis — pass analysis AND duration
4. generate_phrase — generate ONE dark motivational phrase (no arguments)
5. build_clip — call ONCE with video_path, segments_json, phrase, color_grade_json

Use parse_video_analysis.segments_json as build_clip.segments_json.
Use parse_video_analysis.color_grade_json as build_clip.color_grade_json.
Use generate_phrase.phrase as build_clip.phrase.

CRITICAL: build_clip must be called EXACTLY ONCE.
CRITICAL: phrase must come from generate_phrase output only.
When done, report the output_paths."""


def agent():
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        base_url=Config.OPENROUTER_BASE_URL,
        api_key=Config.OPENROUTER_API_KEY,
        temperature=1.1,
    )

    tools = [
        get_video_info,
        analyse_video_local,
        parse_video_analysis,
        generate_phrase,
        build_clip,
    ]

    return create_agent(
        llm,
        tools,
        system_prompt=SYSTEM_PROMPT,
    )
