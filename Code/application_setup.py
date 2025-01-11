import pygame
import pyperclip
from Code.utilities import move_number_to_desired_range
from Code.Editor.editor_loop import editor_loop, EditorSingleton
from typing import Callable
from Code.utilities import COLORS


def application_setup():
    pygame.init()
    #
    # timing
    Time = TimingClass()
    #
    # keys
    Keys = KeysClass()
    #
    # cursor
    Cursor = CursorClass()
    #
    return Time, Keys, Cursor


class ApiObject():
    def __init__(self, Render):
        self.scroll_x = 0
        self.scroll_y = 0
        self.EDITOR = 'Editor'
        self.GAME = 'Game'
        self.MENU = 'Menu'
        self.setup_required = True
        self.current_api = self.EDITOR
        self.api_options = {self.EDITOR: editor_loop,
                            self.GAME: False, 
                            self.MENU: False,}
        self.api_singletons = {self.EDITOR: EditorSingleton,
                               self.GAME: False, 
                               self.MENU: False,}
        self.api_initiated_singletons = {self.EDITOR: 0,
                                         self.GAME: 0, 
                                         self.MENU: 0,}


class TimingClass():
    _TEXT_PIXEL_SIZE = 4

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.desired_fps = 60
        self.previous_tick = pygame.time.get_ticks()
        self.current_tick = pygame.time.get_ticks()
        self.fps = self.desired_fps
        self.delta_time = (self.current_tick - self.previous_tick) / 1000
    #
    def update(self):
        self.previous_tick = self.current_tick
        self.current_tick = pygame.time.get_ticks()
        self.delta_time = (self.current_tick - self.previous_tick) / 1000
        self.delta_time = move_number_to_desired_range(0.001, self.delta_time, 99999999999)
        self.fps = 1 / self.delta_time
        self.clock.tick(self.desired_fps)
    #
    def display_fps(self, Screen, Render, gl_context, lt: list[int, int]):
        fps = str(round(self.fps / 10) * 10)
        Render.draw_string_of_characters(Screen, gl_context, fps, lt, TimingClass._TEXT_PIXEL_SIZE, COLORS['BLACK'])


class CursorClass():
    def __init__(self):
        self.cursors = {
            # [offset_x, offset_y, priority]
            # higher priority > lower priority
            'cursor_arrow': [0, 0, 1],
            'cursor_crosshair': [-3, -3, 5],
            'cursor_nesw': [-13, -13, 99],
            'cursor_eyedrop': [0, -21, 6],
            'cursor_i_beam': [-6, -9, 2]
            }
        self.current_cursor = ['', 0]
        self.last_cursor = ['', 0]
        self.reset_current_cursor()
    #
    def update_cursor(self, Screen, gl_context, Render, Keys):
        match self.current_cursor[0]:
            case 'cursor_arrow' | 'cursor_crosshair' | 'cursor_nesw' | 'cursor_eyedrop':
                Render.basic_rect_ltwh_to_quad(Screen, gl_context, self.current_cursor[0], [Keys.cursor_x_pos.value + self.cursors[self.current_cursor[0]][0], Keys.cursor_y_pos.value + self.cursors[self.current_cursor[0]][1], Render.renderable_objects[self.current_cursor[0]].ORIGINAL_WIDTH, Render.renderable_objects[self.current_cursor[0]].ORIGINAL_HEIGHT])
            case 'cursor_i_beam':
                Render.invert_white(Screen, gl_context, self.current_cursor[0], [Keys.cursor_x_pos.value + self.cursors[self.current_cursor[0]][0], Keys.cursor_y_pos.value + self.cursors[self.current_cursor[0]][1], Render.renderable_objects[self.current_cursor[0]].ORIGINAL_WIDTH, Render.renderable_objects[self.current_cursor[0]].ORIGINAL_HEIGHT], COLORS['BLACK'])
        self.last_cursor = self.current_cursor
        self.reset_current_cursor()
    #
    def add_cursor_this_frame(self, added_cursor: str):
        # if priority of the added cursor is higher than the priority of the current highest priority cursor
        if self.cursors[added_cursor][2] > self.current_cursor[1]:
            self.current_cursor = [added_cursor, self.cursors[added_cursor][2]]
    #
    def reset_current_cursor(self):
        self.current_cursor = ['', 0]
    #
    @staticmethod
    def set_cursor_visibility(visible: bool):
        pygame.mouse.set_visible(visible)
    #
    @staticmethod
    def cursor_is_visible():
        return pygame.mouse.get_visible()


