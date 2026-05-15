# Framez

Framez is a Python video-processing agent that turns a gym video into short, dark cinematic motivation clips.

The application uses a LangChain tool-calling agent to inspect a video, choose the strongest segments, generate a motivational phrase, and render vertical clips with FFmpeg filters, color grading, blur, vignette, and text overlay.

This README is intentionally detailed because it is meant to be read by another coding agent before changing the app. It describes the current executable flow, the expected contracts between tools, and the known mismatches in the codebase.

## What It Does

Given a video file in the `videos/` directory, Framez runs this workflow:

1. Reads video metadata with `ffprobe`.
2. Extracts a small set of frames from the video.
3. Sends those frames to a local vision model through Ollama.
4. Asks the model to propose the best segments for short motivation clips.
5. Parses and validates the selected segments.
6. Generates one dark motivational phrase.
7. Builds one or more final clips with FFmpeg.

Generated videos are saved in the `output/` directory.

## Project Structure

```text
.
|-- main.py                     # CLI entrypoint
|-- factory.py                  # Creates the agent, asks for a video path, and invokes it
|-- agent/
|   |-- agent.py                # LangChain agent definition, tools, model, and system prompt
|   |-- prompts/                # Prompt versions for phrase and analysis logic
|   `-- tools/
|       |-- video_tools.py      # ffprobe metadata and an auxiliary frame extraction helper
|       |-- analyse_tools.py    # Local frame extraction, Ollama vision analysis, and JSON parsing
|       |-- phrase_tools.py     # Phrase generation through OpenRouter/Ollama
|       |-- clip_tools.py       # Final clip orchestration
|       `-- ffmpeg_tools.py     # FFmpeg command generation and rendering
|-- service/
|   |-- llm_router.py           # OpenRouter client wrapper
|   `-- ollama.py               # Local Ollama image/text helpers
|-- utils/
|   `-- config.py               # Environment-based configuration
|-- videos/                     # Input videos
|-- output/                     # Generated clips
`-- test/                       # Existing tests
```

## Requirements

- Python 3.11+
- FFmpeg and FFprobe installed and available in your shell
- An OpenRouter API key
- Ollama for local frame/image analysis
- Optional: Gemini API key, only if you re-enable a Gemini analysis path later
- Optional: Ollama with `llama3.1:latest`, used as a phrase fallback

Install Python dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The code also imports packages such as `python-dotenv`, `openai`, `langchain-openai`, `langchain`, and `ollama`. If they are not already installed in your environment, install them before running the app. `requirements.txt` may not currently list every import used by the code.

## Environment Variables

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_key
```

`OPENROUTER_API_KEY` is required for the main agent and OpenRouter LLM calls. `GEMINI_API_KEY` exists in config but is not used by the current active flow.

## Running The App

Place an input video inside `videos/`, for example:

```text
videos/workout.mp4
```

Run:

```bash
python main.py
```

When prompted, enter only the filename:

```text
workout.mp4
```

Framez will resolve it as:

```text
videos/workout.mp4
```

The rendered files are written to `output/` with names like:

```text
output/1700000000_workout_top1.mp4
output/1700000000_workout_top2.mp4
output/1700000000_workout_top3.mp4
```

## Current Agent Flow

The active agent is defined in `agent/agent.py`.

It uses `ChatOpenAI` with OpenRouter:

```python
model="openai/gpt-4o-mini"
base_url="https://openrouter.ai/api/v1"
```

The system prompt asks the model to run the tools in this order:

1. `get_video_info`
2. `analyse_video_local`
3. `parse_video_analysis`
4. `generate_phrase`
5. `build_clip`

`build_clip` is intentionally called once and receives all parsed segments. The tool then loops through the segments and may render `top1`, `top2`, and `top3` outputs in that single call.

Important implementation detail: this is a LangChain agent driven by a system prompt, not a deterministic hand-written pipeline. The code relies on the model following the tool order and passing compatible tool arguments.

## Video Rendering

Rendering is handled by FFmpeg in `agent/tools/ffmpeg_tools.py`.

The generated clips are vertical `1080x1920` videos and include:

- Cropping and scaling for short-form video
- Dark, desaturated color grading
- Blue/teal color balance
- High contrast and vignette
- Intro blur/fade transition
- Centered text overlay using the configured font
- AAC audio passthrough when audio exists

The default font path is currently hardcoded:

```python
/home/wchida/.local/share/fonts/BebasNeue-Regular.ttf
```

Update `FONT_PATH` in `agent/tools/ffmpeg_tools.py` if that font does not exist on your machine.

## Detailed Runtime Flow For Agents

### 1. CLI Entrypoint

`main.py` only does this:

```python
from factory import AgentFactory

if __name__ == "__main__":
    AgentFactory().start_service()
```

The application behavior starts in `AgentFactory.start_service()`:

