def image_prompt(frame_num: int, total: int, timestamp_label: str):
    return f"""
     Frame {frame_num}/{total} ({timestamp_label}) de um vídeo de treino de musculação. "
                    "Descreva em 2-3 linhas: nível de esforço (baixo/médio/alto), "
                    "exercício ou posição, expressão do atleta."
                    """
