import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para permitir execução direta (F5)
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from unittest.mock import patch, MagicMock
from main import execute
from service.llmRouter import LLMClient
from models.GraphMessage import GraphMessage
from agent.factory import CreateGraph


class TestMain(unittest.TestCase):
    @patch("service.llmRouter.OpenAI")
    @patch("service.langgraph.get_video_frames")
    @patch("service.langgraph.extract_frames")
    @patch("service.langgraph.analyse_frames")
    @patch("service.langgraph.decide_segment")
    @patch("service.langgraph.build_clip")
    def test_main_success(
        self,
        mock_build,
        mock_decide,
        mock_analyse,
        mock_extract,
        mock_get_video,
        mock_openai,
    ):
        # Setup mock return values for each node
        video_path = Path("./videos/IMG_7877.mp4")

        mock_get_video.return_value = {
            "video_path": str(video_path),
            "duration": 60.0,
            "fps": 30.0,
            "success": True,
        }
        mock_extract.return_value = {
            "frames_dir": "./tmp/test_frames",
            "frames": ["frame_0001.jpg", "frame_0002.jpg"],
        }
        mock_analyse.return_value = {"analysis": "Test analysis content"}
        mock_decide.return_value = {
            "segments": [
                {
                    "rank": 1,
                    "start_time": 10.0,
                    "end_time": 40.0,
                    "reason": "Interesting part",
                }
            ]
        }
        mock_build.return_value = {
            "success": True,
            "output_paths": ["./output/test_clip.mp4"],
        }

        # Mock video path existence for the initial check in main.py
        with patch.object(Path, "exists", return_value=True):
            # Verify main() runs without exception
            try:
                execute(video_path)
            except Exception as e:
                self.fail(f"main() raised {type(e).__name__} unexpectedly: {e}")

            # Verify the mocks were called (implicitly verifying the graph flow)
            mock_get_video.assert_called()
            mock_extract.assert_called()
            mock_analyse.assert_called()

            # Test direct graph invocation to verify state accumulation
            client = LLMClient()
            graph = CreateGraph(str(video_path), client)
            initial_state = {"messages": [{"role": "user", "content": "start"}]}
            result = graph.invoke(initial_state)

            # Assertions on final state
            self.assertIsInstance(result, dict)
            self.assertIn("video_path", result)
            self.assertTrue(result.get("success", False))
            self.assertEqual(len(result["segments"]), 1)
            self.assertEqual(result["analysis"], "Test analysis content")

    def test_main_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            execute(Path("./non_existent_video.mp4"))


if __name__ == "__main__":
    unittest.main()