1. Prints `Welcome to framez`.
2. Reads a filename from `input()` if no path was provided to the factory constructor.
3. Resolves the video as `Path.cwd() / "videos" / self.path`.
4. Stops early if the file does not exist.
5. Invokes the LangChain agent with a single user message: `Process this video: <full_path>`.
6. Prints the final message returned by the agent.

The user should provide only the file name, not an absolute path, unless the factory code is changed.

### 2. Video Metadata

`get_video_info` lives in `agent/tools/video_tools.py`.

It runs `ffprobe` and returns:

```json
{
  "datetime": "ISO timestamp",
  "video_path": "path received by the tool",
  "success": true,
  "error": "",
  "attempt": 1,
  "duration": 123.45,
  "fps": 29.97,
  "total_frames": 3700
}
```

The next tool needs `video_path` and `duration`.

### 3. Local Frame Analysis

`analyse_video_local` lives in `agent/tools/analyse_tools.py`.

It first calls `_extract_frames(video_path, duration)`, which:

- creates `./tmp/gym_frames_<pid>`;
- extracts frames from `2.0s` through `duration - 2.0s`;
- samples roughly one frame every 6 seconds;
- caps the sample between 8 and 12 frames;
- writes JPG files like `frame_0001_t0002.00.jpg`;
- scales each frame down to fit within `1280x720`;
- deletes the temporary frame directory in a `finally` block.

It then builds a single contact sheet image from the sampled frames and calls `_analyse_frames_local(frames_dir, frames, duration)`, which asks the configured local vision model to return strict JSON with:

- a short `analysis` of the visual content and lighting;
- a `color_grade` object;
- the top 3 recommended `segments`.

The default visual model is configured in `utils/config.py`:

```python
OLLAMA_VISION_MODEL = "qwen3-vl:8b"
```

The contact sheet is used because local VLMs are more stable with one comparison image than with many images in a single chat message. The prompt is tuned for TikTok/workout selection. It asks the model to prioritize sharp frames, clear athlete visibility, 9:16 crop suitability, peak effort or peak pose, useful composition, and lighting that can survive a dark cinematic grade.

If the contact-sheet response is not parseable JSON, the app falls back to scoring sampled frames individually with the same local vision model. It then builds segments around the highest-scoring frames before falling back to deterministic segments.

Expected model shape:

```json
{
  "analysis": "brief description of video content and lighting",
  "color_grade": {
    "brightness": -0.20,
    "contrast": 1.40,
    "saturation": 0.40,
    "gamma": 0.80,
    "teal_intensity": 0.18,
    "vignette_angle": "PI/4",
    "fontsize": 72,
    "text_y": "h*0.78",
    "blur_duration": 3.0,
    "rationale": "why this grade fits the source lighting"
  },
  "segments": [
    {"rank": 1, "start_time": 5.0, "end_time": 35.0, "reason": "..."},
    {"rank": 2, "start_time": 36.0, "end_time": 62.0, "reason": "..."},
    {"rank": 3, "start_time": 15.0, "end_time": 45.0, "reason": "..."}
  ]
}
```

If parsing the model response fails, `analyse_video_local` returns a deterministic fallback: three 30-second segments distributed across the video and a default Dark Knight-style grade.

### 4. Segment Parsing

`parse_video_analysis` also lives in `agent/tools/analyse_tools.py`.

It receives the raw `analysis` string and `duration`. It:

- strips markdown code fences such as JSON fenced blocks;
- finds the first JSON object in the response;
- parses the JSON;
- reads `segments`;
- detects normalized timestamps if all end times are near `0..1`;
- converts normalized timestamps to seconds when duration is known;
- filters out segments shorter than 15 seconds.

Current return shape:

```json
{
  "segments": [
    {"rank": 1, "start_time": 5.0, "end_time": 35.0, "reason": "..."}
  ],
  "segments_json": "[{\"rank\": 1, \"start_time\": 5.0, \"end_time\": 35.0, \"reason\": \"...\"}]",
  "color_grade": {
    "brightness": -0.20,
    "contrast": 1.40
  },
  "color_grade_json": "{\"brightness\": -0.20, \"contrast\": 1.40}",
  "analysis": "..."
}
```

The `segments_json` and `color_grade_json` fields are included specifically so the agent can pass ready-to-use string arguments to `build_clip`.

### 5. Phrase Generation

`generate_phrase` lives in `agent/tools/phrase_tools.py`.

It uses the prompt from `agent/prompts/v4/generate_phrase.py`, which asks for one short Portuguese phrase with a cold, heavy motivational tone. The requested phrase must be at most 12 words and contain no explanation.

The main path calls OpenRouter through `service/llm_router.py` using:

```text
Config.MODEL_LLM_PHRASE = "openai/gpt-4o-mini"
```

Fallback behavior:

1. If OpenRouter fails, call Ollama text generation with `Config.OLLAMA_TEXT_MODEL`.
2. If Ollama also fails, return `A persistência é o caminho para o êxito.`

Return shape:

```json
{"phrase": "..."}
```

### 6. Clip Rendering

`build_clip` lives in `agent/tools/clip_tools.py`.