class IOKey():
    def __init__(self, mapping):
        self.mapping = mapping
        self.pressed = False
        self.last_pressed = False
        self.newly_pressed = False
        self.released = False
    #
    def update(self, new_value):
        self.last_pressed = self.pressed
        self.pressed = new_value
        self.newly_pressed = self.pressed and not self.last_pressed
        self.released = not self.pressed and self.last_pressed


class AnalogKey():
    def __init__(self, mapping):
        self.mapping = mapping
        self.value = -1
        self.last_value = -1
        self.delta = -1
    #
    def update(self, new_value):
        self.last_value = self.value
        self.value = new_value
        self.delta = self.value - self.last_value


class KeysClass():
    def __init__(self):
        # keyboard
        self.using_keyboard = True
        self.keys = -1
        self.left_click, self.middle_click, self.right_click = -1, -1, -1
        self.mouse_x_pos, self.mouse_y_pos = -1, -1
        self.scroll_x, self.scroll_y = 0, 0
        #
        self.update_io_and_analog: Callable
        self.get_update_function()
        #
        # mapping
        self.ANALOG_MAPPING = {
            # mouse position
            'MOUSE_X_POS': lambda: self.mouse_x_pos,
            'MOUSE_Y_POS': lambda: self.mouse_y_pos,
            'SCROLL_X': lambda: self.scroll_x,
            'SCROLL_Y': lambda: self.scroll_y,
        }
        self.IO_MAPPING = {
            # keyboard
            'BACKSPACE': lambda: self.keys[pygame.K_BACKSPACE],
            'TAB': lambda: self.keys[pygame.K_TAB],
            'RETURN': lambda: self.keys[pygame.K_RETURN],
            'ESCAPE': lambda: self.keys[pygame.K_ESCAPE],
            'SPACE': lambda: self.keys[pygame.K_SPACE],
            ',': lambda: self.keys[pygame.K_COMMA],
            '-': lambda: self.keys[pygame.K_MINUS],
            '.': lambda: self.keys[pygame.K_PERIOD],
            '/': lambda: self.keys[pygame.K_SLASH],
            '0': lambda: self.keys[pygame.K_0],
            '1': lambda: self.keys[pygame.K_1],
            '2': lambda: self.keys[pygame.K_2],
            '3': lambda: self.keys[pygame.K_3],
            '4': lambda: self.keys[pygame.K_4],
            '5': lambda: self.keys[pygame.K_5],
            '6': lambda: self.keys[pygame.K_6],
            '7': lambda: self.keys[pygame.K_7],
            '8': lambda: self.keys[pygame.K_8],
            '9': lambda: self.keys[pygame.K_9],
            ';': lambda: self.keys[pygame.K_SEMICOLON],
            '=': lambda: self.keys[pygame.K_EQUALS],
            '[': lambda: self.keys[pygame.K_LEFTBRACKET],
            ']': lambda: self.keys[pygame.K_RIGHTBRACKET],
            'A': lambda: self.keys[pygame.K_a],
            'B': lambda: self.keys[pygame.K_b],
            'C': lambda: self.keys[pygame.K_c],
            'D': lambda: self.keys[pygame.K_d],
            'E': lambda: self.keys[pygame.K_e],
            'F': lambda: self.keys[pygame.K_f],
            'G': lambda: self.keys[pygame.K_g],
            'H': lambda: self.keys[pygame.K_h],
            'I': lambda: self.keys[pygame.K_i],
            'J': lambda: self.keys[pygame.K_j],
            'K': lambda: self.keys[pygame.K_k],
            'L': lambda: self.keys[pygame.K_l],
            'M': lambda: self.keys[pygame.K_m],
            'N': lambda: self.keys[pygame.K_n],
            'O': lambda: self.keys[pygame.K_o],
            'P': lambda: self.keys[pygame.K_p],
            'Q': lambda: self.keys[pygame.K_q],
            'R': lambda: self.keys[pygame.K_r],
            'S': lambda: self.keys[pygame.K_s],
            'T': lambda: self.keys[pygame.K_t],
            'U': lambda: self.keys[pygame.K_u],
            'V': lambda: self.keys[pygame.K_v],
            'W': lambda: self.keys[pygame.K_w],
            'X': lambda: self.keys[pygame.K_x],
            'Y': lambda: self.keys[pygame.K_y],
            'Z': lambda: self.keys[pygame.K_z],
            'DELETE': lambda: self.keys[pygame.K_DELETE],
            'UP': lambda: self.keys[pygame.K_UP],
            'DOWN': lambda: self.keys[pygame.K_DOWN],
            'LEFT': lambda: self.keys[pygame.K_LEFT],
            'RIGHT': lambda: self.keys[pygame.K_RIGHT],
            'INSERT': lambda: self.keys[pygame.K_INSERT],
            'HOME': lambda: self.keys[pygame.K_HOME],
            'END': lambda: self.keys[pygame.K_END],
            'PAGE_UP': lambda: self.keys[pygame.K_PAGEUP],
            'PAGE_DOWN': lambda: self.keys[pygame.K_PAGEDOWN],
            'F1': lambda: self.keys[pygame.K_F1],
            'F2': lambda: self.keys[pygame.K_F2],
            'F3': lambda: self.keys[pygame.K_F3],
            'F4': lambda: self.keys[pygame.K_F4],
            'F5': lambda: self.keys[pygame.K_F5],
            'F6': lambda: self.keys[pygame.K_F6],
            'F7': lambda: self.keys[pygame.K_F7],
            'F8': lambda: self.keys[pygame.K_F8],
            'F9': lambda: self.keys[pygame.K_F9],
            'F10': lambda: self.keys[pygame.K_F10],
            'F11': lambda: self.keys[pygame.K_F11],
            'F12': lambda: self.keys[pygame.K_F12],
            'CAPSLOCK': lambda: self.keys[pygame.K_CAPSLOCK],
            'SHIFT': lambda: self.keys[pygame.K_RSHIFT] or self.keys[pygame.K_LSHIFT],
            'CONTROL': lambda: self.keys[pygame.K_RCTRL] or self.keys[pygame.K_LCTRL],
            'ALT': lambda: self.keys[pygame.K_RALT] or self.keys[pygame.K_LALT],
            # mouse clicks
            'LEFT_CLICK': lambda: self.left_click,
            'MIDDLE_CLICK': lambda: self.middle_click,
            'RIGHT_CLICK': lambda: self.right_click,
            }
        #
        # controls
        # common
        self.cursor_x_pos = AnalogKey(mapping=self.ANALOG_MAPPING['MOUSE_X_POS'])
        self.cursor_y_pos = AnalogKey(mapping=self.ANALOG_MAPPING['MOUSE_Y_POS'])
        # editor
        self.editor_primary = IOKey(mapping=self.IO_MAPPING['LEFT_CLICK'])
        self.editor_up = IOKey(mapping=self.IO_MAPPING['UP'])
        self.editor_left = IOKey(mapping=self.IO_MAPPING['LEFT'])
        self.editor_down = IOKey(mapping=self.IO_MAPPING['DOWN'])
        self.editor_right = IOKey(mapping=self.IO_MAPPING['RIGHT'])
        self.editor_shift = IOKey(mapping=self.IO_MAPPING['SHIFT'])
        self.editor_control = IOKey(mapping=self.IO_MAPPING['CONTROL'])
        self.editor_tab = IOKey(mapping=self.IO_MAPPING['TAB'])
        self.editor_scroll_x = AnalogKey(mapping=self.ANALOG_MAPPING['SCROLL_X'])
        self.editor_scroll_y = AnalogKey(mapping=self.ANALOG_MAPPING['SCROLL_Y'])
        # main game
        self.primary = IOKey(mapping=self.IO_MAPPING['LEFT_CLICK'])
        self.secondary = IOKey(mapping=self.IO_MAPPING['RIGHT_CLICK'])
        self.release_grapple = IOKey(mapping=self.IO_MAPPING['SPACE'])
        self.float_up = IOKey(mapping=self.IO_MAPPING['W'])
        self.left = IOKey(mapping=self.IO_MAPPING['A'])
        self.sink_down = IOKey(mapping=self.IO_MAPPING['S'])
        self.right = IOKey(mapping=self.IO_MAPPING['D'])
        self.select = IOKey(mapping=self.IO_MAPPING['RETURN'])
        self.interact = IOKey(mapping=self.IO_MAPPING['E'])
        self.pause = IOKey(mapping=self.IO_MAPPING['ESCAPE'])
        #
        self.controls = [
            # common
            self.cursor_x_pos, self.cursor_y_pos, 
            # editor
            self.editor_primary, self.editor_up, self.editor_left, self.editor_down, self.editor_right, self.editor_shift, self.editor_control, self.editor_tab, self.editor_scroll_x, self.editor_scroll_y,
            # main game
            self.primary, self.secondary, self.release_grapple, self.float_up, self.left, self.sink_down, self.right, self.select, self.interact, self.pause,
        ]
    #
    def copy_text(self, text: str):
        pyperclip.copy(text)
    #
    def paste_text(self):
        return pyperclip.paste()
    #
    def update_controls(self, Api):
        self.update_io_and_analog(Api)
        self.apply_updates_to_controls()

    def get_update_function(self):
        if self.using_keyboard:
            self.update_io_and_analog = self.update_keyboard
            return
    #
    def update_keyboard(self, Api):
        self.keys = pygame.key.get_pressed()
        self.left_click, self.middle_click, self.right_click = pygame.mouse.get_pressed()
        self.mouse_x_pos, self.mouse_y_pos = pygame.mouse.get_pos()
        self.scroll_x, self.scroll_y = Api.scroll_x, Api.scroll_y
    #
    def apply_updates_to_controls(self):
        for control in self.controls:
            control.update(control.mapping())
    #
    def keyboard_key_to_character(self):
        if self.keys[pygame.K_LCTRL] or self.keys[pygame.K_RCTRL]:
            if self.keys[pygame.K_a]: return 'CTRL_A'
            if self.keys[pygame.K_c]: return 'CTRL_C'
            if self.keys[pygame.K_v]: return 'CTRL_V'
            if self.keys[pygame.K_x]: return 'CTRL_X'
            if self.keys[pygame.K_z]: return 'CTRL_Z'
            if self.keys[pygame.K_BACKSPACE]: return 'CTRL_BACKSPACE'
            if self.keys[pygame.K_DELETE]: return 'CTRL_DELETE'
        if self.keys[pygame.K_UP]: return 'UP'
        if self.keys[pygame.K_DOWN]: return 'DOWN'
        if self.keys[pygame.K_DELETE]: return 'DELETE'
        if self.keys[pygame.K_BACKSPACE]: return 'BACKSPACE'
        if self.keys[pygame.K_RETURN]: return 'RETURN'
        if self.keys[pygame.K_SPACE]: return ' '
        if not self.keys[pygame.K_LSHIFT] and not self.keys[pygame.K_RSHIFT]:
            if self.keys[pygame.K_0]: return '0'
            if self.keys[pygame.K_1]: return '1'
            if self.keys[pygame.K_2]: return '2'
            if self.keys[pygame.K_3]: return '3'
            if self.keys[pygame.K_4]: return '4'
            if self.keys[pygame.K_5]: return '5'
            if self.keys[pygame.K_6]: return '6'
            if self.keys[pygame.K_7]: return '7'
            if self.keys[pygame.K_8]: return '8'
            if self.keys[pygame.K_9]: return '9'
            if self.keys[pygame.K_a]: return 'a'
            if self.keys[pygame.K_b]: return 'b'
            if self.keys[pygame.K_c]: return 'c'
            if self.keys[pygame.K_d]: return 'd'
            if self.keys[pygame.K_e]: return 'e'
            if self.keys[pygame.K_f]: return 'f'
            if self.keys[pygame.K_g]: return 'g'
            if self.keys[pygame.K_h]: return 'h'
            if self.keys[pygame.K_i]: return 'i'
            if self.keys[pygame.K_j]: return 'j'
            if self.keys[pygame.K_k]: return 'k'
            if self.keys[pygame.K_l]: return 'l'
            if self.keys[pygame.K_m]: return 'm'
            if self.keys[pygame.K_n]: return 'n'
            if self.keys[pygame.K_o]: return 'o'
            if self.keys[pygame.K_p]: return 'p'
            if self.keys[pygame.K_q]: return 'q'
            if self.keys[pygame.K_r]: return 'r'
            if self.keys[pygame.K_s]: return 's'
            if self.keys[pygame.K_t]: return 't'
            if self.keys[pygame.K_u]: return 'u'
            if self.keys[pygame.K_v]: return 'v'
            if self.keys[pygame.K_w]: return 'w'
            if self.keys[pygame.K_x]: return 'x'
            if self.keys[pygame.K_y]: return 'y'
            if self.keys[pygame.K_z]: return 'z'
        else:
            if self.keys[pygame.K_0]: return ')'
            if self.keys[pygame.K_1]: return '!'
            if self.keys[pygame.K_2]: return '@'
            if self.keys[pygame.K_3]: return '#'
            if self.keys[pygame.K_4]: return '$'
            if self.keys[pygame.K_5]: return '%'
            if self.keys[pygame.K_6]: return '^'
            if self.keys[pygame.K_7]: return '&'
            if self.keys[pygame.K_8]: return '*'
            if self.keys[pygame.K_9]: return '('
            if self.keys[pygame.K_a]: return 'A'
            if self.keys[pygame.K_b]: return 'B'
            if self.keys[pygame.K_c]: return 'C'
            if self.keys[pygame.K_d]: return 'D'
            if self.keys[pygame.K_e]: return 'E'
            if self.keys[pygame.K_f]: return 'F'
            if self.keys[pygame.K_g]: return 'G'
            if self.keys[pygame.K_h]: return 'H'
            if self.keys[pygame.K_i]: return 'I'
            if self.keys[pygame.K_j]: return 'J'
            if self.keys[pygame.K_k]: return 'K'
            if self.keys[pygame.K_l]: return 'L'
            if self.keys[pygame.K_m]: return 'M'
            if self.keys[pygame.K_n]: return 'N'
            if self.keys[pygame.K_o]: return 'O'
            if self.keys[pygame.K_p]: return 'P'
            if self.keys[pygame.K_q]: return 'Q'
            if self.keys[pygame.K_r]: return 'R'
            if self.keys[pygame.K_s]: return 'S'
            if self.keys[pygame.K_t]: return 'T'
            if self.keys[pygame.K_u]: return 'U'
            if self.keys[pygame.K_v]: return 'V'
            if self.keys[pygame.K_w]: return 'W'
            if self.keys[pygame.K_x]: return 'X'
            if self.keys[pygame.K_y]: return 'Y'
            if self.keys[pygame.K_z]: return 'Z'
        return None
