# core/screen_capture.py
import time
import numpy as np
import cv2
import mss
from PyQt6.QtCore import QObject, pyqtSignal


class ScreenMonitorWorker(QObject):
    frame_ready = pyqtSignal(np.ndarray, list)
    finished = pyqtSignal()

    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self._run = True

    def run(self):
        with mss.mss() as sct:
            # Обычно monitor[1] - это основной экран.
            # Если нужно захватывать все экраны, используйте monitors[0], но это может быть медленно.
            if len(sct.monitors) > 1:
                monitor = sct.monitors[1]
            else:
                monitor = sct.monitors[0]

            while self._run:
                start_time = time.time()
                try:
                    screenshot = np.array(sct.grab(monitor))
                    img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

                    qr_data, drawn, _ = self.detector.detect_and_decode(img_bgr)

                    if self._run:
                        self.frame_ready.emit(drawn, qr_data)
                except Exception as e:
                    print(f"[Monitor Error] {e}")
                    pass

                elapsed = time.time() - start_time
                if elapsed < 0.05:
                    time.sleep(0.05 - elapsed)
        self.finished.emit()

    def stop(self):
        self._run = False