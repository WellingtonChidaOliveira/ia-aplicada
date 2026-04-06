import { StateGraph, START, END, MessagesZodMeta } from "@langchain/langgraph";
import { z } from "zod/v3";
import { phraseGenerator } from "./nodes/phraseGenerator.ts";
import { withLangGraph } from "@langchain/langgraph/zod";
import { BaseMessage } from "@langchain/core/messages";
import { LlmRouterService } from "../server/llmRouterService.ts";

const MessageState = z.object({
  messages: withLangGraph(z.custom<BaseMessage[]>(), MessagesZodMeta),
  datetime: z.string().optional(),
  error: z.string().optional(),
  success: z.boolean().default(false),
  failed: z.boolean().default(false),
});

export type GraphMessageState = z.infer<typeof MessageState>;

export function buildGraph(llmClient: LlmRouterService) {
  const graph = new StateGraph({
    stateSchema: MessageState,
  })
    .addNode("phraseGenerator", phraseGenerator(llmClient))
    .addEdge(START, "phraseGenerator")
    .addEdge("phraseGenerator", END);

  return graph.compile();
}
