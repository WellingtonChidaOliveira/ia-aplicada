import { StateGraph, START, END, MessagesZodMeta } from "@langchain/langgraph";
import { z } from "zod/v3";
import { llm } from "./nodes/llm.ts";
import { withLangGraph } from "@langchain/langgraph/zod";
import { BaseMessage } from "@langchain/core/messages";

const MessageState = z.object({
  messages: withLangGraph(z.custom<BaseMessage[]>(), MessagesZodMeta),
  datetime: z.string().optional(),
  error: z.string().optional(),
  success: z.boolean().default(false),
  failed: z.boolean().default(false),
});

export type GraphMessageState = z.infer<typeof MessageState>;

export function buildGraph() {
  const graph = new StateGraph({
    stateSchema: MessageState,
  })
    .addNode("llm", llm)
    .addEdge(START, "llm")
    .addEdge("llm", END);

  return graph.compile();
}
