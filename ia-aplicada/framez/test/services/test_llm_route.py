import re
import unittest
from unittest.mock import MagicMock
from agent.prompts.v4.generate_phrase import generate_phrase_prompt
from service.llm_router import LLMClient
from utils.config import Config


class TestLLMClient(unittest.TestCase):
    def setUp(self):
        self.client = LLMClient()
        self.original_llm_router = self.client.llm_router
        self.client.llm_router = MagicMock()

    def tearDown(self):
        self.client.llm_router = self.original_llm_router

    def test_llm_router(self):
        # Configure o mock para retornar uma resposta específica
        self.client.llm_router.return_value = "Resposta de teste"

        # Teste básico
        response = self.client.llm_router("Olá", "gpt-3.5-turbo")
        self.assertEqual(response, "Resposta de teste")

        # Teste com opções
        response = self.client.llm_router("Olá", "gpt-3.5-turbo", {"temperature": 0.7})
        self.assertEqual(response, "Resposta de teste")

    def test_llm_router_options(self):
        # Teste com opções padrão (options=None)
        self.client.llm_router.return_value = "Resposta com default"
        self.client.llm_router("Teste")

        # Verifica se foi chamado com options={}
        self.client.llm_router.assert_called_with(
            "Teste", Config.MODEL_LLM_DECIDE, options={}
        )

    # def test_generate_phrase(self):
    #     # Teste de sucesso com frase (retorno não vazio)
    #     for _ in range(3):
    #         response = self.client.llm_router(
    #             prompt=generate_phrase_prompt(
    #                 "Expressão de foco e confiança, postura ereta indicando preparação intensa"
    #             ),
    #             model="openai/gpt-4o-mini",
    #             options={
    #                 "temperature": 1.2,
    #                 "top_p": 0.95,
    #                 "frequency_penalty": 1.0,
    #                 "presence_penalty": 0.8,
    #             },
    #         )

    #         print("Response: ", response)
    #         self.assertNotEqual(response, "")


if __name__ == "__main__":
    unittest.main()
