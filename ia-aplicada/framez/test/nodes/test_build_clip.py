import unittest
import http
from agent.nodes import buildClip
from unittest.mock import MagicMock, mock_open, patch
from pathlib import Path
from models.graph_message import GraphMessage


def mock_llm_router(*args, **kwargs):
    return http.HTTPStatus.BAD_REQUEST


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


@patch("agent.nodes.buildClip.LLMClient", MagicMock(return_value=MagicMock()))
class TestGeneratePhrase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mock_llm_client = MagicMock()
        self.mock_llm_client.llm_router = MagicMock(side_effect=mock_llm_router)

    def test_generate_phrase(self):
        resp = buildClip._gerar_frase(self.mock_llm_client)
        print(resp)
        self.assertIsInstance(resp, str)
        self.assertNotEqual(resp, "")
        self.assertNotEqual(resp, None)

    @patch("agent.nodes.buildClip.subprocess.run")
    @patch("agent.nodes.buildClip.os.path.getsize", return_value=1024)
    @patch("agent.nodes.buildClip.os.path.exists", return_value=True)
    @patch("agent.nodes.buildClip.os.remove")
    @patch("builtins.open", new_callable=mock_open)
    def test_render_clip_success(
        self, mock_file, mock_remove, mock_exists, mock_getsize, mock_subprocess
    ):
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        data = mockDataClip()
        result = buildClip._render_clip(**data)

        self.assertTrue(result["success"])
        self.assertEqual(result["error"], "")
        mock_subprocess.assert_called_once()
        mock_file.assert_called_once()

    @patch("agent.nodes.buildClip.subprocess.run")
    @patch("agent.nodes.buildClip.os.path.getsize", return_value=1024)
    @patch("agent.nodes.buildClip.os.path.exists", return_value=True)
    @patch("agent.nodes.buildClip.os.remove")
    @patch("builtins.open", new_callable=mock_open)
    def test_render_clip_fail(
        self, mock_file, mock_remove, mock_exists, mock_getsize, mock_subprocess
    ):
        mock_subprocess.return_value = MagicMock(returncode=1, stderr="")

        data = mockDataClip()
        result = buildClip._render_clip(**data)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], result["error"][-500:])
        mock_subprocess.assert_called_once()
        mock_file.assert_called_once()

    @patch("agent.nodes.buildClip.subprocess.run")
    @patch("agent.nodes.buildClip.os.path.getsize", return_value=1024)
    @patch("agent.nodes.buildClip.os.path.exists", return_value=True)
    @patch("agent.nodes.buildClip.os.remove")
    @patch("builtins.open", new_callable=mock_open)
    def test_render_clip_fail_file_not_exists(
        self, mock_file, mock_remove, mock_exists, mock_getsize, mock_subprocess
    ):
        mock_exists.return_value = False
        data = mockDataClip()
        result = buildClip._render_clip(**data)
        self.assertFalse(result["success"])
        mock_subprocess.assert_called_once()
        mock_file.assert_called_once()
        mock_remove.assert_called_once()

    @patch("agent.nodes.buildClip.os.makedirs")
    @patch("agent.nodes.buildClip.os.path.getsize", return_value=1024)
    @patch(
        "agent.nodes.buildClip._gerar_frase", return_value="Acredite no seu potencial!"
    )
    @patch(
        "agent.nodes.buildClip._render_clip",
        return_value={"success": True, "error": ""},
    )
    def test_build_clip_success(
        self, mock_render_clip, mock_gerar_frase, mock_getsize, mock_makedirs
    ):
        data = mockDataClip()
        result = buildClip.build_clip(
            state=GraphMessage(
                video_path=data["video_path"],
                segments=[
                    {
                        "start_time": data["start_time"],
                        "end_time": 20.0,
                        "reason": "",
                    }
                ],
            ),
            client=self.mock_llm_client,
        )
        self.assertTrue(result["success"])
        self.assertEqual(len(result["output_paths"]), 1)
        self.assertNotEqual(result["output_path"], "")
        self.assertEqual(result["error"], "")
        mock_render_clip.assert_called_once()
        mock_gerar_frase.assert_called_once()

    @patch("agent.nodes.buildClip.os.makedirs")
    @patch(
        "agent.nodes.buildClip._gerar_frase", return_value="Acredite no seu potencial!"
    )
    @patch(
        "agent.nodes.buildClip._render_clip",
        return_value={"success": False, "error": "ffmpeg error"},
    )
    def test_build_clip_fail(self, mock_render_clip, mock_gerar_frase, mock_makedirs):
        data = mockDataClip()
        result = buildClip.build_clip(
            state=GraphMessage(
                video_path=data["video_path"],
                segments=[
                    {
                        "start_time": data["start_time"],
                        "end_time": 20.0,
                        "reason": "",
                    }
                ],
            ),
            client=self.mock_llm_client,
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["output_paths"], [])
        self.assertEqual(result["output_path"], "")
        self.assertEqual(result["error"], "ffmpeg error")
        mock_render_clip.assert_called_once()
        mock_gerar_frase.assert_called_once()


if __name__ == "__main__":
    unittest.main()
