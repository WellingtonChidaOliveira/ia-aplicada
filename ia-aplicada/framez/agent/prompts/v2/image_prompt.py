def image_prompt(frame_num: int, total: int, timestamp_label: str):
    return f"""Analise o Frame {frame_num}/{total} ({timestamp_label}) de um vídeo de calistenia ou musculação.

Descreva a cena de forma técnica e objetiva (máximo 3 linhas):
1. Atividade: Exercício ou pose realizada.
2. Intensidade: Nível de esforço (Baixo, Médio, Alto) ou Pose/Transição.
3. Foco: Expressão e estado do atleta (ex: concentração, fadiga).

    Diretrizes Críticas:
        - Descreva APENAS o que está visível. Não deduza contextos externos.
        - Não use jargões excessivamente técnicos; prefira clareza visual.
        - Seja direto: Evite frases como "Eu vejo..." ou "Esta imagem mostra...".
        - Foque em elementos que indiquem um momento de "pico" ou alta qualidade estética.
    """
