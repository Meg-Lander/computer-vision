# ui/ip_camera_dialog.py
import cv2
import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QComboBox, QPushButton, QLabel, QMessageBox, QFrame, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings, QRect
from PyQt6.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QLinearGradient

from core.ip_worker import IPCameraWorker
from ui.loading import LoadingOverlay


class ScannerHUD(QWidget):
    """Виджет, рисующий бегающую линию сканера поверх видео"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.y_pos = 0
        self.direction = 1
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.hide()

    def start(self):
        self.show()
        self.timer.start(20)  # 50 FPS

    def stop(self):
        self.hide()
        self.timer.stop()

    def animate(self):
        h = self.height()
        speed = 5
        self.y_pos += speed * self.direction
        if self.y_pos > h:
            self.y_pos = h
            self.direction = -1
        elif self.y_pos < 0:
            self.y_pos = 0
            self.direction = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()

        grad = QLinearGradient(0, self.y_pos, w, self.y_pos)
        grad.setColorAt(0, QColor(0, 255, 0, 0))
        grad.setColorAt(0.5, QColor(0, 255, 0, 255))
        grad.setColorAt(1, QColor(0, 255, 0, 0))

        pen = QPen(QColor(0, 255, 0))
        pen.setBrush(grad)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(0, self.y_pos, w, self.y_pos)


class IPCameraDialog(QDialog):
    data_found = pyqtSignal(list, np.ndarray, float)

    def __init__(self, detector, parent=None):
        super().__init__(parent)
        self.detector = detector
        self.setWindowTitle("IP Webcam Scanner (HUD Active)")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")


        self.settings = QSettings("EliteQR", "IPCameraHistory")

        self.worker = None

        layout = QVBoxLayout(self)


        input_layout = QHBoxLayout()

        self.combo_url = QComboBox()
        self.combo_url.setEditable(True)
        self.combo_url.setStyleSheet("""
            QComboBox { padding: 8px; border: 1px solid #555; background: #252526; color: white; border-radius: 4px; }
            QComboBox::drop-down { border: none; }
        """)
        self._load_history()  # Загрузка истории

        self.btn_connect = QPushButton("ПОДКЛЮЧИТЬСЯ")
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.setStyleSheet("""
            QPushButton { background-color: #007acc; color: white; padding: 8px 15px; border: none; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #0062a3; }
        """)
        self.btn_connect.clicked.connect(self.toggle_connect)

        input_layout.addWidget(self.combo_url, stretch=1)
        input_layout.addWidget(self.btn_connect)
        layout.addLayout(input_layout)


        self.frame_container = QFrame()
        self.frame_container.setStyleSheet("background: black; border: 1px solid #333; border-radius: 4px;")
        self.frame_layout = QVBoxLayout(self.frame_container)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel("ОЖИДАНИЕ ПОДКЛЮЧЕНИЯ...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("color: #666;")
        self.frame_layout.addWidget(self.video_label)


        self.hud = ScannerHUD(self.video_label)


        self.overlay = LoadingOverlay(self.video_label)

        layout.addWidget(self.frame_container, stretch=1)

    def _load_history(self):
        history = self.settings.value("history", [], type=list)
        if not history:
            history = ["http://192.168.0.100:8080/video", "http://192.168.1.5:8080/video"]
        self.combo_url.addItems(history)

    def _save_history(self, url):
        history = [self.combo_url.itemText(i) for i in range(self.combo_url.count())]
        if url in history:
            history.remove(url)
        history.insert(0, url)
        history = history[:5]  # Храним только 5 последних
        self.settings.setValue("history", history)

    def toggle_connect(self):
        if self.worker and self.worker.isRunning():
            self.stop_stream()
        else:
            self.start_stream()

    def start_stream(self):
        url = self.combo_url.currentText().strip()
        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите URL камеры!")
            return

        self._save_history(url)
        self.btn_connect.setText("ОТКЛЮЧИТЬСЯ")
        self.btn_connect.setStyleSheet(
            "background-color: #c42b1c; color: white; padding: 8px 15px; font-weight: bold; border-radius: 4px;")
        self.video_label.setText("ПОДКЛЮЧЕНИЕ...")

        self.worker = IPCameraWorker(url, self.detector)
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.result_ready.connect(self.handle_result)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

        self.hud.start()

    def stop_stream(self):
        if self.worker:
            self.worker.stop()
        self.hud.stop()

    def update_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qt_img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)

        pix = QPixmap.fromImage(qt_img).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(pix)


        if self.hud.isVisible():
            self.hud.resize(self.video_label.size())
        if self.overlay.isVisible():
            self.overlay.resize(self.video_label.size())

    def handle_result(self, qr_data, drawn_img, duration):
        self.hud.stop()
        self.overlay.start()
        self.data_found.emit(qr_data, drawn_img, duration)
        self.close()

    def handle_error(self, msg):
        QMessageBox.critical(self, "Ошибка IP камеры", msg)
        self.stop_stream()

    def on_worker_finished(self):
        self.btn_connect.setText("ПОДКЛЮЧИТЬСЯ")
        self.btn_connect.setStyleSheet(
            "background-color: #007acc; color: white; padding: 8px 15px; font-weight: bold; border-radius: 4px;")
        self.video_label.clear()
        self.video_label.setText("ТРАНСЛЯЦИЯ ОСТАНОВЛЕНА")
        self.overlay.stop()
        self.hud.stop()

    def closeEvent(self, event):
        self.stop_stream()
        super().closeEvent(event)