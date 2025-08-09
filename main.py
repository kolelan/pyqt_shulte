import sys
import random
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSpinBox, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor


class SchulteTableApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Конфигурационные переменные
        self.timer_font_size = 24
        self.timer_text_color = QColor(0, 0, 0)  # Черный
        self.timer_bg_color = QColor(240, 240, 240)  # Светло-серый

        self.target_font_size = 36
        self.target_font_family = "Arial"
        self.target_text_color = QColor(0, 0, 255)  # Синий
        self.target_bg_color = QColor(240, 240, 240)  # Светло-серый

        self.cell_font_size = 24
        self.cell_text_color = QColor(0, 0, 0)  # Черный
        self.cell_bg_color = QColor(255, 255, 255)  # Белый
        self.cell_highlight_color = QColor(200, 230, 255)  # Голубой

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Таблицы Шульте')
        self.setGeometry(100, 100, 800, 600)

        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)

        # Элементы управления
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(2, 10)
        self.rows_spin.setValue(4)
        self.rows_spin.setPrefix("Строки: ")

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(2, 10)
        self.cols_spin.setValue(4)
        self.cols_spin.setPrefix("Столбцы: ")

        self.game_mode_combo = QComboBox()
        self.game_mode_combo.addItems([
            "Нажатие с обновлением",
            "Игра по нажатию",
            "Игра по наведению",
            "Удержание внимания 3с",
            "Удержание внимания 5с",
            "Удержание внимания 10с",
            "Простой режим"
        ])
        self.game_mode_combo.setCurrentText("Игра по наведению")

        self.target_label = QLabel("1")
        target_font = QFont(self.target_font_family, self.target_font_size)
        self.target_label.setFont(target_font)
        self.target_label.setStyleSheet(
            f"color: {self.target_text_color.name()}; "
            f"background-color: {self.target_bg_color.name()}; "
            "padding: 5px;"
        )
        self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setMinimumWidth(80)

        self.timer_label = QLabel("00:00.000")
        timer_font = QFont("Arial", self.timer_font_size)
        self.timer_label.setFont(timer_font)
        self.timer_label.setStyleSheet(
            f"color: {self.timer_text_color.name()}; "
            f"background-color: {self.timer_bg_color.name()}; "
            "padding: 5px;"
        )
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setMinimumWidth(150)

        self.start_button = QPushButton("Старт")
        self.start_button.setMinimumWidth(100)
        self.start_button.clicked.connect(self.toggle_game)

        # Добавляем элементы на панель управления
        control_layout.addWidget(self.rows_spin)
        control_layout.addWidget(self.cols_spin)
        control_layout.addWidget(self.game_mode_combo)
        control_layout.addWidget(self.target_label)
        control_layout.addWidget(self.timer_label)
        control_layout.addWidget(self.start_button)

        # Таблица
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.cell_clicked)

        # Включаем отслеживание движения мыши
        self.table.setMouseTracking(True)
        self.table.viewport().installEventFilter(self)

        # Основной layout
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.table)

        # Игровые переменные
        self.game_active = False
        self.current_target = 1
        self.start_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.attention_timer = QTimer()
        self.attention_timer.timeout.connect(self.attention_timeout)
        self.last_hovered_cell = None

        # Инициализация таблицы
        self.generate_table()

    def eventFilter(self, source, event):
        if (source is self.table.viewport() and
                event.type() == event.MouseMove and
                self.game_active and
                self.game_mode_combo.currentText() == "Игра по наведению"):

            pos = event.pos()
            item = self.table.itemAt(pos)
            if item is not None:
                row, col = item.row(), item.column()
                if (row, col) != self.last_hovered_cell:
                    self.last_hovered_cell = (row, col)
                    self.check_cell_hover(row, col)
        return super().eventFilter(source, event)

    def check_cell_hover(self, row, col):
        if not self.game_active:
            return

        item = self.table.item(row, col)
        if item and item.text() == str(self.current_target):
            self.increment_target()

    def generate_table(self):
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)

        numbers = list(range(1, rows * cols + 1))
        random.shuffle(numbers)

        for i in range(rows):
            for j in range(cols):
                item = QTableWidgetItem(str(numbers.pop()))
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Arial", self.cell_font_size))
                item.setForeground(self.cell_text_color)
                item.setBackground(self.cell_bg_color)
                self.table.setItem(i, j, item)

    def toggle_game(self):
        if self.game_active:
            self.stop_game()
        else:
            self.start_game()

    def start_game(self):
        self.game_active = True
        self.current_target = 1
        self.target_label.setText(str(self.current_target))
        self.start_button.setText("Стоп")
        self.last_hovered_cell = None

        # Сброс и запуск таймера
        self.start_time = time.time()
        self.timer.start(10)  # Обновление каждые 10 мс

        # Установка таймера для режимов удержания внимания
        mode = self.game_mode_combo.currentText()
        if mode.startswith("Удержание"):
            if "3с" in mode:
                interval = 3000
            elif "5с" in mode:
                interval = 5000
            else:
                interval = 10000
            self.attention_timer.start(interval)

        # Генерация новой таблицы
        self.generate_table()

    def stop_game(self):
        self.game_active = False
        self.start_button.setText("Старт")
        self.timer.stop()
        self.attention_timer.stop()

    def update_timer(self):
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        milliseconds = int((elapsed % 1) * 1000)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}")

    def attention_timeout(self):
        if self.game_active:
            self.increment_target()

    def cell_clicked(self, row, col):
        if not self.game_active:
            return

        mode = self.game_mode_combo.currentText()
        item = self.table.item(row, col)

        if mode in ["Нажатие с обновлением", "Игра по нажатию"]:
            if item and item.text() == str(self.current_target):
                self.increment_target()
                if mode == "Нажатие с обновлением":
                    self.generate_table()

    def increment_target(self):
        self.current_target += 1
        self.target_label.setText(str(self.current_target))

        # Проверка на завершение игры
        if self.current_target > self.rows_spin.value() * self.cols_spin.value():
            self.stop_game()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_game()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SchulteTableApp()
    ex.show()
    sys.exit(app.exec_())