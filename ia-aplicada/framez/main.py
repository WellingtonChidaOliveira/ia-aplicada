from agent.factory import CreateGraph

graph = CreateGraph()
graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
