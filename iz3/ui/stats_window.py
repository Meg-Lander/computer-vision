# ui/stats_window.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QHeaderView,
    QAbstractItemView, QHBoxLayout, QPushButton, QTableWidgetItem, QFileDialog
)
from PyQt6.QtGui import QFont

class StatsWindow(QDialog):
    def __init__(self, stats_manager, parent=None):
        super().__init__(parent)
        self.manager = stats_manager
        self.setWindowTitle("Метрики и Статистика")
        self.resize(900, 500)
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")

        layout = QVBoxLayout(self)

        lbl = QLabel("ИСТОРИЯ СЕССИЙ И МЕТРИКИ")
        lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #007acc; letter-spacing: 1px;")
        layout.addWidget(lbl)

        self.table = QTableWidget()
        cols = ["Время", "Источник", "Кол-во QR", "YOLO Conf (Avg)", "Geo Score (Avg)", "Время обр. (сек)"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #252526;
                gridline-color: #3e3e42;
                border: 1px solid #3e3e42;
                font-family: 'Segoe UI';
            }
            QHeaderView::section {
                background-color: #333337;
                padding: 5px;
                border: 1px solid #3e3e42;
                font-weight: bold;
            }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #007acc; }
        """)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Экспорт в CSV")
        btn_export.setFixedHeight(35)
        btn_export.setStyleSheet("""
            QPushButton { background-color: #2d2d30; border: 1px solid #555; padding: 5px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #3e3e40; }
        """)
        btn_export.clicked.connect(self.export_data)

        btn_close = QPushButton("Закрыть")
        btn_close.setFixedHeight(35)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #c42b1c; color: white; border: none; padding: 5px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #e81123; }
        """)
        btn_close.clicked.connect(self.close)

        btn_layout.addWidget(btn_export)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        self.load_data()

    def load_data(self):
        history = self.manager.get_history()
        self.table.setRowCount(len(history))
        for i, row in enumerate(history):
            self.table.setItem(i, 0, QTableWidgetItem(str(row['timestamp'])))
            self.table.setItem(i, 1, QTableWidgetItem(str(row['source'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(row['count'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(row['conf_avg'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(row['geo_score_avg'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(row['duration'])))

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")
        if path:
            if self.manager.export_csv(path):
                self.setWindowTitle("Метрики - Экспорт успешен")
            else:
                self.setWindowTitle("Метрики - Ошибка экспорта")