import unittest
from unittest.mock import MagicMock
from models.GraphMessage import GraphMessage
from agent.nodes.decideSegment import decide_segment


def mock_state():
    return GraphMessage(
        {
            "duration": 100.0,
            "analysis": "analysis",
            "frames": [],
            "messages": [],
        }
    )


class TestDecideSegment(unittest.TestCase):
    def setUp(self):
        self.mock_llm_client = MagicMock()

    def test_decide_segment_valid_response(self):
        state = mock_state()
        response = self.mock_llm_client.llm_router.return_value
        response.strip.return_value = '{"trechos": [{"rank": 1, "start_time": 0.0, "end_time": 30.0, "reason": "reason"}]}'
        result = decide_segment(state, self.mock_llm_client)
        self.assertEqual(
            result["segments"],
            [
                {"rank": 1, "start_time": 0.0, "end_time": 30.0, "reason": "reason"},
                {
                    "rank": 2,
                    "start_time": 25.0,
                    "end_time": 55.0,
                    "reason": "fallback automático",
                },
                {
                    "rank": 3,
                    "start_time": 50.0,
                    "end_time": 80.0,
                    "reason": "fallback automático",
                },
            ],
        )

    def test_decide_segment_connection_error(self):
        state = mock_state()
        self.mock_llm_client.llm_router.side_effect = "Connection error"
        result = decide_segment(state, self.mock_llm_client)
        self.assertEqual(len(result["segments"]), 3)

    def test_decide_segment_more_than_3_segments(self):
        state = mock_state()
        response = self.mock_llm_client.llm_router.return_value
        response.strip.return_value = '{"trechos": [{"rank": 1, "start_time": 0.0, "end_time": 30.0, "reason": "reason"}, {"rank": 2, "start_time": 30.0, "end_time": 60.0, "reason": "reason"}, {"rank": 3, "start_time": 60.0, "end_time": 90.0, "reason": "reason"}, {"rank": 4, "start_time": 90.0, "end_time": 120.0, "reason": "reason"}]}'
        result = decide_segment(state, self.mock_llm_client)
        self.assertEqual(len(result["segments"]), 3)
