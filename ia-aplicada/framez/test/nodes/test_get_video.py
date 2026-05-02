import json
import unittest
from unittest.mock import patch
from agent.tools.video_tools import HandleVideoTools

class TestGetVideo(unittest.TestCase):
    def setUp(self):
        self.tools = HandleVideoTools()

    @patch("agent.tools.video_tools.subprocess.run")
    def test_get_video_info(self, mock_run):
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
        
        mock_state = {"video_path": "test_video.mp4"}
        result = self.tools.get_video_info.invoke({"state": mock_state})
        
        self.assertTrue(result["success"])
        self.assertEqual(result["duration"], 60.0)
        self.assertEqual(result["fps"], 30.0)
        self.assertEqual(result["total_frames"], 1800)

if __name__ == "__main__":
    unittest.main()
