from langgraph.graph import StateGraph, MessagesState, START, END


def GraphHandler():
    return start_graph()


def start_graph():
    graph = StateGraph(MessagesState)
    graph.add_node(mock_llm)
    graph.add_edge(START, "mock_llm")
    graph.add_edge("mock_llm", END)
    return graph.compile()


def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}
