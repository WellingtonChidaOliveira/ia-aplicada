import json
import unittest
from unittest.mock import patch, MagicMock
from agent.nodes.get_video import get_video_frames, get_video_info


class TestGetVideo(unittest.TestCase):
    @patch("agent.nodes.get_video.subprocess.run")
    def test_get_video_info(self, mock_run):
        # Mocking ffprobe output
        mock_run.return_value.stdout = json.dumps(
            {
                "format": {"duration": "60.0"},
                "streams": [
                    {
                        "codec_type": "video",
                        "avg_frame_rate": "30/1",
                        "nb_frames": "1800",
                    }
                ],
            }
        )

        result = get_video_info("test_video.mp4")
        self.assertEqual(result["format"]["duration"], "60.0")

    @patch("agent.nodes.get_video.get_video_info")
    def test_get_video_frames(self, mock_get_video_info):
        # Mocking get_video_info
        mock_get_video_info.return_value = {
            "format": {"duration": "60.0"},
            "streams": [
                {"codec_type": "video", "avg_frame_rate": "30/1", "nb_frames": "1800"}
            ],
        }

        result = get_video_frames("test_video.mp4")
        self.assertTrue(result["success"])
        self.assertEqual(result["duration"], 60.0)
        self.assertEqual(result["fps"], 30.0)
        self.assertEqual(result["total_frames"], 1800)


if __name__ == "__main__":
    unittest.main()
