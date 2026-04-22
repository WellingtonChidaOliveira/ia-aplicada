from agent.nodes.get_video import VideoInfo
import json
import unittest
from unittest.mock import patch


class TestGetVideo(unittest.TestCase):
    def setUp(self):
        # Mocking ffprobe output for initialization
        with patch("agent.nodes.get_video.subprocess.run") as mock_run:
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
            self.video_info = VideoInfo("test_video.mp4")

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

        result = self.video_info.get_video_info()
        self.assertEqual(result["format"]["duration"], "60.0")

    def test_get_video_frames(self):
        # Mock GraphMessage state
        mock_state = {"video_path": "test_video.mp4"}

        result = self.video_info.get_video_frames(mock_state)
        self.assertTrue(result["success"])
        self.assertEqual(result["duration"], 60.0)
        self.assertEqual(result["fps"], 30.0)
        self.assertEqual(result["total_frames"], 1800)



if __name__ == "__main__":
    unittest.main()
