from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.core.window import Window
from kivy.metrics import dp
import random
import time

# Language constants
LANGUAGES = {
    'En': 'English',
    'Ru': 'Русский',
    'Ch': '中文'
}

# English texts
TEXTS = {
    'En': {
        'header': "Schulte tables",
        'click_update': "Click - update",
        'tap_game': "Tap game",
        'hover_game': "Hover game",
        'update_every': "Update every",
        'update_3': "Update every 3s",
        'update_5': "Update every 5s",
        'update_10': "Update every 10s",
        'simple_mode': "Simple mode",
        'start': "Start",
        'stop': "Stop",
        'rows': "Rows: ",
        'cols': "Columns: "
    },
    'Ru': {
        'header': "Таблицы Шульте",
        'click_update': "Нажатие с обновлением",
        'tap_game': "Игра по нажатию",
        'hover_game': "Игра по наведению",
        'update_every': "Обновление каждые",
        'update_3': "Обновление каждые 3с",
        'update_5': "Обновление каждые 5с",
        'update_10': "Обновление каждые 10с",
        'simple_mode': "Простой режим",
        'start': "Старт",
        'stop': "Стоп",
        'rows': "Строки: ",
        'cols': "Столбцы: "
    },
    'Ch': {
        'header': "舒尔特表格",
        'click_update': "点击刷新模式",
        'tap_game': "点击游戏模式",
        'hover_game': "悬停游戏模式",
        'update_every': "自动刷新",
        'update_3': "每3秒刷新",
        'update_5': "每5秒刷新",
        'update_10': "每10秒刷新",
        'simple_mode': "简单模式",
        'start': "开始",
        'stop': "停止",
        'rows': "行数: ",
        'cols': "列数: "
    }
}

MODES = {
    'CLICK_UPDATE': 'click_update',
    'TAP_GAME': 'tap_game',
    'HOVER_GAME': 'hover_game',
    'UPDATE_3': 'update_3',
    'UPDATE_5': 'update_5',
    'UPDATE_10': 'update_10',
    'SIMPLE': 'simple_mode'
}


