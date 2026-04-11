def decide_prompt(duration: float, analysis: str, frames_count: int):
    prompt = f"""Você analisou {frames_count} frames de um vídeo de treino de musculação com duração total de {duration:.1f} segundos.

            Aqui está a análise de cada frame:

            {analysis}

            Com base nessa análise, escolha o melhor trecho para um clipe de academia estilo TikTok.
            Critérios: maior intensidade de esforço, boa expressão do atleta, qualidade visual.
            O trecho deve ter entre 20 e 45 segundos.
            Os timestamps disponíveis vão de 2.00s até {duration - 2:.1f}s.

            Responda APENAS com JSON válido, sem texto antes ou depois:
            {{
            "start_time": <float>,
            "end_time": <float>,
            "reason": "<motivo em uma frase>"
            }}"""

    return prompt
