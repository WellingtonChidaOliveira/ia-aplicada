import unittest
from unittest.mock import MagicMock, mock_open, patch
from models.graph_message import GraphMessage
from agent.nodes.analyse_frame import (
    load_base64,
    analyse_frame,
    analyse_frames,
    UNAVAILABLE_LABEL,
    MIN_CONTENT_LENGTH,
)


def mock_state(frames=None, frames_dir="/fake/dir") -> GraphMessage:
    return GraphMessage(
        {
            "duration": 100.0,
            "analysis": "",
            "frames": frames or ["frame_0001_t006.25.jpg", "frame_0002_t012.50.jpg"],
            "frames_dir": frames_dir,
            "messages": [],
        }
    )


class TestLoadBase64(unittest.TestCase):
    @patch("builtins.open", mock_open(read_data=b"fake_image_bytes"))
    def test_returns_base64_string(self):
        result = load_base64("/fake/path/frame.jpg")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_raises_when_file_not_found(self, _mock_file):
        with self.assertRaises(FileNotFoundError):
            load_base64("/nonexistent/frame.jpg")


class TestAnalyseFrame(unittest.TestCase):
    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.send_image_ollama")
    @patch("agent.nodes.analyse_frame.load_base64", return_value="base64data")
    def test_returns_content_on_success(self, _mock_b64, mock_ollama, mock_sleep):
        mock_response = MagicMock()
        mock_response.message.content = "A" * MIN_CONTENT_LENGTH
        mock_ollama.return_value = mock_response

        result = analyse_frame("/fake/frame.jpg", "frame_0001_t006.25.jpg", 1, 10)

        self.assertEqual(result, "A" * MIN_CONTENT_LENGTH)
        mock_ollama.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.send_image_ollama")
    @patch("agent.nodes.analyse_frame.load_base64", return_value="base64data")
    def test_retries_when_content_too_short(self, _mock_b64, mock_ollama, mock_sleep):
        short_response = MagicMock()
        short_response.message.content = "short"

        good_response = MagicMock()
        good_response.message.content = "B" * MIN_CONTENT_LENGTH

        mock_ollama.side_effect = [short_response, good_response]

        result = analyse_frame("/fake/frame.jpg", "frame_0001_t006.25.jpg", 1, 10)

        self.assertEqual(result, "B" * MIN_CONTENT_LENGTH)
        self.assertEqual(mock_ollama.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.send_image_ollama")
    @patch("agent.nodes.analyse_frame.load_base64", return_value="base64data")
    def test_returns_unavailable_when_all_retries_exhausted(
        self, _mock_b64, mock_ollama, mock_sleep
    ):
        mock_response = MagicMock()
        mock_response.message.content = "tiny"
        mock_ollama.return_value = mock_response

        result = analyse_frame(
            "/fake/frame.jpg", "frame_0001_t006.25.jpg", 1, 10, retries=3
        )

        self.assertEqual(result, UNAVAILABLE_LABEL)
        self.assertEqual(mock_ollama.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.send_image_ollama")
    @patch("agent.nodes.analyse_frame.load_base64", return_value="base64data")
    def test_returns_unavailable_when_ollama_raises(
        self, _mock_b64, mock_ollama, mock_sleep
    ):
        mock_ollama.side_effect = Exception("Connection error")

        result = analyse_frame(
            "/fake/frame.jpg", "frame_0001_t006.25.jpg", 1, 10, retries=2
        )

        self.assertEqual(result, UNAVAILABLE_LABEL)
        self.assertEqual(mock_ollama.call_count, 2)

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.send_image_ollama")
    @patch("agent.nodes.analyse_frame.load_base64", return_value="base64data")
    def test_falls_back_to_frame_number_when_timestamp_not_parseable(
        self, _mock_b64, mock_ollama, mock_sleep
    ):
        mock_response = MagicMock()
        mock_response.message.content = "C" * MIN_CONTENT_LENGTH
        mock_ollama.return_value = mock_response

        # frame name without "_t" pattern should use fallback label
        result = analyse_frame("/fake/frame.jpg", "no_timestamp_frame.jpg", 3, 10)

        self.assertEqual(result, "C" * MIN_CONTENT_LENGTH)
        mock_ollama.assert_called_once()

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.send_image_ollama")
    @patch("agent.nodes.analyse_frame.load_base64", return_value="base64data")
    def test_parses_timestamp_from_frame_name(self, _mock_b64, mock_ollama, mock_sleep):
        mock_response = MagicMock()
        mock_response.message.content = "D" * MIN_CONTENT_LENGTH
        mock_ollama.return_value = mock_response

        result = analyse_frame("/fake/frame.jpg", "frame_0001_t006.25.jpg", 1, 10)

        self.assertEqual(result, "D" * MIN_CONTENT_LENGTH)
        call_args = mock_ollama.call_args
        # second argument is the prompt; it should contain the formatted timestamp
        prompt_arg = call_args[0][1]
        self.assertIn("t=6.25s", prompt_arg)


class TestAnalyseFrames(unittest.TestCase):
    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch(
        "agent.nodes.analyse_frame.analyse_frame",
        return_value="Athlete performing squat with high effort.",
    )
    def test_returns_analysis_for_all_frames(self, mock_analyse, mock_sleep):
        state = mock_state(frames=["frame_0001_t006.25.jpg", "frame_0002_t012.50.jpg"])

        result = analyse_frames(state)

        self.assertIn("analysis", result)
        self.assertEqual(mock_analyse.call_count, 2)
        self.assertIn("frame_0001_t006.25.jpg", result["analysis"])
        self.assertIn("frame_0002_t012.50.jpg", result["analysis"])

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch(
        "agent.nodes.analyse_frame.analyse_frame",
        return_value="Athlete performing squat with high effort.",
    )
    def test_frames_are_sorted(self, mock_analyse, mock_sleep):
        # provide frames out of order to ensure sorting
        state = mock_state(frames=["frame_0003_t018.75.jpg", "frame_0001_t006.25.jpg"])

        analyse_frames(state)

        first_call_frame_name = mock_analyse.call_args_list[0][0][1]
        self.assertEqual(first_call_frame_name, "frame_0001_t006.25.jpg")

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.analyse_frame", return_value=UNAVAILABLE_LABEL)
    def test_handles_unavailable_analysis(self, mock_analyse, mock_sleep):
        state = mock_state(frames=["frame_0001_t006.25.jpg"])

        result = analyse_frames(state)

        self.assertIn(UNAVAILABLE_LABEL, result["analysis"])

    @patch("agent.nodes.analyse_frame.time.sleep")
    @patch("agent.nodes.analyse_frame.analyse_frame")
    def test_returns_empty_analysis_for_no_frames(self, mock_analyse, mock_sleep):
        state = MagicMock()
        state.get.side_effect = lambda key: [] if key == "frames" else "/fake/dir"

        result = analyse_frames(state)

        self.assertEqual(result["analysis"], "")
        mock_analyse.assert_not_called()


if __name__ == "__main__":
    unittest.main()
