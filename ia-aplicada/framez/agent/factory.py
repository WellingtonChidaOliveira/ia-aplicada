from service.langgraph import start_graph


def CreateGraph(path: str, client):
    return start_graph(path, client)
