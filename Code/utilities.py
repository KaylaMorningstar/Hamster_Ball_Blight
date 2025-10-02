import os
import math
from __main__ import PATH
import pathlib
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import pygame

ONE_FRAME_AT_60_FPS = 1/ 60
OFF_SCREEN = -99999
FILE_TYPES = {
    (FILE_ANY := '*'): '*',
    (FILE_TXT := '*.txt'): '.txt',
    (FILE_PNG := '*.png'): '.png',
    }


def select_file(*acceptable_files: tuple[str]):
    file_types = [(FILE_TYPES.get(acceptable_file), acceptable_file) for acceptable_file in acceptable_files]
    if any(map(lambda x: x[0] is None, file_types)):
        return ''
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    file_name = askopenfilename(filetypes=file_types,
                                title=f'Select a file of one of the following types: {", ".join(alias for (alias, _) in file_types)}')
    root.destroy()
    return file_name


def path_exists(path):
    return os.path.exists(path)


def create_folder(path):
    os.makedirs(path)


def get_all_paths_in_directory(directory: str, file_type: str = '*'):
    return pathlib.Path(directory).glob(file_type)


def str_can_be_int(string):
    try:
        int(string)
        return True
    except:
        return False


def str_can_be_float(string):
    try:
        float(string)
        return True
    except:
        return False


def str_can_be_hex(string):
    try:
        int(string, 16)
        return True
    except:
        return False


def angle_in_range(lower: float, theta: float, upper: float):
    # not inclusive of edges
    return (theta - lower) % 360 < (upper - lower) % 360


def difference_between_angles(angle1: float, angle2: float):
    return (angle2 - angle1 + 180) % 360 - 180


def round_scaled(value: float | int, scale: float | int):
    return scale * round(value / scale)


def ceil_scaled(value: float | int, scale: float | int):
    return scale * math.ceil(value / scale)


def floor_scaled(value: float | int, scale: float | int):
    return scale * math.floor(value / scale)


def switch_to_base10(string: str, base: int):
    return int(string, base)


def base10_to_hex(integer: int):
    return hex(integer)[2:]


def add_characters_to_front_of_string(string: str, desired_string_length: int, character: str):
    if len(string) >= desired_string_length:
        return string
    return character * (desired_string_length - len(string)) + string


def get_time():
    return time.time_ns() / 1000000000


def point_is_in_ltwh(px: (float | int), py: (float | int), ltwh: list[(float | int), (float | int), (float | int), (float | int)]):
    return (ltwh[0] <= px <= ltwh[0] + ltwh[2]) and (ltwh[1] <= py <= ltwh[1] + ltwh[3])


def get_rect_minus_borders(ltwh: list[(float | int), (float | int), (float | int), (float | int)], border_size: float | int):
    return [
        ltwh[0] + border_size,
        ltwh[1] + border_size,
        ltwh[2] - (2 * border_size),
        ltwh[3] - (2 * border_size)
        ]


def move_number_to_desired_range(low: (float | int), value: (float | int), high: (float | int)):
    if value < low:
        return low
    elif value > high:
        return high
    else:
        return value


def atan2(x: (float | int), y: (float | int)):
    return math.degrees(math.atan2(y, x)) % 360


def rgba_to_glsl(rgba: list[int, int, int, int] | tuple[int, int, int, int]):
    return (
        rgba[0] / 255, 
        rgba[1] / 255, 
        rgba[2] / 255, 
        rgba[3] / 255
        )


def get_blended_color_float(background_rgba: list[float, float, float, float], foreground_rgba: list[float, float, float, float]):
    return [
        (foreground_rgba[0] * foreground_rgba[3]) + (background_rgba[0] * (1.0 - foreground_rgba[3])),
        (foreground_rgba[1] * foreground_rgba[3]) + (background_rgba[1] * (1.0 - foreground_rgba[3])),
        (foreground_rgba[2] * foreground_rgba[3]) + (background_rgba[2] * (1.0 - foreground_rgba[3])),
        1
    ]


def get_blended_color_int(background_rgba: list[int, int, int, int] | pygame.Color, foreground_rgba: list[int, int, int, int] | pygame.Color):
    percent_alpha = (foreground_rgba[3] / 255)
    inverse_percent_alpha = ((255 - foreground_rgba[3]) / 255)
    return (
        int((foreground_rgba[0] * percent_alpha) + (background_rgba[0] * inverse_percent_alpha)),
        int((foreground_rgba[1] * percent_alpha) + (background_rgba[1] * inverse_percent_alpha)),
        int((foreground_rgba[2] * percent_alpha) + (background_rgba[2] * inverse_percent_alpha)),
        int((foreground_rgba[3] * percent_alpha) + (background_rgba[3] * inverse_percent_alpha))
    )


