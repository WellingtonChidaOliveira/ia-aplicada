def decide_prompt(duration: float, analysis: str):
    prompt = f"""Você é um Curador de Conteúdo Especialista em Redes Sociais (TikTok/Reels/Shorts).

Sua tarefa é analisar as descrições dos frames de um vídeo de treino e selecionar os 3 MELHORES TRECHOS para gerar clipes impactantes.

CRITÉRIOS DE SELEÇÃO:
- Priorize: Pico de esforço muscular, expressões de foco/intensidade e movimentos fluidos.
- Evite: Partes paradas, enquadramentos ruins, desfoque ou transições confusas.
- Impacto: O Top 1 deve ser o momento mais impressionante do vídeo.

REGRAS TÉCNICAS:
- Selecione EXATAMENTE 3 trechos.
- Duração de cada trecho: Entre 20 e 45 segundos.
- Intervalo permitido: De 2.0s até {duration - 2.0:.1f}s.
- Os trechos podem ser independentes (não precisam ser contínuos).

DADOS DA ANÁLISE DOS FRAMES:
{analysis}

INSTRUÇÕES DE SAÍDA:
Responda APENAS com um objeto JSON válido, sem nenhum texto adicional.
Formato esperado:
{{
    "trechos": [
        {{
            "rank": 1,
            "start_time": <float>,
            "end_time": <float>,
            "reason": "<explicação curta do porquê este momento foi escolhido>"
        }},
        {{
            "rank": 2,
            "start_time": <float>,
            "end_time": <float>,
            "reason": "<destaque deste trecho>"
        }},
        {{
            "rank": 3,
            "start_time": <float>,
            "end_time": <float>,
            "reason": "<destaque deste trecho>"
        }}
    ]
}}"""
    return prompt
