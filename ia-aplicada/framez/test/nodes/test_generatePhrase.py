import unittest
from service.llmRouter import LLMClient
from agent.prompts.v1.generatePhrase import generate_phrase_prompt


class TestGeneratePhrase(unittest.TestCase):
    def setUp(self):
        self.client = LLMClient()

    def test_generate_phrase(self):
        rsp = self.client.llm_router(
            generate_phrase_prompt(),
            # options={
            #     "temperature": 1.2,
            # },
        )
        print(rsp)
        self.assertIsInstance(rsp, str)
        # self.assertLessEqual(len(rsp), 60)


if __name__ == "__main__":
    unittest.main()
