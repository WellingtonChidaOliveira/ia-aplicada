def image_prompt(frame_num: int, total: int, timestamp_label: str):
    return f"""Analise o Frame {frame_num}/{total} ({timestamp_label}) de um vídeo de calistenia ou musculação.

    Sua tarefa é descrever a cena de forma técnica e objetiva em até 3 linhas, focando em:
    1. Atividade: Exercício específico, movimento ou pose sendo realizada.
    2. Intensidade: Nível de esforço visível (Baixo, Médio, Alto) ou se é uma Pose/Transição.
    3. Expressão e Foco: Estado do atleta (ex: concentração total, fadiga extrema, satisfação).

    Diretrizes Críticas:
        - Descreva APENAS o que está visível. Não deduza contextos externos.
        - Não use jargões excessivamente técnicos; prefira clareza visual.
        - Seja direto: Evite frases como "Eu vejo..." ou "Esta imagem mostra...".
        - Foque em elementos que indiquem um momento de "pico" ou alta qualidade estética.
    """