def percent_to_rgba(rgba: list[float, float, float, float] | tuple[float, float, float, float]):
    return (
        round(rgba[0] * 255), 
        round(rgba[1] * 255), 
        round(rgba[2] * 255), 
        round(rgba[3] * 255)
        )


def rgba_to_bgra(rgba: list[float, float, float, float] | tuple[float, float, float, float]):
    return (
        rgba[2],
        rgba[1],
        rgba[0],
        rgba[3],
    )


COLORS = {
    'NOTHING': rgba_to_glsl((0, 0, 0, 0)),
    'DEFAULT': rgba_to_glsl((0, 0, 0, 255)),
    'BLACK': rgba_to_glsl((0, 0, 0, 255)),
    'WHITE': rgba_to_glsl((255, 255, 255, 255)),
    'SHADY_RED': rgba_to_glsl((255, 128, 128, 255)),
    'RED': rgba_to_glsl((255, 0, 0, 255)),
    'GREEN': rgba_to_glsl((0, 255, 0, 255)),
    'BLUE': rgba_to_glsl((0, 0, 255, 255)),
    'PINK': rgba_to_glsl((215, 123, 186, 255)),
    'LIGHT_YELLOW': rgba_to_glsl((251, 242, 128, 200)),
    'YELLOW': rgba_to_glsl((255, 255, 0, 255)),
    'GREY': rgba_to_glsl((175, 175, 175, 255)),
    'LIGHT_GREY': rgba_to_glsl((215, 215, 215, 255)),
    'ORANGE': rgba_to_glsl((255, 184, 65, 255))
    }


def get_text_height(text_pixel_size: (int | float)):
    return text_pixel_size * 7


def get_text_width(Render, text, text_pixel_size):
    return sum([(Render.renderable_objects[character].ORIGINAL_WIDTH * text_pixel_size) + text_pixel_size for character in text]) - text_pixel_size


def loading_and_unloading_images_manager(Screen, Render, gl_context, IMAGE_PATHS, things_to_load, things_to_unload):
    for key, value in IMAGE_PATHS.items():
        criteria_for_loading = value[0]
        path = value[1]
        loading_the_image = len([item for item in criteria_for_loading if item in things_to_load])
        unloading_the_image = len([item for item in criteria_for_loading if item in things_to_unload])
        #
        if loading_the_image > 0:
            if key not in Render.renderable_objects.keys():
                Render.add_moderngl_texture_to_renderable_objects_dict(Screen, gl_context, path, key)
        if unloading_the_image > 0:
            if key in Render.renderable_objects.keys():
                Render.remove_moderngl_texture_from_renderable_objects_dict(key)


class CaseBreak(Exception):
    pass


ALWAYS_LOADED = 'ALWAYS_LOADED'
LOADED_IN_EDITOR = 'LOADED_IN_EDITOR'
LOADED_IN_GAME = 'LOADED_IN_GAME'
LOADED_IN_MENU = 'LOADED_IN_MENU'

