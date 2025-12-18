# core/snipper.py
import numpy as np
import cv2
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QColor, QPen, QPainter, QCursor, QImage


class SnippingWidget(QWidget):
    """
    Виджет, перекрывающий весь экран для выбора области (стиль Win+Shift+S).
    Исправлена ошибка памяти 0xC0000409.
    """
    on_snip_taken = pyqtSignal(np.ndarray)
    on_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Настройка окна: без рамок, поверх всех окон
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)  # Не удалять объект при закрытии

        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)

        self.original_pixmap = None
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False

    def start(self):
        """Захват экрана и показ виджета"""
        screen = QApplication.primaryScreen()

        # Получаем ID корневого окна (Desktop)
        # В некоторых версиях PyQt6 grabWindow(0) работает стабильнее
        self.original_pixmap = screen.grabWindow(0)

        rect = self.original_pixmap.rect()
        self.setGeometry(rect)
        self.showFullScreen()

        # Сброс координат
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        self.update()

    def paintEvent(self, event):
        if not self.original_pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # 1. Рисуем затемненный фон
        painter.drawPixmap(0, 0, self.original_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # 2. Если идет выделение, "вырезаем" дырку
        if self.begin != self.end:
            # Нормализация прямоугольника (чтобы работало выделение в любую сторону)
            rect = QRect(self.begin, self.end).normalized()

            # Рисуем чистый скриншот внутри прямоугольника
            painter.drawPixmap(rect, self.original_pixmap, rect)

            # Рисуем рамку
            pen = QPen(QColor("#007acc"), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Текст с размерами
            w, h = rect.width(), rect.height()
            if w > 10 and h > 10:
                txt = f"{w} x {h}"
                painter.setPen(QColor("#ffffff"))
                # Рисуем текст чуть выше рамки
                painter.drawText(rect.x(), rect.y() - 5, txt)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.is_snipping = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_snipping = False
        self.end = event.pos()

        # Сначала скрываем окно, чтобы пользователь видел реакцию мгновенно
        self.hide()

        # Вычисляем область
        rect = QRect(self.begin, self.end).normalized()

        # Защита от микроблаков (слишком мелкая область)
        if rect.width() < 5 or rect.height() < 5:
            self.close()
            self.on_closed.emit()
            return

        try:
            # Вырезаем кусок
            cropped = self.original_pixmap.copy(rect)

            # Конвертация в QImage
            q_img = cropped.toImage()
            # Конвертируем в формат, гарантированно понятный для конвертации (RGBA)
            q_img = q_img.convertToFormat(QImage.Format.Format_RGBA8888)

            width = q_img.width()
            height = q_img.height()

            # --- БЕЗОПАСНАЯ КОНВЕРТАЦИЯ ПАМЯТИ ---
            ptr = q_img.bits()
            ptr.setsize(height * width * 4)

            # Создаем массив NumPy и делаем .copy(), чтобы отвязаться от памяти Qt!
            arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4)).copy()

            # Переводим RGBA -> BGR (для OpenCV)
            img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

            self.on_snip_taken.emit(img_bgr)

        except Exception as e:
            print(f"[Snipper Error] {e}")
            self.on_closed.emit()
        finally:
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.on_closed.emit()