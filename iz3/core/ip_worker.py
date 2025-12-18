# core/ip_worker.py
import cv2
import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class IPCameraWorker(QThread):
    frame_ready = pyqtSignal(np.ndarray)  # Просто кадр для превью
    result_ready = pyqtSignal(list, np.ndarray, float)  # Если нашли код: данные, картинка, время
    error_occurred = pyqtSignal(str)

    def __init__(self, url, detector):
        super().__init__()
        self.url = url
        self.detector = detector
        self._run = True
        self.skip_frames = 10  # Проверять QR код каждые 10 кадров (оптимизация)

    def run(self):
        cap = cv2.VideoCapture(self.url)

        # Настройка буфера, чтобы уменьшить задержку (Latency)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            self.error_occurred.emit(f"Не удалось подключиться к: {self.url}")
            return

        frame_count = 0

        while self._run:
            ret, frame = cap.read()
            if not ret:
                # Если поток прервался, пробуем переподключиться или выходим
                time.sleep(0.1)
                continue

            # 1. Отправляем кадр в GUI для плавного видео
            if self._run:
                self.frame_ready.emit(frame)

            # 2. Раз в N кадров пытаемся найти QR код
            frame_count += 1
            if frame_count % self.skip_frames == 0:
                try:
                    # Используем "легкую" проверку или полную.
                    # Чтобы не тормозить поток, можно делать resize для детекции
                    # Но пока попробуем на полном кадре.

                    # ВАЖНО: detect_and_decode возвращает (qr_data, drawn_img, time)
                    # Мы используем копию кадра, чтобы рисование не портило превью
                    check_frame = frame.copy()
                    qr_data, drawn_img, duration = self.detector.detect_and_decode(check_frame)

                    if qr_data:
                        # УРА! НАШЛИ!
                        self.result_ready.emit(qr_data, drawn_img, duration)
                        self._run = False  # Останавливаем цикл
                        break
                except Exception as e:
                    print(f"Detection error in stream: {e}")

            # Ограничение FPS, чтобы не грузить CPU
            time.sleep(0.01)

        cap.release()

    def stop(self):
        self._run = False
        self.wait()