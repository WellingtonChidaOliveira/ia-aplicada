def prompt_analisys_video() -> str:
    return """
Você é um especialista em análise de vídeos de treino de musculação.
Sua tarefa é descrever o que vê em cada frame fornecido.
Para cada frame, descreva: nível de esforço aparente, tipo de exercício, 
expressão facial, qualidade do movimento e composição visual.
Seja descritivo e detalhado. Não retorne JSON nesta etapa.
"""


def user_prompt() -> str:
    return """
Analise cada frame abaixo em ordem. Para cada um, descreva:
- Intensidade do esforço (baixa / média / alta)
- Tipo de exercício identificado
- Expressão e estado aparente do atleta
- Qualidade visual e composição do frame
"""
