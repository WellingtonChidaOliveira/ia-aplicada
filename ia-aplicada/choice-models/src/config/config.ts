export type Config = {
  port: number;
  openRouterApiKey: string;
  models: string[];
};

export const loadConfig = () => {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (apiKey === null || apiKey == "") {
    throw new Error("OPENROUTER_API_KEY is not defined");
  }
  const config: Config = {
    port: Number(process.env.PORT) || 3000,
    openRouterApiKey: apiKey!,
    models: [
      "meta-llama/llama-4-scout-17b-16e-instruct",
      "qwen/qwen3.6-plus-preview:free",
      "x-ai/grok-4.1-fast:free",
    ],
  };

  return config;
};
