from flask import Flask, request, jsonify
import openai
import os
import time
import re

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
    cleaned_answer = re.sub(r"【\\d+:\\d+†source】", "", answer).strip()

    return jsonify({"replies": [{"message": cleaned_answer}]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
