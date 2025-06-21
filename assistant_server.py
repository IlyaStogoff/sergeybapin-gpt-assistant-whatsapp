from flask import Flask, request, jsonify
import openai
import os
import time

openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

app = Flask(__name__)

@app.route("/whatsapp", methods=["GET", "POST"])
def handle_whatsapp():
    # Пробуем взять сообщение из заголовка
    user_message = request.headers.get("message")

    # Если не пришло — пробуем из GET параметра
    if not user_message:
        user_message = request.args.get("message")

    if not user_message:
        return jsonify({"reply": "❗ Сообщение не получено"}), 400

    # Создаём поток и отправляем сообщение
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    while True:
        status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value

    return jsonify({"reply": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
