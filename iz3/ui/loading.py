# ui/loading.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Пропускать клики сквозь
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("ОБРАБОТКА...")
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 16px;
                background-color: rgba(0, 0, 0, 180);
                padding: 10px 20px;
                border-radius: 15px;
                border: 1px solid #007acc;
            }
        """)
        layout.addWidget(self.label)


        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_text)

    def start(self):
        self.resize(self.parent().size())
        self.show()
        self.timer.start(300)

    def stop(self):
        self.timer.stop()
        self.hide()

    def animate_text(self):
        self.dots = (self.dots + 1) % 4
        self.label.setText(f"ОБРАБОТКА{'.' * self.dots}")

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))