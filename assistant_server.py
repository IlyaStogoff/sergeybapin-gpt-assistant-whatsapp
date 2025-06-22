from flask import Flask, request, jsonify
import openai, os, time, re, requests, tempfile
from xlcalculator import ModelCompiler, Evaluator
from openpyxl import load_workbook

# Конфиг
openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")
EXCEL_PATH = "Sticker.food_08.06.25.xlsx"
SHEET_NAME = "Prices"

# Собираем модель Excel
compiler = ModelCompiler()
model = compiler.read_and_parse_archive(EXCEL_PATH)
evaluator = Evaluator(model)

app = Flask(__name__)

def parse_dimensions(text):
    nums = re.findall(r"\d+", text)
    return tuple(map(int, nums[:3])) if len(nums) >= 3 else None

@app.route("/whatsapp", methods=["POST"])
def handle_whatsapp():
    data = request.get_json()
    if not data or "query" not in data or "message" not in data["query"]:
        return jsonify({"replies":[{"message":"⚠️ Сообщение не получено"}]}), 400

    user_message = data["query"]["message"]
    dims = parse_dimensions(user_message)
    if not dims:
        return jsonify({"replies":[{"message":"Пожалуйста, укажи: ширину, высоту и тираж цифрами."}]}), 200

    width, height, tirazh = dims

    # Запись в Excel-модель
    evaluator.set_cell_value(SHEET_NAME, "B2", width)
    evaluator.set_cell_value(SHEET_NAME, "C2", height)
    evaluator.set_cell_value(SHEET_NAME, "D2", tirazh)

    # Вычисление формулы
    try:
        price = evaluator.evaluate(SHEET_NAME, "E2")
        reply = f"По размеру {width}×{height} мм и тиражу {tirazh} шт. цена: {price} ₸ за штуку."
    except Exception as e:
        reply = f"Ошибка при расчёте: {str(e)}"

    cleaned = re.sub(r"【\d+:\d+†.*?】", "", reply).strip()
    return jsonify({"replies":[{"message":cleaned}]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
