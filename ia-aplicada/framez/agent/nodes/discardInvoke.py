from langchain_core.messages import AIMessage
from models.GraphMessage import GraphMessage


def discard_invoke(state: GraphMessage) -> GraphMessage:
    print("Discarding invoke")
    messages = state.get("messages") or []
    if messages and messages[-1].content == "skip":
        return {"messages": [AIMessage(content="skip message")]}

    return {"messages": messages}
