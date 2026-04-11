from agent.prompts.v2.generatePhrase import generate_phrase_prompt
from models.GraphMessage import GraphMessage
from service.llmRouter import LLMClient


def generate_phrase(state: GraphMessage, client: LLMClient) -> GraphMessage:
    response = client.llm_router(
        generate_phrase_prompt(),
    )

    return {"motivation_phrase": response.strip()}
