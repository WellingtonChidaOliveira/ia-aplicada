def generate_phrase_prompt(reason: str):
    return f"""Existe um momento em que alguém está completamente sozinho com o seu esforço. 
Sem plateia. Sem aprovação. Só ele e o peso do que escolheu carregar.

Com base na RAZÃO DO MOMENTO abaixo, escreva UMA frase curta que nomeie a verdade interna desse instante.

DIRETRIZES CRÍTICAS:
- Não descreva o exercício ou a ação física. Nomeie o SENTIMENTO ou a CONSTATAÇÃO por trás da ação.
- Estilo: Estóico, seco e profundo. Frases que fazem o leitor parar e reler.
- Máximo 80 caracteres.
- Retorne apenas a frase, sem aspas e sem explicações.

RAZÃO DO MOMENTO (O que está acontecendo): {reason}

REFERÊNCIAS DE IMPACTO:
"O que me destrói também me ensina exatamente onde eu era fraco."
"A carga não pesa mais que a vontade de parar."
"Não é força. É a recusa de dar razão a quem esperava que eu parasse."
"O silêncio do esforço é o único lugar onde minha dor faz sentido."
"Venci a mim mesmo hoje; o resto do mundo é apenas uma consequência."
"O peso que carrego hoje é a leveza que terei amanhã."
"""
