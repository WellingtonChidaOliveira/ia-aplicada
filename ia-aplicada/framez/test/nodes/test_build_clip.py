import unittest
from agent.nodes.build_clip import BuildClip, _gerar_frase, _render_clip
from unittest.mock import MagicMock, mock_open, patch
from pathlib import Path
from models.graph_message import GraphMessage


def mock_llm_router(*args, **kwargs):
    return "A persistência é o caminho para o êxito."


def mockDataClip() -> dict:
    return {
        "video_path": str(Path.cwd() / "test" / "video_test" / "sample.mp4"),
        "start_time": 10.0,
        "duration": 20.0,
        "phrase": "Acredite no seu potencial!",
        "output_path": str(Path.cwd() / "output_test" / "test_clip_top1.mp4"),
        "output_dir": str(Path.cwd() / "output_test"),
        "base_timestamp": 1700000000,
        "rank": 1,
    }


@patch("agent.nodes.build_clip.LLMClient", MagicMock(return_value=MagicMock()))
class TestBuildClip(unittest.TestCase):
    def setUp(self):
        self.mock_llm_client = MagicMock()
        self.mock_llm_client.llm_router = MagicMock(side_effect=mock_llm_router)
        self.node = BuildClip(self.mock_llm_client)

    def test_generate_phrase(self):
        resp = _gerar_frase("pico de esforço", self.mock_llm_client)
        self.assertIsInstance(resp, str)
        self.assertNotEqual(resp, "")
        self.assertNotEqual(resp, None)

    @patch("agent.nodes.build_clip.subprocess.run")
    @patch("agent.nodes.build_clip.os.path.getsize", return_value=1024)
    @patch("agent.nodes.build_clip.os.path.exists", return_value=True)
    @patch("agent.nodes.build_clip.os.remove")
    @patch("builtins.open", new_callable=mock_open)
    def test_render_clip_success(
        self, mock_file, mock_remove, mock_exists, mock_getsize, mock_subprocess
    ):
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        data = mockDataClip()
        result = _render_clip(**data)

        self.assertTrue(result["success"])
        self.assertEqual(result["error"], "")
        mock_subprocess.assert_called_once()
        mock_file.assert_called_once()

    @patch("agent.nodes.build_clip.subprocess.run")
    @patch("agent.nodes.build_clip.os.path.getsize", return_value=1024)
    @patch("agent.nodes.build_clip.os.path.exists", return_value=True)
    @patch("agent.nodes.build_clip.os.remove")
    @patch("builtins.open", new_callable=mock_open)
    def test_render_clip_fail(
        self, mock_file, mock_remove, mock_exists, mock_getsize, mock_subprocess
    ):
        mock_subprocess.return_value = MagicMock(returncode=1, stderr="error message")

        data = mockDataClip()
        result = _render_clip(**data)

        self.assertFalse(result["success"])
        self.assertIn("error message", result["error"])
        mock_subprocess.assert_called_once()
        mock_file.assert_called_once()

    @patch("agent.nodes.build_clip.subprocess.run")
    @patch("agent.nodes.build_clip.os.path.getsize", return_value=1024)
    @patch("agent.nodes.build_clip.os.path.exists", return_value=True)
    @patch("agent.nodes.build_clip.os.remove")
    @patch("builtins.open", new_callable=mock_open)
    def test_render_clip_fail_file_not_exists(
        self, mock_file, mock_remove, mock_exists, mock_getsize, mock_subprocess
    ):
        mock_exists.return_value = False
        data = mockDataClip()
        result = _render_clip(**data)
        self.assertFalse(result["success"])
        mock_subprocess.assert_called_once()
        mock_file.assert_called_once()
        mock_remove.assert_called_once()

    @patch("agent.nodes.build_clip.os.makedirs")
    @patch("agent.nodes.build_clip.os.path.getsize", return_value=1024)
    @patch(
        "agent.nodes.build_clip._gerar_frase", return_value="Acredite no seu potencial!"
    )
    @patch(
        "agent.nodes.build_clip._render_clip",
        return_value={"success": True, "error": ""},
    )
    def test_build_clip_success(
        self, mock_render_clip, mock_gerar_frase, mock_getsize, mock_makedirs
    ):
        data = mockDataClip()
        result = self.node.build_clip(
            state=GraphMessage(
                video_path=data["video_path"],
                segments=[
                    {
                        "start_time": data["start_time"],
                        "end_time": 20.0,
                        "reason": "pico de esforço",
                    }
                ],
            )
        )
        self.assertTrue(result["success"])
        self.assertEqual(len(result["output_paths"]), 1)
        self.assertNotEqual(result["output_path"], "")
        self.assertEqual(result["error"], "")
        mock_render_clip.assert_called_once()
        mock_gerar_frase.assert_called_once()

    @patch("agent.nodes.build_clip.os.makedirs")
    @patch(
        "agent.nodes.build_clip._gerar_frase", return_value="Acredite no seu potencial!"
    )
    @patch(
        "agent.nodes.build_clip._render_clip",
        return_value={"success": False, "error": "ffmpeg error"},
    )
    def test_build_clip_fail(self, mock_render_clip, mock_gerar_frase, mock_makedirs):
        data = mockDataClip()
        result = self.node.build_clip(
            state=GraphMessage(
                video_path=data["video_path"],
                segments=[
                    {
                        "start_time": data["start_time"],
                        "end_time": 20.0,
                        "reason": "pico de esforço",
                    }
                ],
            )
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["output_paths"], [])
        self.assertEqual(result["output_path"], "")
        self.assertEqual(result["error"], "ffmpeg error")
        mock_render_clip.assert_called_once()
        mock_gerar_frase.assert_called_once()


if __name__ == "__main__":
    unittest.main()