class DotOverlay(Widget):
    visible = BooleanProperty(False)
    color = ListProperty([1, 0, 0, 1])  # Red color
    radius = NumericProperty(dp(4))
    pos_offset = ListProperty([dp(3), dp(2)])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(visible=self.update_canvas)
        self.bind(size=self.update_canvas)
        self.bind(pos=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.visible:
            with self.canvas:
                Color(*self.color)
                center_x = self.center_x + self.pos_offset[0]
                center_y = self.center_y + self.pos_offset[1]
                Ellipse(pos=(center_x - self.radius, center_y - self.radius),
                        size=(self.radius * 2, self.radius * 2))


class SchulteTable(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = 4
        self.cols = 4
        self.cells = []
        self.current_hover = None
        self.bind(size=self.update_dot_position)

    def generate_table(self, rows, cols):
        self.clear_widgets()
        self.rows = rows
        self.cols = cols
        self.cells = []

        numbers = list(range(1, rows * cols + 1))
        random.shuffle(numbers)

        for i in range(rows * cols):
            btn = Button(text=str(numbers[i]),
                         font_size=dp(24),
                         background_normal='',
                         background_color=[1, 1, 1, 1],
                         color=[0, 0, 0, 1])
            btn.number = numbers[i]
            btn.bind(on_press=self.on_cell_click)
            btn.bind(on_enter=self.on_cell_enter)
            btn.bind(on_leave=self.on_cell_leave)
            self.cells.append(btn)
            self.add_widget(btn)

    def on_cell_click(self, instance):
        app = App.get_running_app()
        if app.game_active and app.game_mode in ['CLICK_UPDATE', 'TAP_GAME']:
            if instance.number == app.current_target:
                app.increment_target()
                if app.game_mode == 'CLICK_UPDATE':
                    self.generate_table(app.rows_spin, app.cols_spin)

    def on_cell_enter(self, instance):
        app = App.get_running_app()
        if app.game_active and app.game_mode == 'HOVER_GAME':
            if instance.number == app.current_target:
                instance.background_color = [0.8, 0.9, 1, 1]  # Highlight color
                app.increment_target()
            self.current_hover = instance

    def on_cell_leave(self, instance):
        instance.background_color = [1, 1, 1, 1]
        self.current_hover = None

    def update_dot_position(self, *args):
        app = App.get_running_app()
        if hasattr(app, 'dot_overlay'):
            app.dot_overlay.center = self.center


class SchulteTableApp(App):
    current_language = StringProperty('En')
    game_active = BooleanProperty(False)
    current_target = NumericProperty(1)
    timer_text = StringProperty('00:00.000')
    target_text = StringProperty('1')
    button_text = StringProperty('Start')
    rows_spin = NumericProperty(4)
    cols_spin = NumericProperty(4)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = 0
        self.timer_event = None
        self.attention_timer = None
        self.game_mode = 'HOVER_GAME'
        self.dot_visible = False

    def build(self):
        self.title = TEXTS[self.current_language]['header']
        self.root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        # Control panel
        controls = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))

        # Language selection
        self.language_spinner = Spinner(
            text='English',
            values=list(LANGUAGES.values()),
            size_hint=(None, None),
            size=(dp(100), dp(44))
        )
        self.language_spinner.bind(text=self.on_language_change)

        # Dot toggle
        self.dot_button = ToggleButton(
            text='+',
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            group='dot',
            font_size=dp(16)
        )
        self.dot_button.bind(state=self.on_dot_toggle)

        # Rows and columns spinners
        self.rows_spinner = Spinner(
            text=f"{TEXTS[self.current_language]['rows']}4",
            values=[f"{TEXTS[self.current_language]['rows']}{i}" for i in range(2, 11)],
            size_hint=(None, None),
            size=(dp(100), dp(44))
        )
        self.rows_spinner.bind(text=self.on_rows_change)

        self.cols_spinner = Spinner(
            text=f"{TEXTS[self.current_language]['cols']}4",
            values=[f"{TEXTS[self.current_language]['cols']}{i}" for i in range(2, 11)],
            size_hint=(None, None),
            size=(dp(100), dp(44))
        )
        self.cols_spinner.bind(text=self.on_cols_change)

        # Game mode
        self.mode_spinner = Spinner(
            text=TEXTS[self.current_language]['hover_game'],
            values=[
                TEXTS[self.current_language]['click_update'],
                TEXTS[self.current_language]['tap_game'],
                TEXTS[self.current_language]['hover_game'],
                TEXTS[self.current_language]['update_3'],
                TEXTS[self.current_language]['update_5'],
                TEXTS[self.current_language]['update_10'],
                TEXTS[self.current_language]['simple_mode']
            ],
            size_hint=(None, None),
            size=(dp(150), dp(44))
        )
        self.mode_spinner.bind(text=self.on_mode_change)

        # Target label
        self.target_label = Label(
            text='1',
            font_size=dp(36),
            color=[0, 0, 1, 1],
            size_hint=(None, None),
            size=(dp(80), dp(44))
        )

        # Timer label
        self.timer_label = Label(
            text='00:00.000',
            font_size=dp(24),
            color=[0, 0, 0, 1],
            size_hint=(None, None),
            size=(dp(150), dp(44))
        )

        # Start/Stop button
        self.start_button = Button(
            text=TEXTS[self.current_language]['start'],
            size_hint=(None, None),
            size=(dp(100), dp(44))
        )
        self.start_button.bind(on_press=self.toggle_game)

        # Add controls to panel
        controls.add_widget(self.language_spinner)
        controls.add_widget(self.dot_button)
        controls.add_widget(self.rows_spinner)
        controls.add_widget(self.cols_spinner)
        controls.add_widget(self.mode_spinner)
        controls.add_widget(self.target_label)
        controls.add_widget(self.timer_label)
        controls.add_widget(self.start_button)

        # Table
        self.table = SchulteTable()

        # Dot overlay
        self.dot_overlay = DotOverlay(size=self.table.size)
        self.table.add_widget(self.dot_overlay)
        self.dot_overlay.visible = False

        self.root.add_widget(controls)
        self.root.add_widget(self.table)

        # Generate initial table
        self.table.generate_table(self.rows_spin, self.cols_spin)

        return self.root

    def on_language_change(self, spinner, text):
        for code, name in LANGUAGES.items():
            if name == text:
                self.current_language = code
                break

        self.update_ui_language()

    def update_ui_language(self):
        self.title = TEXTS[self.current_language]['header']
        self.start_button.text = TEXTS[self.current_language]['start'] if not self.game_active else \
        TEXTS[self.current_language]['stop']

        # Update spinners text
        self.rows_spinner.text = f"{TEXTS[self.current_language]['rows']}{self.rows_spin}"
        self.rows_spinner.values = [f"{TEXTS[self.current_language]['rows']}{i}" for i in range(2, 11)]

        self.cols_spinner.text = f"{TEXTS[self.current_language]['cols']}{self.cols_spin}"
        self.cols_spinner.values = [f"{TEXTS[self.current_language]['cols']}{i}" for i in range(2, 11)]

        # Update mode spinner
        mode_texts = [
            TEXTS[self.current_language]['click_update'],
            TEXTS[self.current_language]['tap_game'],
            TEXTS[self.current_language]['hover_game'],
            TEXTS[self.current_language]['update_3'],
            TEXTS[self.current_language]['update_5'],
            TEXTS[self.current_language]['update_10'],
            TEXTS[self.current_language]['simple_mode']
        ]

        current_mode_text = self.mode_spinner.text
        self.mode_spinner.values = mode_texts

        # Try to keep the same mode if possible
        for mode_text in mode_texts:
            if mode_text == current_mode_text:
                self.mode_spinner.text = mode_text
                break
        else:
            # Default to hover game if exact match not found
            self.mode_spinner.text = TEXTS[self.current_language]['hover_game']

    def on_dot_toggle(self, instance, state):
        self.dot_visible = state == 'down'
        self.dot_overlay.visible = self.dot_visible

    def on_rows_change(self, spinner, text):
        prefix = TEXTS[self.current_language]['rows']
        self.rows_spin = int(text[len(prefix):])
        if self.game_active:
            self.table.generate_table(self.rows_spin, self.cols_spin)

    def on_cols_change(self, spinner, text):
        prefix = TEXTS[self.current_language]['cols']
        self.cols_spin = int(text[len(prefix):])
        if self.game_active:
            self.table.generate_table(self.rows_spin, self.cols_spin)

    def on_mode_change(self, spinner, text):
        for mode, key in MODES.items():
            if text == TEXTS[self.current_language][key]:
                self.game_mode = mode
                break

    def toggle_game(self, instance):
        if self.game_active:
            self.stop_game()
        else:
            self.start_game()
        self.update_button_text()

    def start_game(self):
        self.game_active = True
        self.current_target = 1
        self.target_label.text = str(self.current_target)
        self.target_label.color = [0, 0, 1, 1]  # Blue for current target
        self.update_button_text()

        self.start_time = time.time()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.01)

        if self.game_mode in ['UPDATE_3', 'UPDATE_5', 'UPDATE_10']:
            interval = 3 if self.game_mode == 'UPDATE_3' else 5 if self.game_mode == 'UPDATE_5' else 10
            self.attention_timer = Clock.schedule_interval(self.attention_timeout, interval)

        self.table.generate_table(self.rows_spin, self.cols_spin)

    def stop_game(self):
        self.game_active = False
        self.update_button_text()
        if self.timer_event:
            self.timer_event.cancel()
        if self.attention_timer:
            self.attention_timer.cancel()

    def update_button_text(self):
        self.button_text = TEXTS[self.current_language]['stop'] if self.game_active else TEXTS[self.current_language][
            'start']
        self.start_button.text = self.button_text

    def update_timer(self, dt):
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        milliseconds = int((elapsed % 1) * 1000)
        self.timer_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        self.timer_label.text = self.timer_text

    def attention_timeout(self, dt):
        if self.game_active:
            max_cells = self.rows_spin * self.cols_spin
            if self.current_target <= max_cells:
                self.increment_target()
                self.table.generate_table(self.rows_spin, self.cols_spin)
            else:
                self.attention_timer.cancel()

    def increment_target(self):
        max_cells = self.rows_spin * self.cols_spin
        if self.current_target <= max_cells:
            self.current_target += 1
            if self.current_target > max_cells:
                self.target_text = str(max_cells)
                self.target_label.color = [0, 0.5, 0, 1]  # Green for completed
            else:
                self.target_text = str(self.current_target)
                self.target_label.color = [0, 0, 1, 1]  # Blue for current target
            self.target_label.text = self.target_text

        if self.current_target > max_cells:
            self.stop_game()

    def on_key_down(self, window, key, *args):
        if key == 32:  # Space key
            self.toggle_game(None)

    def on_start(self):
        Window.bind(on_key_down=self.on_key_down)


if __name__ == '__main__':
    SchulteTableApp().run()