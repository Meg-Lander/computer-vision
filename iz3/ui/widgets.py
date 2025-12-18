# ui/widgets.py
from PyQt6.QtWidgets import (
    QLabel, QPushButton, QFrame, QVBoxLayout, QHBoxLayout,
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsOpacityEffect, QWidget
)
from PyQt6.QtGui import QFont, QPainter, QDesktopServices, QColor, QPixmap
from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve


# --- КНОПКИ (ВСЕГДА СЕРЫЕ) ---
class IndButton(QPushButton):
    def __init__(self, text, primary=False):

        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        # ЕДИНЫЙ СТИЛЬ ДЛЯ ВСЕХ КНОПОК
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a3a3c, stop:1 #2d2d30);
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #4a4a4c;
                border-color: #777;
            }
            QPushButton:pressed { background-color: #252526; }
            QPushButton:disabled { background-color: #252526; color: #555; }
        """)



class QRContentCard(QFrame):
    def __init__(self, index, text, conf, geo):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2e; 
                border-radius: 4px;
                border: 1px solid #3e3e42;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        lbl_idx = QLabel(f"#{index}")
        lbl_idx.setStyleSheet("color: #666; font-weight: bold; border: none; font-size: 10px;")
        lbl_metrics = QLabel(f"YOLO: {conf:.2f} | GEO: {geo:.2f}")
        lbl_metrics.setStyleSheet("color: #555; font-size: 9px; border: none;")
        top_row.addWidget(lbl_idx)
        top_row.addStretch()
        top_row.addWidget(lbl_metrics)
        layout.addLayout(top_row)

        row_content = QHBoxLayout()
        txt_lbl = QLabel(text)
        txt_lbl.setWordWrap(True)
        txt_lbl.setStyleSheet("border: none;")

        is_url = text.startswith("http")
        if is_url:
            txt_lbl.setStyleSheet(
                "color: #4da6ff; font-family: Consolas; font-size: 12px; text-decoration: underline; border: none;")
            txt_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            txt_lbl.mousePressEvent = lambda e: QDesktopServices.openUrl(QUrl(text))
            txt_lbl.setToolTip("Нажмите, чтобы открыть ссылку")
        else:
            txt_lbl.setStyleSheet("color: #e0e0e0; font-family: Consolas; font-size: 12px; border: none;")

        row_content.addWidget(txt_lbl, stretch=1)
        layout.addLayout(row_content)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        btn_copy = QPushButton("Копировать")
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.setFixedHeight(22)
        btn_copy.setStyleSheet("""
            QPushButton { background: #3a3a3c; color: #ccc; border: 1px solid #555; border-radius: 3px; font-size: 10px; padding: 0 10px; }
            QPushButton:hover { background: #505050; color: white; }
        """)
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(text))

        btn_layout.addWidget(btn_copy)

        if is_url:
            btn_open = QPushButton("Перейти ↗")
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.setFixedHeight(22)
            btn_open.setStyleSheet("""
                QPushButton { background: #005f9e; color: white; border: 1px solid #007acc; border-radius: 3px; font-size: 10px; padding: 0 10px; }
                QPushButton:hover { background: #007acc; }
            """)
            btn_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(text)))
            btn_layout.addWidget(btn_open)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)



class GroupResultWidget(QWidget):
    def __init__(self, source_name, codes):
        super().__init__()
        self.is_expanded = True
        self.codes_count = len(codes)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. ЗАГОЛОВОК (КНОПКА)
        self.toggle_btn = QPushButton()
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.clicked.connect(self.toggle_content)

        border_color = "#2da44e" if self.codes_count > 0 else "#3e3e42"
        bg_color = "#252526"


        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding-left: 10px;
                padding-right: 10px;
                color: #ffffff; 
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background-color: #2d2d30; }}
        """)

        btn_layout = QHBoxLayout(self.toggle_btn)
        btn_layout.setContentsMargins(10, 0, 10, 0)

        self.arrow_lbl = QLabel("▼")
        self.arrow_lbl.setStyleSheet("border: none; color: #ffffff; font-size: 10px;")

        display_name = (source_name[:25] + '..') if len(source_name) > 25 else source_name
        name_lbl = QLabel(display_name)
        name_lbl.setStyleSheet("border: none; font-weight: bold; color: #ffffff;")

        badge_color = "#2da44e" if self.codes_count > 0 else "#555"
        count_lbl = QLabel(f"{self.codes_count}")
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_lbl.setFixedSize(24, 18)
        count_lbl.setStyleSheet(f"""
            background-color: {badge_color}; 
            color: white; 
            border-radius: 9px; 
            font-size: 11px; 
            font-weight: bold; 
            border: none;
        """)

        btn_layout.addWidget(self.arrow_lbl)
        btn_layout.addWidget(name_lbl)
        btn_layout.addStretch()
        btn_layout.addWidget(count_lbl)

        self.main_layout.addWidget(self.toggle_btn)

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(5, 5, 5, 10)
        self.content_layout.setSpacing(8)

        for i, code in enumerate(codes):
            card = QRContentCard(i + 1, code['text'], code.get('conf', 0), code.get('geo_score', 0))
            self.content_layout.addWidget(card)

        self.main_layout.addWidget(self.content_area)

        if self.codes_count == 0:
            self.toggle_content()

    def toggle_content(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.content_area.show()
            self.arrow_lbl.setText("▼")
        else:
            self.content_area.hide()
            self.arrow_lbl.setText("▶")



class PhotoViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: #101010;")

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    def set_image(self, pixmap):
        self._pixmap_item.setPixmap(pixmap)
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.setSceneRect(self._pixmap_item.boundingRect())

    def clear(self):
        self._pixmap_item.setPixmap(QPixmap())
        self.setSceneRect(0, 0, 0, 0)

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)