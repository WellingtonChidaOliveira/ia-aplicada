import os
from langchain_core.messages import AIMessage
from models.GraphMessage import GraphMessage


def mock_llm(state: GraphMessage):
    path = state.get("output_path")
    if os.path.exists(path):
        return {"messages": [AIMessage(content=path)]}
    else:
        return {"messages": [AIMessage(content="Erro ao gerar clipe")]}
