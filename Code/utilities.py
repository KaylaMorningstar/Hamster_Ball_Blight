import os
import math
from __main__ import PATH
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename


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


def round_scaled(value: float | int, scale: float | int):
    return scale * round(value / scale)


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


def get_blended_color(background_rgba: list[float, float, float, float], foreground_rgba: list[float, float, float, float]):
    return [
        (foreground_rgba[0] * foreground_rgba[3]) + (background_rgba[0] * (1.0 - foreground_rgba[3])),
        (foreground_rgba[1] * foreground_rgba[3]) + (background_rgba[1] * (1.0 - foreground_rgba[3])),
        (foreground_rgba[2] * foreground_rgba[3]) + (background_rgba[2] * (1.0 - foreground_rgba[3])),
        1
    ]


def percent_to_rgba(rgba: list[float, float, float, float] | tuple[float, float, float, float]):
    return (
        round(rgba[0] * 255), 
        round(rgba[1] * 255), 
        round(rgba[2] * 255), 
        round(rgba[3] * 255)
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


LINE_OVERLAP_NONE = 0
LINE_THICKNESS_MIDDLE = 0
LINE_OVERLAP_MAJOR = 0x01
LINE_OVERLAP_MINOR = 0x02
LINE_OVERLAP_BOTH = 0x03
CIRCLE = 0
SQUARE = 1


def bresenham(x0, y0, x1, y1):
    points = []
    dx = x1 - x0
    dy = y1 - y0
    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1
    dx = abs(dx)
    dy = abs(dy)
    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0
    D = 2*dy - dx
    y = 0
    for x in range(dx + 1):
        points.append((x0 + x*xx + y*yx, y0 + x*xy + y*yy))
        if D >= 0:
            y += 1
            D -= 2*dx
        D += 2*dy
    return points


# def _bresenham(x1, y1, x2, y2, mode):
#     points = []
#     dx = x2 - x1
#     dy = y2 - y1
#     if (dx < 0):
#         dx = -dx
#         step_x = -1
#     else:
#         step_x = 1
#     if (dy < 0):
#         dy = -dy
#         step_y = -1
#     else:
#         step_y = +1
#     dxt2 = dx << 1
#     dyt2 = dy << 1
#     points.append((x1, y1))
#     if (dx > dy):
#         error = dyt2 - dx
#         while (x1 != x2):
#             x1 += step_x
#             if (error >= 0):
#                 if (mode & LINE_OVERLAP_MAJOR):
#                     points.append((x1, y1))
#                 y1 += step_y
#                 if (mode & LINE_OVERLAP_MINOR):
#                     points.append((x1 - step_x, y1))
#                 error -= dxt2
#             error += dyt2
#             points.append((x1, y1))
#     else:
#         error = dxt2 - dy
#         while (y1 != y2):
#             y1 += step_y
#             if (error >= 0):
#                 if (mode & LINE_OVERLAP_MAJOR):
#                     points.append((x1, y1))
#                 x1 += step_x
#                 if (mode & LINE_OVERLAP_MINOR):
#                     points.append((x1, y1 - step_y))
#                 error -= dyt2
#             error += dxt2
#             points.append((x1, y1))
#     return points


# def bresenham(x1, y1, x2, y2, thickness, mode):
#     points = []
#     dy = x1 - x2
#     dx = y2 - y1
#     if mode == CIRCLE:
#         angle = abs((abs(math.degrees(math.atan2(dx, dy))) % 90) - 45)
#         if angle != 0:
#             sin_theta = math.sin(math.radians(angle))
#             hypotnuse = 1 / sin_theta
#             thickness /= hypotnuse
#     if (dx < 0):
#         dx = -dx
#         step_x = -1
#     else:
#         step_x = +1
#     if (dy < 0):
#         dy = -dy
#         step_y = -1
#     else:
#         step_y = +1
#     dxt2 = dx << 1
#     dyt2 = dy << 1
#     if (dx > dy):
#         error = dyt2 - dx
#         i = thickness // 2
#         while i > 0:
#             x1 -= step_x
#             x2 -= step_x
#             if (error >= 0):
#                 y1 -= step_y
#                 y2 -= step_y
#                 error -= dxt2
#             error += dyt2
#             i -= 1
#         points.extend(_bresenham(x1, y1, x2, y2, LINE_THICKNESS_MIDDLE))
#         error = dyt2 - dx
#         i = thickness
#         while i > 1:
#             x1 += step_x
#             x2 += step_x
#             overlap = LINE_OVERLAP_NONE
#             if (error >= 0):
#                 y1 += step_y
#                 y2 += step_y
#                 error -= dxt2
#                 overlap = LINE_OVERLAP_BOTH
#             error += dyt2
#             points.extend(_bresenham(x1, y1, x2, y2, overlap))
#             i -= 1
#     else:
#         error = dxt2 - dy
#         i = thickness // 2
#         while i > 0:
#             y1 -= step_y
#             y2 -= step_y
#             if (error >= 0):
#                 x1 -= step_x
#                 x2 -= step_x
#                 error -= dyt2
#             error += dxt2
#             i -= 1
#         points.extend(_bresenham(x1, y1, x2, y2, LINE_THICKNESS_MIDDLE))
#         error = dxt2 - dy
#         i = thickness
#         while i > 1:
#             y1 += step_y
#             y2 += step_y
#             overlap = LINE_OVERLAP_NONE
#             if (error >= 0):
#                 x1 += step_x
#                 x2 += step_x
#                 error -= dyt2
#                 overlap = LINE_OVERLAP_BOTH
#             error += dxt2
#             points.extend(_bresenham(x1, y1, x2, y2, overlap))
#             i -= 1
#     return points


class CaseBreak(Exception):
    pass


ALWAYS_LOADED = 'ALWAYS_LOADED'
LOADED_IN_EDITOR = 'LOADED_IN_EDITOR'

IMAGE_PATHS = {
    # key: [Bool, path, draw_function_key]; 'always' to not unload image
    # blank images
    ' ': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\blanks\\blank_character.png'],
    # pixels
    'black_pixel': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\pixels\\black_pixel.png'],
    'blank_pixel': [[ALWAYS_LOADED], PATH + '\\Images\\always_loaded\\pixels\\blank_pixel.png'],
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
    # cursors
    'cursor_arrow': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_arrow.png'],
    'cursor_crosshair': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_crosshair.png'],
    'cursor_big_crosshair': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_big_crosshair.png'],
    'cursor_nesw': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_nesw.png'],
    'cursor_eyedrop': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_eyedrop.png'],
    'cursor_i_beam': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\cursors\\cursor_i_beam.png'],
    # common
    'editor_circle': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\common\\circle.png'],
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
    'Filled rectangle':  [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Filled rectangle.png'],
    'Empty ellipse':     [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Empty ellipse.png'],
    'Filled ellipse':    [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Filled ellipse.png'],
    'Blur':              [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Blur.png'],
    'Jumble':            [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Jumble.png'],
    'Eyedropper':        [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tools\\Eyedropper.png'],
    # tool attributes
    'brush_thickness': [[LOADED_IN_EDITOR], PATH + '\\Images\\not_always_loaded\\editor\\tool_attributes\\brush_thickness.png'],
    # test
    # 'map': [[LOADED_IN_EDITOR], 'C:\\Users\\Kayle\\Desktop\\OLD_HAMSTER\\HAMSTER_BALL_BLITZ\\data\\Images\\Forest\\Forest1.png']
}