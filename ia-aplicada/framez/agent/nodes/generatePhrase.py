from agent.prompts.v2.generatePhrase import generate_phrase_prompt
from models.GraphMessage import GraphMessage
from service.llmRouter import LLMClient
from config.config import Config


def generate_phrase(state: GraphMessage, client: LLMClient) -> GraphMessage:
    response = client.llm_router(
        generate_phrase_prompt(),
        model=Config.MODEL_LLM_PHRASE,
    )

    return {"motivation_phrase": response.strip()}
