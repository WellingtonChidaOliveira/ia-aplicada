import { buildGraph } from "./graph.ts";
import { LlmRouterService } from "../server/llmRouterService.ts";
import { config } from "../config/config.ts";

export function createGraph() {
  const llmClient = new LlmRouterService(config);
  return buildGraph(llmClient);
}

export const graph = async () => {
  return createGraph();
};
