import unittest
from unittest.mock import patch
from agent.nodes.extract_frames import ExtractFramesNode
from models.graph_message import GraphMessage


class TestExtractFrames(unittest.TestCase):
    def setUp(self):
        self.extract_frames = ExtractFramesNode()

    def test_calculate_max_frames_min(self):
        # Duration 30s -> 30/6 = 5. Min is 8.
        self.assertEqual(self.extract_frames.calculate_max_frames(30.0), 8)

    def test_calculate_max_frames_mid(self):
        # Duration 60s -> 60/6 = 10.
        self.assertEqual(self.extract_frames.calculate_max_frames(60.0), 10)

    def test_calculate_max_frames_max(self):
        # Duration 180s -> 180/6 = 30. Max is 20.
        self.assertEqual(self.extract_frames.calculate_max_frames(180.0), 20)

    @patch("agent.nodes.extract_frames.subprocess.run")
    @patch("agent.nodes.extract_frames.os.path.exists")
    @patch("agent.nodes.extract_frames.os.makedirs")
    def test_extract_frames_success(self, mock_makedirs, mock_exists, mock_run):
        # Mocking
        mock_exists.return_value = True
        state = GraphMessage({"duration": 60.0, "video_path": "test_video.mp4"})

        # Execution
        result = self.extract_frames.extract_frames(state)

        # Assertions
        # 60s / 6 = 10 frames
        max_frames = 10
        self.assertEqual(len(result["frames"]), max_frames)
        self.assertTrue(result["frames_dir"].startswith("./tmp/gym_frames_"))
        self.assertEqual(mock_run.call_count, max_frames)

        # Check if ffmpeg was called with correct arguments at least once
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("-i", cmd)
        self.assertIn("test_video.mp4", cmd)
        self.assertIn("-vframes", cmd)
        self.assertIn("1", cmd)

    @patch("agent.nodes.extract_frames.subprocess.run")
    @patch("agent.nodes.extract_frames.os.path.exists")
    @patch("agent.nodes.extract_frames.os.makedirs")
    def test_extract_frames_failure(self, mock_makedirs, mock_exists, mock_run):
        # Mocking: first 5 frames succeed, next 5 fail
        mock_exists.side_effect = [True] * 5 + [False] * 5
        state = GraphMessage({"duration": 60.0, "video_path": "test_video.mp4"})

        # Execution
        result = self.extract_frames.extract_frames(state)

        # Assertions
        self.assertEqual(len(result["frames"]), 5)
        self.assertEqual(mock_run.call_count, 10)


if __name__ == "__main__":
    unittest.main()
