# config.py
import os

# Укажите актуальный путь к вашей модели
MODEL_PATH = r"D:/для питона/pythonProject1/iz3/iz3/runs/detect/qr_model7/weights/best.pt"

# Проверка существования модели (опционально)
if not os.path.exists(MODEL_PATH):
    print(f"[WARNING] Model not found at: {MODEL_PATH}")