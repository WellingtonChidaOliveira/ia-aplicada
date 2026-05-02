import ollama


def send_image_ollama(img_b64: str, prompt: str):
    response = ollama.chat(
        model="llava:7b",
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
            "num_predict": 512,
        },
        keep_alive=0,
    )

    return response


def send_text_ollama(prompt: str):
    response = ollama.chat(
        model="llama3.1:latest",
        stream=False,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 1.2,
        },
    )

    return response.message.content
