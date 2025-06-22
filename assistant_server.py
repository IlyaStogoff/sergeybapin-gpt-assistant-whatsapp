from flask import Flask, request, jsonify
import openai
import os
import time
import requests
import tempfile

openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def handle_whatsapp():
    data = request.get_json()

    if not data or "query" not in data or "message" not in data["query"]:
        return jsonify({"replies": [{"message": "⚠️ Сообщение не получено"}]}), 400

    user_message = data["query"]["message"]

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
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value

    return jsonify({"replies": [{"message": answer}]})


@app.route("/transcribe", methods=["POST"])
def transcribe_voice():
    data = request.get_json()
    if not data or "audio_url" not in data:
        return jsonify({"replies": [{"message": "❗ Нет ссылки на аудиофайл"}]}), 400

    audio_url = data["audio_url"]

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
            audio_data = requests.get(audio_url).content
            tmp_file.write(audio_data)
            tmp_file.flush()

            with open(tmp_file.name, "rb") as f:
                transcript = openai.Audio.transcribe("whisper-1", f)

        text = transcript.get("text", "🤷 Не удалось распознать речь.")

        return jsonify({
            "replies": [
                {
                    "message": text
                }
            ]
        })

    except Exception as e:
        return jsonify({
            "replies": [
                {
                    "message": f"⚠️ Ошибка: {str(e)}"
                }
            ]
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
