import sys
import random
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSpinBox, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer, QEvent, QPoint, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush


HEADER_APP = "Schulte tables"
CLICK_UPDATE_MODE = "Click - update"
TAP_GAME_MODE = "Tap game"
HOVER_GAME_MODE = "Hover game"
UPDATE_EVERY_MODE = "Update every"
UPDATE_EVERY_3_MODE = "Update every 3с"
UPDATE_EVERY_5_MODE = "Update every 5с"
UPDATE_EVERY_10_MODE = "Update every 10с"
SIMPLE_GAME_MODE = "Simple mode"
START_BUTTON = "Start"
STOP_BUTTON = "Stop"
ADD_CENTER_X = 0
ADD_CENTER_Y = 0

class DotOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.dot_visible = False
        self.dot_color = QColor(255, 0, 0)  # Красная точка
        self.dot_radius = 6  # Размер точки

    def set_dot_visible(self, visible):
        self.dot_visible = visible
        self.update()

    def paintEvent(self, event):
        if self.dot_visible:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(self.dot_color))
            painter.setPen(Qt.NoPen)

            # Рисуем точку в центре виджета со смещением на 1 пиксель вправо и вниз
            center = self.rect().center()
            offset_center = QPoint(center.x() + 3, center.y() + 2)
            painter.drawEllipse(offset_center, self.dot_radius, self.dot_radius)
            painter.end()


class SchulteTableApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализируем игровые переменные
        self.game_active = False
        self.current_target = 1
        self.start_time = 0
        self.last_hovered_cell = None
        self.highlighted_cell = None  # Для хранения подсвеченной ячейки

        # Конфигурационные переменные
        self.timer_font_size = 24
        self.timer_text_color = QColor(0, 0, 0)
        self.timer_bg_color = QColor(240, 240, 240)

        self.target_font_size = 36
        self.target_font_family = "Arial"
        self.target_text_color = QColor(0, 0, 255)
        self.target_bg_color = QColor(240, 240, 240)
        self.target_completed_color = QColor(0, 128, 0)

        self.cell_font_size = 24
        self.cell_text_color = QColor(0, 0, 0)
        self.cell_bg_color = QColor(255, 255, 255)
        self.cell_highlight_color = QColor(200, 230, 255)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(HEADER_APP)
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)

        # Кнопка для отображения точки
        self.dot_button = QPushButton("+")
        self.dot_button.setCheckable(True)
        self.dot_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #aaa;
                min-width: 30px;
                max-width: 30px;
            }
            QPushButton:checked {
                background-color: #d0d0d0;
            }
        """)
        self.dot_button.toggled.connect(self.toggle_dot_visibility)

        # Элементы управления
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(2, 10)
        self.rows_spin.setValue(4)
        self.rows_spin.setPrefix("Rows: ")

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(2, 10)
        self.cols_spin.setValue(4)
        self.cols_spin.setPrefix("Columns: ")

        self.game_mode_combo = QComboBox()
        self.game_mode_combo.addItems([
            CLICK_UPDATE_MODE,
            TAP_GAME_MODE,
            HOVER_GAME_MODE,
            UPDATE_EVERY_3_MODE,
            UPDATE_EVERY_5_MODE,
            UPDATE_EVERY_10_MODE,
            SIMPLE_GAME_MODE
        ])
        self.game_mode_combo.setCurrentText(HOVER_GAME_MODE)

        self.target_label = QLabel("1")
        target_font = QFont(self.target_font_family, self.target_font_size)
        self.target_label.setFont(target_font)
        self.update_target_label_style()
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

        self.start_button = QPushButton(START_BUTTON)
        self.start_button.setMinimumWidth(100)
        self.start_button.clicked.connect(self.toggle_game)

        control_layout.addWidget(self.dot_button)
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

        self.table.setMouseTracking(True)
        self.table.viewport().installEventFilter(self)

        # Оверлей для точки
        self.dot_overlay = DotOverlay(self.table)
        self.dot_overlay.hide()
        self.table.viewport().stackUnder(self.dot_overlay)

        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.table)

        # Таймеры
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.attention_timer = QTimer()
        self.attention_timer.timeout.connect(self.attention_timeout)

        self.generate_table()

    def toggle_dot_visibility(self, visible):
        if visible:
            self.dot_overlay.show()
            self.dot_overlay.set_dot_visible(True)
            self.update_dot_position()
        else:
            self.dot_overlay.set_dot_visible(False)
            self.dot_overlay.hide()

    def update_dot_position(self):
        if not hasattr(self, 'dot_overlay'):
            return

        if self.dot_button.isChecked():
            self.dot_overlay.setGeometry(self.table.viewport().rect())
            self.dot_overlay.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_dot_position()

    def clear_highlight(self):
        """Удаляет подсветку с активной ячейки"""
        if self.highlighted_cell:
            row, col = self.highlighted_cell
            item = self.table.item(row, col)
            if item:
                item.setBackground(self.cell_bg_color)
            self.highlighted_cell = None

    def update_target_label_style(self):
        max_cells = self.rows_spin.value() * self.cols_spin.value()
        if hasattr(self, 'current_target') and self.current_target > max_cells:
            color = self.target_completed_color
            self.target_label.setText(str(max_cells))
        else:
            color = self.target_text_color

        self.target_label.setStyleSheet(
            f"color: {color.name()}; "
            f"background-color: {self.target_bg_color.name()}; "
            "padding: 5px;"
        )

    def eventFilter(self, source, event):
        if (source is self.table.viewport() and
                event.type() == QEvent.MouseMove and
                self.game_active and
                self.game_mode_combo.currentText() == HOVER_GAME_MODE):

            pos = event.pos()
            item = self.table.itemAt(pos)
            if item is not None:
                row, col = item.row(), item.column()
                if (row, col) != self.last_hovered_cell:
                    # Удаляем подсветку с предыдущей ячейки
                    if self.last_hovered_cell:
                        prev_row, prev_col = self.last_hovered_cell
                        prev_item = self.table.item(prev_row, prev_col)
                        if prev_item:
                            prev_item.setBackground(self.cell_bg_color)

                    # Подсвечиваем новую ячейку
                    if item.text() == str(self.current_target):
                        item.setBackground(self.cell_highlight_color)
                        self.highlighted_cell = (row, col)
                    else:
                        self.highlighted_cell = None

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
        # Удаляем подсветку перед генерацией новой таблицы
        self.clear_highlight()

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

        # Обновляем положение точки после генерации таблицы
        self.update_dot_position()

    def toggle_game(self):
        if self.game_active:
            self.stop_game()
        else:
            self.start_game()

    def start_game(self):
        self.game_active = True
        self.current_target = 1
        self.target_label.setText(str(self.current_target))
        self.update_target_label_style()
        self.start_button.setText(STOP_BUTTON)
        self.last_hovered_cell = None
        self.clear_highlight()  # Очищаем подсветку при старте игры

        self.start_time = time.time()
        self.timer.start(10)

        mode = self.game_mode_combo.currentText()
        if mode.startswith(UPDATE_EVERY_MODE):
            if "3с" in mode:
                interval = 3000
            elif "5с" in mode:
                interval = 5000
            else:
                interval = 10000
            self.attention_timer.start(interval)

        self.generate_table()

    def stop_game(self):
        self.game_active = False
        self.start_button.setText(START_BUTTON)
        self.timer.stop()
        self.attention_timer.stop()
        self.clear_highlight()  # Очищаем подсветку при остановке игры

    def update_timer(self):
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        milliseconds = int((elapsed % 1) * 1000)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}")

    def attention_timeout(self):
        if self.game_active:
            max_cells = self.rows_spin.value() * self.cols_spin.value()
            if self.current_target <= max_cells:
                self.increment_target()
                self.generate_table()
            else:
                self.attention_timer.stop()

    def cell_clicked(self, row, col):
        if not self.game_active:
            return

        mode = self.game_mode_combo.currentText()
        item = self.table.item(row, col)

        if mode in [CLICK_UPDATE_MODE, TAP_GAME_MODE]:
            if item and item.text() == str(self.current_target):
                self.increment_target()
                if mode == CLICK_UPDATE_MODE:
                    self.generate_table()

    def increment_target(self):
        max_cells = self.rows_spin.value() * self.cols_spin.value()
        if self.current_target <= max_cells:
            self.current_target += 1
            if self.current_target > max_cells:
                self.target_label.setText(str(max_cells))
            else:
                self.target_label.setText(str(self.current_target))
            self.update_target_label_style()

        if self.current_target > max_cells:
            self.stop_game()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_game()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SchulteTableApp()
    ex.show()
    sys.exit(app.exec_())