IMAGE_PATHS = {
    # key: [Bool, path, draw_function_key]; 'always' to not unload image
    # blank images
    ' ': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\blanks\\blank_character.png'],
    # pixels
    'black_pixel': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\pixels\\black_pixel.png'],
    'blank_pixel': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\pixels\\blank_pixel.png'],
    'white_pixel': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\pixels\\white_pixel.png'],
    # lower case letters
    'a': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\a.png'],
    'b': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\b.png'],
    'c': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\c.png'],
    'd': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\d.png'],
    'e': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\e.png'],
    'f': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\f.png'],
    'g': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\g.png'],
    'h': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\h.png'],
    'i': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\i.png'],
    'j': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\j.png'],
    'k': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\k.png'],
    'l': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\l.png'],
    'm': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\m.png'],
    'n': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\n.png'],
    'o': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\o.png'],
    'p': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\p.png'],
    'q': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\q.png'],
    'r': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\r.png'],
    's': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\s.png'],
    't': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\t.png'],
    'u': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\u.png'],
    'v': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\v.png'],
    'w': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\w.png'],
    'x': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\x.png'],
    'y': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\y.png'],
    'z': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\lower_case\\z.png'],
    # upper case letters
    'A': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\a.png'],
    'B': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\b.png'],
    'C': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\c.png'],
    'D': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\d.png'],
    'E': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\e.png'],
    'F': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\f.png'],
    'G': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\g.png'],
    'H': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\h.png'],
    'I': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\i.png'],
    'J': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\j.png'],
    'K': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\k.png'],
    'L': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\l.png'],
    'M': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\m.png'],
    'N': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\n.png'],
    'O': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\o.png'],
    'P': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\p.png'],
    'Q': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\q.png'],
    'R': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\r.png'],
    'S': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\s.png'],
    'T': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\t.png'],
    'U': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\u.png'],
    'V': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\v.png'],
    'W': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\w.png'],
    'X': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\x.png'],
    'Y': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\y.png'],
    'Z': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\upper_case\\z.png'],
    # numbers
    '0': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n0.png'],
    '1': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n1.png'],
    '2': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n2.png'],
    '3': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n3.png'],
    '4': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n4.png'],
    '5': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n5.png'],
    '6': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n6.png'],
    '7': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n7.png'],
    '8': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n8.png'],
    '9': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\numbers\\n9.png'],
    # symbols
    "'": [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\apostraphe.png'],
    '*': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\asterisk.png'],
    '^': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\circumflex.png'],
    ':': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\colon.png'],
    ',': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\comma.png'],
    '=': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\equals.png'],
    '!': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\explanation.png'],
    '>': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\greater_than.png'],
    '[': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\left_bracket.png'],
    '(': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\left_parentheses.png'],
    '<': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\less_than.png'],
    '-': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\minus.png'],
    '×': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\multiplication.png'],
    '.': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\period.png'],
    '+': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\plus.png'],
    '?': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\question.png'],
    '"': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\quote.png'],
    ']': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\right_bracket.png'],
    ')': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\right_parentheses.png'],
    ';': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\semi_colon.png'],
    '_': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\underscore.png'],
    '#': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\pound.png'],
    '\\': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\back_slash.png'],
    '/': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\symbols\\forward_slash.png'],
    # editor cursors
    'cursor_arrow': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_arrow.png'],
    'cursor_crosshair': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_crosshair.png'],
    'cursor_big_crosshair': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_big_crosshair.png'],
    'cursor_nesw': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_nesw.png'],
    'cursor_eyedrop': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_eyedrop.png'],
    'cursor_i_beam': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_i_beam.png'],
    # common
    'editor_circle': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\common\\circle.png'],
    'level_dimensions': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\common\\level_dimensions.png'],
    # editor tools on right side of screen
    'Marquee rectangle': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Marquee rectangle.png'],
    'Lasso':             [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Lasso.png'],
    'Pencil':            [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Pencil.png'],
    'Eraser':            [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Eraser.png'],
    'Spray':             [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Spray.png'],
    'Hand':              [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Hand.png'],
    'Bucket':            [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Bucket.png'],
    'Line':              [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Line.png'],
    'Curvy line':        [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Curvy line.png'],
    'Empty rectangle':   [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Empty rectangle.png'],
    'Blur':              [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Blur.png'],
    'Jumble':            [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Jumble.png'],
    'Eyedropper':        [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Eyedropper.png'],
    # tool attributes
    'tool_attribute_outline': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tool_attributes\\tool_attribute_outline.png'],
    'tool_attribute_clock': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tool_attributes\\clock.png'],
    # editor modes
    'pretty_mode': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\modes\\pretty_mode.png'],
    'collision_mode': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\modes\\collision_mode.png'],
    'draw_mode': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\modes\\draw_mode.png'],
    'block_mode': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\modes\\block_mode.png'],
    'object_mode': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\modes\\object_mode.png'],
    # test
    # 'map': [[LOADED_IN_EDITOR], 'C:\\Users\\Kayle\\Desktop\\OLD_HAMSTER\\HAMSTER_BALL_BLITZ\\data\\Images\\Forest\\Forest1.png']
    # player
    'player_ball_front': [[LOADED_IN_GAME], PATH + '\\Images\\not_always_loaded\\game\\player\\ball_front.png'],
    'classic_spout': [[LOADED_IN_GAME], PATH + '\\Images\\not_always_loaded\\game\\player\\classic_spout.png'],
    # game cursors
    'classic_cursor1': [[LOADED_IN_GAME], PATH + '\\Images\\not_always_loaded\\cursors\\classic_cursor1.png'],
    'classic_cursor2': [[LOADED_IN_GAME], PATH + '\\Images\\not_always_loaded\\cursors\\classic_cursor2.png'],
}