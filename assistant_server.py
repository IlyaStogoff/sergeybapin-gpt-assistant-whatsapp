from flask import Flask, request, jsonify
import openai
import os
import time

openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def handle_whatsapp():
    data = request.get_json()

    if not data or "query" not in data or "message" not in data["query"]:
        return jsonify({"replies": [{"message": "⚠️ Сообщение не получено"}]}), 400

    user_message = data["query"]["message"]

    # Создаём поток и добавляем сообщение
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

    # Ждём ответа
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value

    return jsonify({"replies": [{"message": answer}]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
