from pathlib import Path

from agent.agent import create_agent


class AgentFactory:
    def __init__(self, path: str | None = None):
        self.agent = create_agent()
        self.path = path

    def start_service(self):
        print("Welcome to framez")
        if self.path is None:
            self.path = input("Enter the path to the video: ")

        full_path = Path.cwd() / "videos" / self.path
        if not full_path.exists():
            print(f"Video not found: {full_path}")
            return

        print(f"Processing: {full_path}")

        result = self.agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Process this video and create a dark gym motivation clip: {full_path}",
                    }
                ]
            }
        )

        # última mensagem do agente é o resultado final
        final_message = result["messages"][-1].content
        print(f"\nResult: {final_message}")


# Top-level factory for LangGraph API/Studio.
# Must accept NO arguments (or only RunnableConfig) — the server uses
# Python inspect to validate the signature and rejects anything else.
# path and client are fetched lazily inside the graph nodes from the state.
# def CreateGraph():
#     client = LLMClient()
#     video_path = str(Path("./videos/tr.mp4"))
#     video_tools = HandleVideoTools()
#     extract_frames = ExtractFramesNode()
#     analyse_frames = AnalyseFrameNode()
#     decide_segment = DecideSegment(client)
#     build_clip = BuildClip(client)

#     return start_graph(
#         video_tools=video_tools,
#         extract_frames=extract_frames,
#         analyse_frames=analyse_frames,
#         decide_segment=decide_segment,
#         build_clip=build_clip,
#     )
