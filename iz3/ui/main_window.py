# ui/main_window.py
import os
import time
import cv2
import datetime
import numpy as np

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QScrollArea, QPushButton, QApplication, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QDragEnterEvent, QDropEvent, QDragMoveEvent

from config import MODEL_PATH
from core.stats_manager import StatsManager
from core.detector import QRDetector
from core.snipper import SnippingWidget
from ui.widgets import IndButton, PhotoViewer, GroupResultWidget
from ui.stats_window import StatsWindow
from ui.ip_camera_dialog import IPCameraDialog


class EliteMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR ANALYZER")
        self.resize(1300, 850)
        self.setStyleSheet("QMainWindow { background-color: #1e1e1e; }")

        # Включаем поддержку Drag & Drop
        self.setAcceptDrops(True)

        self.stats_manager = StatsManager()
        self.detector = None


        self.batch_items = []
        self.batch_index = 0

        try:
            self.detector = QRDetector(MODEL_PATH)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки модели", f"Не удалось загрузить модель:\n{e}")

        self.snipper = SnippingWidget()
        self.snipper.on_snip_taken.connect(self.process_snip_image)
        self.snipper.on_closed.connect(self.on_snipper_closed)

        self.init_ui()



    def dragEnterEvent(self, event: QDragEnterEvent):
        """Вызывается, когда вы втаскиваете файл в окно"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Вызывается, пока вы водите файлом над окном (ВАЖНО ДЛЯ WINDOWS)"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Вызывается, когда вы отпускаете кнопку мыши"""
        urls = event.mimeData().urls()
        if not urls: return


        path = urls[0].toLocalFile()


        if os.path.isdir(path):
            self.process_folder(path)
        else:
            self.process_file(path)


    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(400)
        sidebar.setStyleSheet("background-color: #252526; border-right: 1px solid #333;")

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(15, 20, 15, 20)
        sb_layout.setSpacing(12)

        lbl_title = QLabel("ПАНЕЛЬ УПРАВЛЕНИЯ")
        lbl_title.setStyleSheet("color: #888; font-weight: bold; letter-spacing: 1px; font-size: 12px;")
        sb_layout.addWidget(lbl_title)

        self.btn_file = IndButton("ОТКРЫТЬ ФАЙЛ")
        self.btn_file.clicked.connect(self.on_file)
        sb_layout.addWidget(self.btn_file)

        self.btn_monitor = IndButton("ВЫДЕЛИТЬ ОБЛАСТЬ", primary=True)
        self.btn_monitor.clicked.connect(self.start_snipping_mode)
        sb_layout.addWidget(self.btn_monitor)

        self.btn_ip_cam = IndButton("IP WEBCAM (ТЕЛЕФОН)")
        self.btn_ip_cam.clicked.connect(self.open_ip_camera)
        sb_layout.addWidget(self.btn_ip_cam)

        self.btn_stats = IndButton("СТАТИСТИКА / МЕТРИКИ")
        self.btn_stats.setStyleSheet(
            "QPushButton { border: 1px dashed #555; color: #aaa; background: transparent; } "
            "QPushButton:hover { color: white; border: 1px solid #777; }"
        )
        self.btn_stats.clicked.connect(self.show_stats)
        sb_layout.addWidget(self.btn_stats)

        lbl_res = QLabel("ЖУРНАЛ СКАНИРОВАНИЯ")
        lbl_res.setStyleSheet("color: #888; font-weight: bold; margin-top: 20px; font-size: 12px;")
        sb_layout.addWidget(lbl_res)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.results_container = QWidget()
        self.results_container.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(10)

        self.scroll_area.setWidget(self.results_container)
        sb_layout.addWidget(self.scroll_area)


        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(10)

        btn_clear_log = QPushButton("Очистить журнал")
        btn_clear_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_log.setStyleSheet("background: transparent; color: #666; border: none; font-size: 11px;")
        btn_clear_log.clicked.connect(self.clear_log)

        btn_clear_view = QPushButton("Закрыть фото")
        btn_clear_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_view.setStyleSheet("background: transparent; color: #666; border: none; font-size: 11px;")
        btn_clear_view.clicked.connect(self.clear_view)

        btns_layout.addWidget(btn_clear_log)
        btns_layout.addWidget(btn_clear_view)

        sb_layout.addLayout(btns_layout)


        preview_panel = QFrame()
        preview_panel.setStyleSheet("background-color: #101010;")
        pp_layout = QVBoxLayout(preview_panel)
        pp_layout.setContentsMargins(0, 0, 0, 0)
        pp_layout.setSpacing(0)

        self.preview = PhotoViewer()
        pp_layout.addWidget(self.preview)


        self.nav_frame = QFrame()
        self.nav_frame.setFixedHeight(50)
        self.nav_frame.setStyleSheet("background-color: #1e1e1e; border-top: 1px solid #333;")
        self.nav_frame.hide()

        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(10, 5, 10, 5)

        self.btn_prev = QPushButton("◀ Назад")
        self.btn_prev.setFixedSize(100, 30)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_prev.setStyleSheet(
            "QPushButton { background: #333; color: white; border: none; border-radius: 4px; } QPushButton:hover { background: #444; }")

        self.lbl_counter = QLabel("0 / 0")
        self.lbl_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_counter.setStyleSheet("color: #aaa; font-weight: bold; font-family: Consolas;")

        self.btn_next = QPushButton("Вперед ▶")
        self.btn_next.setFixedSize(100, 30)
        self.btn_next.clicked.connect(self.next_image)
        self.btn_next.setStyleSheet(
            "QPushButton { background: #333; color: white; border: none; border-radius: 4px; } QPushButton:hover { background: #444; }")

        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_counter)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addStretch()

        pp_layout.addWidget(self.nav_frame)

        self.status_bar = QLabel("Система готова. Перетащите папку или файл.")
        self.status_bar.setFixedHeight(25)
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_bar.setStyleSheet(
            "background-color: #007acc; color: white; font-weight: bold; font-family: 'Segoe UI'; font-size: 12px;"
        )
        pp_layout.addWidget(self.status_bar)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(preview_panel)

        if not self.detector:
            self.status_bar.setText("ОШИБКА: МОДЕЛЬ НЕ ЗАГРУЖЕНА")
            self.status_bar.setStyleSheet("background-color: #c42b1c; color: white; font-weight: bold;")
            self.btn_file.setEnabled(False)
            self.btn_monitor.setEnabled(False)
            self.btn_ip_cam.setEnabled(False)


    def clear_view(self):
        self.preview.clear()
        self.batch_items = []
        self.batch_index = 0
        self.update_nav_ui()
        self.status_bar.setText("Область просмотра очищена")
        self.status_bar.setStyleSheet("background-color: #333; color: #aaa;")


    def update_nav_ui(self):
        count = len(self.batch_items)
        if count > 1:
            self.nav_frame.show()
            self.lbl_counter.setText(f"{self.batch_index + 1} / {count}")
        else:
            self.nav_frame.hide()

    def next_image(self):
        if self.batch_index < len(self.batch_items) - 1:
            self.batch_index += 1
            self.load_batch_image()
            self.update_nav_ui()

    def prev_image(self):
        if self.batch_index > 0:
            self.batch_index -= 1
            self.load_batch_image()
            self.update_nav_ui()

    def load_batch_image(self):
        if not self.batch_items: return

        item = self.batch_items[self.batch_index]
        path = item.get('path')
        img_bgr = item.get('image')

        if path and os.path.exists(path):
            try:
                stream = open(path, "rb")
                bytes_data = bytearray(stream.read())
                numpyarray = np.asarray(bytes_data, dtype=np.uint8)
                img_bgr = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)
                if img_bgr is not None and img_bgr.shape[2] == 4:
                    img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2BGR)
            except:
                return

        if img_bgr is None: return

        output_img = img_bgr.copy()
        qr_data = item.get('data', [])

        for i, code in enumerate(qr_data):
            if 'points' in code:
                pts = np.array(code['points'], np.int32)
                color = (100, 255, 0)
                cv2.polylines(output_img, [pts], True, color, 3, cv2.LINE_AA)

            if 'corner' in code:
                corner = code['corner']
                label = f"ID:{i} | {code.get('text', '')[:10]}..."
                cv2.putText(output_img, label, (int(corner[0]), int(corner[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 0), 1, cv2.LINE_AA)

        self._display_image(output_img)
        filename = os.path.basename(path) if path else "Скриншот"
        self.status_bar.setText(f"Просмотр: {filename} ({len(qr_data)} кодов)")
        self.status_bar.setStyleSheet("background-color: #333; color: white;")


    def process_folder(self, folder_path):
        files = os.listdir(folder_path)
        images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))]

        if not images:
            self.status_bar.setText("В папке нет изображений")
            return

        self.batch_items = []
        self.clear_log()
        self.clear_view()

        total = len(images)
        processed = 0
        found_total = 0

        self.status_bar.setText(f"Обработка: 0 / {total}")
        self.status_bar.setStyleSheet("background-color: #e6a700; color: black;")

        for img_file in images:
            full_path = os.path.join(folder_path, img_file)
            processed += 1

            try:
                stream = open(full_path, "rb")
                bytes_data = bytearray(stream.read())
                numpyarray = np.asarray(bytes_data, dtype=np.uint8)
                img = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)

                if img is not None:
                    if img.shape[2] == 4: img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                    qr_data, _, duration = self.detector.detect_and_decode(img)

                    self.batch_items.append({
                        'path': full_path,
                        'image': None,
                        'data': qr_data
                    })

                    if qr_data:
                        found_total += len(qr_data)
                        self.stats_manager.add_record(img_file, qr_data, duration)
                        self.add_group_result(img_file, qr_data)

            except Exception:
                pass

            if processed % 5 == 0:
                self.status_bar.setText(f"Обработка: {processed} / {total}")
                QApplication.processEvents()

        self.status_bar.setText(f"Готово. Обработано {total}, Найдено {found_total}")
        self.status_bar.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold;")

        if self.batch_items:
            self.batch_index = 0
            self.load_batch_image()
            self.update_nav_ui()

    def process_file(self, path):
        filename = os.path.basename(path)
        try:
            stream = open(path, "rb")
            bytes_data = bytearray(stream.read())
            numpyarray = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)

            if img is not None:
                if img.shape[2] == 4: img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                qr_data, _, duration = self.detector.detect_and_decode(img)

                self.batch_items = [{
                    'path': path,
                    'image': None,
                    'data': qr_data
                }]
                self.batch_index = 0

                self._display_image(img)
                self.load_batch_image()
                self.update_nav_ui()

                self.stats_manager.add_record(filename, qr_data, duration)
                if qr_data:
                    self.add_group_result(filename, qr_data)
                    self.status_bar.setText(f"УСПЕХ: Найдено {len(qr_data)} кодов")
                    self.status_bar.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold;")
                else:
                    self.status_bar.setText("Коды не найдены")
                    self.status_bar.setStyleSheet("background-color: #c42b1c; color: white;")
        except Exception as e:
            self.status_bar.setText(f"Ошибка: {e}")


    def _display_image(self, img_bgr):
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_rgb = np.ascontiguousarray(img_rgb)
        h, w, ch = img_rgb.shape
        qt_img = QImage(img_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.preview.set_image(QPixmap.fromImage(qt_img))

    def add_group_result(self, source, codes):
        group_widget = GroupResultWidget(source, codes)
        self.results_layout.insertWidget(0, group_widget)

    def clear_log(self):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_stats(self):
        dlg = StatsWindow(self.stats_manager, self)
        dlg.exec()

    def on_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.process_file(path)


    def start_snipping_mode(self):
        self.showMinimized()
        QTimer.singleShot(300, self.snipper.start)

    def on_snipper_closed(self):
        self.showNormal()
        self.activateWindow()

    def process_snip_image(self, img_bgr):
        self.showNormal()
        self.activateWindow()
        QApplication.processEvents()

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        name = f"Скриншот {timestamp}"

        qr_data, drawn_img, duration = self.detector.detect_and_decode(img_bgr)

        self.batch_items = [{
            'path': None,
            'image': img_bgr,
            'data': qr_data
        }]
        self.batch_index = 0
        self.update_nav_ui()

        self._display_image(drawn_img)
        self.add_group_result(name, qr_data)
        self.stats_manager.add_record(name, qr_data, duration)

    def open_ip_camera(self):
        if not self.detector: return
        dlg = IPCameraDialog(self.detector, self)
        dlg.data_found.connect(self.on_ip_camera_success)
        dlg.exec()

    def on_ip_camera_success(self, qr_data, drawn_img, duration):
        name = f"IP Cam {datetime.datetime.now().strftime('%H:%M:%S')}"

        self.batch_items = [{
            'path': None,
            'image': drawn_img,
            'data': qr_data
        }]
        self.batch_index = 0
        self.update_nav_ui()

        self._display_image(drawn_img)
        self.stats_manager.add_record(name, qr_data, duration)
        self.add_group_result(name, qr_data)