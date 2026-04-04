import { buildGraph } from "./graph.ts";

export function createGraph() {
  return buildGraph();
}

export const graph = async () => {
  return createGraph();
};