Signature:

```python
build_clip(
    video_path: str,
    segments_json: str,
    phrase: str,
    color_grade_json: str = "{}",
) -> dict
```

It expects `segments_json` to be a JSON string containing a list of segment objects. For each segment it calculates:

```python
duration = end_time - start_time
```

Then it renders one file per segment:

```text
output/<timestamp>_<video_name>_top<rank>.mp4
```

The phrase is written into a temporary text file inside `output/`, wrapped at about 22 characters per line, and passed to FFmpeg's `drawtext` filter. The text file is removed after rendering.

The current TikTok-oriented encode settings live in `utils/config.py`:

```python
VIDEO_CRF = "18"
VIDEO_PRESET = "slow"
VIDEO_AUDIO_BITRATE = "192k"
```

These settings produce larger files than the previous fast/CRF 23 encode, but preserve more detail after the vertical crop and color grading.

If `color_grade_json` is empty or invalid, `build_clip` uses this fallback:

```json
{
  "brightness": -0.20,
  "contrast": 1.40,
  "saturation": 0.40,
  "gamma": 0.80,
  "teal_intensity": 0.18,
  "vignette_angle": "PI/4",
  "fontsize": 72,
  "text_y": "h*0.78",
  "blur_duration": 3.0
}
```

Final return shape:

```json
{
  "success": true,
  "output_paths": ["output/1700000000_workout_top1.mp4"],
  "output_path": "output/1700000000_workout_top1.mp4",
  "error": ""
}
```

## Expected Tool Contract

If an agent needs to bypass the autonomous tool-calling behavior and reason about the intended pipeline directly, the contract is:

```python
info = get_video_info(video_path)

analysis_result = analyse_video_local(
    video_path=info["video_path"],
    duration=info["duration"],
)

parsed = parse_video_analysis(
    analysis=analysis_result["analysis"],
    duration=info["duration"],
)

phrase_result = generate_phrase()

clip_result = build_clip(
    video_path=info["video_path"],
    segments_json=json.dumps(parsed["segments"]),
    phrase=phrase_result["phrase"],
    color_grade_json=json.dumps(parsed.get("color_grade", {})),
)
```

`parse_video_analysis` also returns `segments_json` and `color_grade_json`; those are the preferred values for the agent to pass into `build_clip`.

## Services

`service/llm_router.py` is a thin OpenAI-compatible client pointed at OpenRouter:

```python
OpenAI(
    base_url=Config.OPENROUTER_BASE_URL,
    api_key=Config.OPENROUTER_API_KEY,
)
```

`service/ollama.py` exposes:

- `send_image_ollama`, currently configured through `Config.OLLAMA_VISION_MODEL`;
- `send_text_ollama`, currently configured through `Config.OLLAMA_TEXT_MODEL`.

The default local vision model is `qwen3-vl:8b`.

## Notes About Video Analysis

The active path is `analyse_video_local`, not `analyse_video_gemini`. It extracts frames locally and sends them to Ollama. `GEMINI_API_KEY` remains in configuration, but Gemini is not part of the currently registered agent tools.

The parser accepts Gemini-style JSON and also detects normalized timestamps between `0` and `1`, converting them to seconds when the video duration is known.

## Tests

There are tests under `test/`, but several currently reference older modules such as `agent.nodes.*`, while the current app uses `agent.tools.*`. Those tests need to be updated before the full suite can run successfully.

When aligned, the intended command is:

```bash
python -m unittest discover -s test
```

## Known Issues And Maintenance Notes

These points are important for another agent before making changes:

1. `README.md` was untracked in the observed git status, so treat its previous contents as user work.
2. `langgraph.json` points to `./agent/factory.py:CreateGraph`, but that file/function is not present in the current tree.
3. The executable path today is `python main.py`, not LangGraph Studio/API.
4. `parse_video_analysis` returns both structured values and JSON-string values for `segments` and `color_grade`.
5. `FONT_PATH` in `agent/tools/ffmpeg_tools.py` is an absolute machine-specific path.
6. The active local vision model is `Config.OLLAMA_VISION_MODEL`, currently `qwen3-vl:8b`.
7. `utils.helper.load_base64_files` is used to load all extracted frame files as base64 before sending them to Ollama.
8. `requirements.txt` may be incomplete for the current imports.
9. `build_clip` runs the generated FFmpeg command with `shell=True`, so paths and quote escaping deserve care.
10. The app assumes input videos live under `videos/` and output can be written under `output/`.

## Recommended Stabilization Order

For future maintenance, fix these in this order:

1. Move `FONT_PATH` into config or environment.
2. Update `requirements.txt` for all active imports.
3. Update or remove the stale `langgraph.json`.
4. Refresh tests so they target `agent.tools.*` and the current CLI/agent flow.

## LangGraph

The repository includes `langgraph.json`, but the configured graph target points to:

```text
./agent/factory.py:CreateGraph
```

That file/function is not present in the current tree. The working entrypoint today is the CLI flow through `python main.py`.
