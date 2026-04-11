import ollama


def send_image_ollama(img_b64: str, prompt: str):
    response = ollama.chat(
        model="qwen3-vl:8b",
        stream=False,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [img_b64],
            }
        ],
        options={
            "temperature": 0.1,
            "num_predict": 256,
        },
    )

    return response


def send_text_ollama(prompt: str):
    response = ollama.chat(
        model="qwen3-vl:8b",
        stream=False,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0.1,
            "num_predict": 256,
        },
    )

    return response
