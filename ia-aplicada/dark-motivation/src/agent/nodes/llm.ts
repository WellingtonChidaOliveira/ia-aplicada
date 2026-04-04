import { AIMessage } from "@langchain/core/messages";
import { type GraphMessageState } from "../graph.ts";

export const llm = async (
  state: GraphMessageState,
): Promise<Partial<GraphMessageState>> => {
  return {
    messages: [new AIMessage({ content: "hello world" })],
    success: true,
  };
};
