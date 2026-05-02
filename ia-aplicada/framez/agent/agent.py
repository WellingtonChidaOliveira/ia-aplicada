from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.tools.analyse_tools import analyse_video_gemini, parse_gemini_analysis
from agent.tools.video_tools import get_video_info
from agent.tools.phrase_tools import generate_phrase
from agent.tools.clip_tools import build_clip
from utils.config import Config


SYSTEM_PROMPT = """You are a video processing agent specialized in creating dark gym motivation clips.

Given a video path, execute these steps IN ORDER:
1. get_video_info — get video metadata
2. analyse_video_gemini — analyse full video
3. parse_gemini_analysis — pass gemini_analysis AND duration
4. generate_phrase — generate ONE dark motivational phrase
5. build_clip — call EXACTLY ONCE with video_path, segments_json and phrase

CRITICAL RULES:
- build_clip must be called EXACTLY ONCE — never retry, never call again
- If build_clip returns success=false, report the error and STOP
- phrase must come from generate_phrase output only
- After build_clip completes (success or failure), report result and STOP

Do not loop. Do not retry failed steps. Execute once and report."""


def create_agent():
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        base_url=Config.OPENROUTER_BASE_URL,
        api_key=Config.OPENROUTER_API_KEY,
        temperature=0,
    )

    tools = [
        get_video_info,
        analyse_video_gemini,
        parse_gemini_analysis,
        generate_phrase,
        build_clip,
    ]

    return create_react_agent(
        llm,
        tools,
        prompt=SYSTEM_PROMPT,
    )
