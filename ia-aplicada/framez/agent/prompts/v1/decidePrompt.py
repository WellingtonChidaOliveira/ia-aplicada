def decide_prompt(duration: float, analysis: str, frames_count: int):
    prompt = f"""Você é um curador de conteúdo de alta performance para redes sociais.

            Sua função é analisar os frames de um vídeo de treino e selecionar os 3 MELHORES TRECHOS, do mais impactante ao menos impactante, para gerar clipes curtos (estilo TikTok/Reels).

            Você deve priorizar:
            - Pico de esforço muscular
            - Expressão facial de intensidade/foco
            - Boa qualidade de imagem
            - Movimento fluido e potente
            - Evitar partes paradas, confusas ou de baixa qualidade

            Cada trecho deve ter entre 20 e 45 segundos.
            Os timestamps disponíveis vão de 2.00s até {duration - 2:.1f}s.

            Analise os frames abaixo:
            {analysis}

            Com base nessa análise, escolha os 3 MELHORES TRECHOS para clipes de academia estilo TikTok.
            Critérios: maior intensidade de esforço, boa expressão do atleta, qualidade visual.
            Ordene-os do MELHOR (top1) ao TERCEIRO MELHOR (top3).
            Os trechos não precisam ser contíguos nem se sobrepor.
            Cada trecho deve ter entre 20 e 45 segundos.
            Os timestamps disponíveis vão de 2.00s até {duration - 2:.1f}s.

            Responda APENAS com JSON válido, sem texto antes ou depois.
            O array "trechos" deve conter EXATAMENTE 3 objetos:
            {{
                "trechos": [
                    {{
                        "rank": 1,
                        "start_time": <float>,
                        "end_time": <float>,
                        "reason": "<motivo em uma frase>"
                    }},
                    {{
                        "rank": 2,
                        "start_time": <float>,
                        "end_time": <float>,
                        "reason": "<motivo em uma frase>"
                    }},
                    {{
                        "rank": 3,
                        "start_time": <float>,
                        "end_time": <float>,
                        "reason": "<motivo em uma frase>"
                    }}
                ]
            }}"""

    return prompt

