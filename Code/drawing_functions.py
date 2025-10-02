from array import array
import math
from Code.utilities import atan2, get_text_height, get_text_width, rgba_to_bgra, angle_in_range, difference_between_angles, get_time
import pygame
import moderngl
import numpy as np
from typing import Callable, Iterable
from Code.Editor.editor_utilities import LineTool, get_perfect_circle_edge_angles_for_drawing_lines, get_perfect_square_edge_angles_for_drawing_lines


def initialize_display():
    Screen = ScreenObject()
    #
    gl_context = moderngl.create_context()
    gl_context.enable(moderngl.BLEND)
    Render = RenderObjects(gl_context)
    #
    return Screen, Render, gl_context


class ScreenObject():
    def __init__(self):
        self.window_resize: bool = False
        self.ACCEPTABLE_WIDTH_RANGE = [1000, 10000]
        self.ACCEPTABLE_HEIGHT_RANGE = [650, 10000]
        self.width = 1000
        self.height = 700
        self.aspect = self.width / self.height
        self.screen = pygame.display.set_mode((self.width, self.height), flags=(pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE), vsync=True)
        #self.screen = pygame.display.set_mode((self.width, self.height), flags=(pygame.OPENGL), vsync=True)
        self.display = pygame.Surface((self.width, self.height))
    #
    def update_aspect(self):
        self.aspect = self.width / self.height
    #
    def update(self):
        pygame.display.flip()


class RenderableObject():
    def __init__(self, Screen: ScreenObject, texture, width, height, rotation):
        self.texture = texture
        self.ORIGINAL_WIDTH = width
        self.ORIGINAL_HEIGHT = height
        self.rotation = rotation
        #
        topleft_x = -1.0
        topleft_y = 1.0
        topright_x = topleft_x + ((2 * self.ORIGINAL_WIDTH) / Screen.width)
        bottomleft_y = topleft_y - ((2 * self.ORIGINAL_HEIGHT) / Screen.height)
        center_x = (topleft_x + topright_x) / 2
        center_y = (topleft_y + bottomleft_y) / 2
        self.ORIGINAL_HYPOTNUSE = math.sqrt(abs(topleft_x - center_x)**2 + abs(topleft_y - center_y) / 2)
        #
        topleft_rot = atan2(-abs(center_x - topleft_x), abs(center_y - topleft_y))
        topright_rot = atan2(abs(center_x - topright_x), abs(center_y - topleft_y))
        bottomleft_rot = atan2(abs(center_x - topleft_x), -abs(center_y - bottomleft_y))
        bottomright_rot = atan2(-abs(center_x - topright_x), -abs(center_y - bottomleft_y))
        self.ORIGINAL_ROTATIONS = [topleft_rot, topright_rot, bottomleft_rot, bottomright_rot]


class RenderObjects():
    def __init__(self, gl_context):
        self.programs = {}
        self.get_programs(gl_context)  # 'program_name': program
        self.renderable_objects = {}  # 'object_name': RenderableObject
        self.stored_draws = {}  # 'draw_name': [render_function_reference, {kwargs: value}]
    #
    def get_programs(self, gl_context):
        self.programs['basic_rect'] = DrawBasicRect(gl_context)
        self.programs['rotation_rect'] = DrawRotationRect(gl_context)
        self.programs['basic_image_with_color'] = DrawImageWithColor(gl_context)
        self.programs['basic_rect_with_color'] = DrawBasicRectWithVariableColor(gl_context)
        self.programs['basic_rect_glow'] = DrawBasicRectGlow(gl_context)
        self.programs['basic_rect_circle_glow'] = DrawBasicRectCircleGlow(gl_context)
        self.programs['basic_outline'] = DrawBasicOutline(gl_context)
        self.programs['RGBA_picker'] = DrawRGBAPicker(gl_context)
        self.programs['spectrum_x'] = DrawSpectrumX(gl_context)
        self.programs['checkerboard'] = DrawCheckerboard(gl_context)
        self.programs['text'] = DrawText(gl_context)
        self.programs['invert_white'] = DrawInvertWhite(gl_context)
        self.programs['circle_outline'] = DrawCircleOutline(gl_context)
        self.programs['draw_circle'] = DrawCircle(gl_context)
        self.programs['draw_ellipse'] = DrawEllipse(gl_context)
        self.programs['draw_hollow_ellipse'] = DrawHollowEllipse(gl_context)
        self.programs['draw_line'] = DrawLine(gl_context)
        self.programs['draw_collision_tile'] = DrawCollisionTile(gl_context)
        self.programs['draw_water_jet'] = DrawWaterJet(gl_context)
    #
    def write_pixels(self, name: str, ltwh: tuple[int, int, int, int], rgba: tuple[int, int, int, int]):
        self.renderable_objects[name].texture.write(np.array(rgba_to_bgra(rgba), dtype=np.uint8).tobytes(), viewport=ltwh)
    #
    def write_pixels_from_pg_surface(self, name: str, pg_surface: pygame.Surface):
        self.renderable_objects[name].texture.write(pg_surface.get_buffer().raw)
    #
    def write_pixels_from_bytearray(self, name: str, byte_array: bytearray):
        self.renderable_objects[name].texture.write(byte_array)
    #
    def add_moderngl_texture_with_surface(self, Screen: ScreenObject, gl_context: moderngl.Context, pygame_image: pygame.Surface, name):
        width, height = pygame_image.get_size()
        texture = gl_context.texture((width, height), 4)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.swizzle = 'BGRA'
        texture.write(pygame_image.get_view('1'))
        rotation = 0
        self.renderable_objects[name] = RenderableObject(Screen, texture, width, height, rotation)
        return pygame_image
    #
    def add_moderngl_texture_to_renderable_objects_dict(self, Screen: ScreenObject, gl_context: moderngl.Context, path, name):
        pygame_image = pygame.image.load(path).convert_alpha()
        width, height = pygame_image.get_size()
        texture = gl_context.texture((width, height), 4)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.swizzle = 'BGRA'
        texture.write(pygame_image.get_view('1'))
        rotation = 0
        self.renderable_objects[name] = RenderableObject(Screen, texture, width, height, rotation)
        return pygame_image
    #
    def add_moderngl_texture_using_bytearray(self, Screen: ScreenObject, gl_context: moderngl.Context, byte_array: bytearray, bytes_per_pixel: int, width: int, height: int, name: str):
        texture = gl_context.texture((width, height), bytes_per_pixel)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.swizzle = 'RGBA'
        texture.write(byte_array)
        rotation = 0
        self.renderable_objects[name] = RenderableObject(Screen, texture, width, height, rotation)
        return pygame.image.frombytes(bytes(byte_array), (width, height), 'RGBA') if bytes_per_pixel == 4 else None
    #
    def add_moderngl_texture_scaled(self, Screen: ScreenObject, gl_context: moderngl.Context, path, name, scale):
        pygame_image = pygame.image.load(path).convert_alpha()
        width, height = [int(wh * scale) for wh in pygame_image.get_size()]
        pygame_image = pygame.transform.scale(pygame_image, (width, height))
        texture = gl_context.texture((width, height), 4)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.swizzle = 'BGRA'
        texture.write(pygame_image.get_view('1'))
        rotation = 0
        self.renderable_objects[name] = RenderableObject(Screen, texture, width, height, rotation)
        return pygame_image
    #
    def remove_moderngl_texture_from_renderable_objects_dict(self, name):
        self.renderable_objects[name].texture.release()
        del self.renderable_objects[name]
    #:
    def store_draw(self, draw_name: str, render_function_reference: Callable, kwargs_dict: dict):
        self.stored_draws[draw_name] = [render_function_reference, kwargs_dict]
    #
    def execute_stored_draw(self, Screen: ScreenObject, gl_context: moderngl.Context, draw_name: str):
        # 'draw_name': [render_function_reference, {kwargs: value}]
        self.stored_draws[draw_name][0](Screen, gl_context, **self.stored_draws[draw_name][1])
        del self.stored_draws[draw_name]
    #
    def basic_rect_ltwh_to_quad(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh):
        # 'basic_rect', DrawBasicRect
        program = self.programs['basic_rect'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def rotation_rect_ltwhr_to_quad(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwhr):
        # 'rotation_rect', DrawRotationRect
        program = self.programs['rotation_rect'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwhr[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwhr[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwhr[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwhr[3]) / Screen.height)
        program['rotation'] = math.radians(ltwhr[4])
        program['offset_x'] = (topleft_x + topright_x) / 2
        program['offset_y'] = (topleft_y + bottomleft_y) / 2
        program['aspect'] = Screen.aspect
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def basic_rect_ltwh_image_with_color(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, rgba):
        # 'basic_image_with_color', DrawImageWithColor
        program = self.programs['basic_image_with_color'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['alpha'] = rgba[3]
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def basic_rect_ltwh_with_color_to_quad(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, rgba):
        # 'basic_rect_with_color', DrawBasicRectWithVariableColor
        program = self.programs['basic_rect_with_color'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['alpha'] = rgba[3]
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def basic_rect_ltwh_glow(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, rgba, glowing_pixels):
        # 'basic_rect_glow', DrawBasicRectGlow
        new_ltwh = [ltwh[0] - glowing_pixels, ltwh[1] - glowing_pixels, ltwh[2] + (2 * glowing_pixels), ltwh[3] + (2 * glowing_pixels)]
        program = self.programs['basic_rect_glow'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * new_ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * new_ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * new_ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * new_ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['glowing_pixels'] = abs(1 - (ltwh[2] / new_ltwh[2]))
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def basic_rect_circle_ltwh_glow(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, rgba, glowing_pixels, brightness):
        # 'basic_rect_circle_glow', DrawBasicRectCircleGlow
        new_ltwh = [ltwh[0] - glowing_pixels, ltwh[1] - glowing_pixels, ltwh[2] + (2 * glowing_pixels), ltwh[3] + (2 * glowing_pixels)]
        program = self.programs['basic_rect_circle_glow'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * new_ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * new_ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * new_ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * new_ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['brightness'] = brightness
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def basic_outline_ltwh(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, rgba, outline_pixels):
        # 'basic_outline', DrawBasicOutline
        new_ltwh = [ltwh[0] - outline_pixels, ltwh[1] - outline_pixels, ltwh[2] + (2 * outline_pixels), ltwh[3] + (2 * outline_pixels)]
        program = self.programs['basic_outline'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * new_ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * new_ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * new_ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * new_ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def rgba_picker(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, saturation):
        # 'RGBA_picker', DrawRGBAPicker
        width = ltwh[2] / 6
        height = ltwh[3] / 2
        for left_index in range(6):
            left = ltwh[0] + (left_index * width)
            for top_index in range(2):
                top = ltwh[1] + (top_index * height)
                key = f'{str(left_index)}_{str(top_index)}'
                program = self.programs['RGBA_picker'].PROGRAMS[key]
                renderable_object = self.renderable_objects[object_name]
                topleft_x = (-1.0 + ((2 * left) / Screen.width)) * Screen.aspect
                topleft_y = 1.0 - ((2 * top) / Screen.height)
                topright_x = topleft_x + ((2 * width * Screen.aspect) / Screen.width)
                bottomleft_y = topleft_y - ((2 * height) / Screen.height)
                program['aspect'] = Screen.aspect
                program['saturation'] = saturation
                quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
                renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
                renderable_object.texture.use(0)
                renderer.render(mode=moderngl.TRIANGLE_STRIP)
                quads.release()
                renderer.release()
    #
    def spectrum_x(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, rgba1, rgba2):
        # 'spectrum_x', DrawSpectrumX
        program = self.programs['spectrum_x'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red1'] = rgba1[0]
        program['green1'] = rgba1[1]
        program['blue1'] = rgba1[2]
        program['alpha1'] = rgba1[3]
        program['red2'] = rgba2[0]
        program['green2'] = rgba2[1]
        program['blue2'] = rgba2[2]
        program['alpha2'] = rgba2[3]
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def checkerboard(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh, rgba1, rgba2, repeat_x, repeat_y, offset_x: int = 0, offset_y: int = 0):
        # 'checkerboard', DrawCheckerboard
        program = self.programs['checkerboard'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red1'] = rgba1[0]
        program['green1'] = rgba1[1]
        program['blue1'] = rgba1[2]
        program['alpha1'] = rgba1[3]
        program['red2'] = rgba2[0]
        program['green2'] = rgba2[1]
        program['blue2'] = rgba2[2]
        program['alpha2'] = rgba2[3]
        
        program['offset_x'] = float(offset_x) / ltwh[2]
        program['offset_y'] = float(offset_y) / ltwh[3]

        program['two_tiles_x'] = 2 / (ltwh[2] / repeat_x)
        program['two_tiles_y'] = 2 / (ltwh[3] / repeat_y)
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def draw_string_of_characters(self, Screen: ScreenObject, gl_context: moderngl.Context, string, lt, text_pixel_size, rgba):
        # 'text', DrawText
        ltwh = [lt[0], lt[1], 0, get_text_height(text_pixel_size)]
        for character in string:
            ltwh[2] = get_text_width(self, character, text_pixel_size)
            program = self.programs['text'].program
            renderable_object = self.renderable_objects[character]
            topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
            topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
            topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
            bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
            program['aspect'] = Screen.aspect
            program['red'] = rgba[0]
            program['green'] = rgba[1]
            program['blue'] = rgba[2]
            program['alpha'] = rgba[3]
            quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
            renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
            renderable_object.texture.use(0)
            renderer.render(mode=moderngl.TRIANGLE_STRIP)
            quads.release()
            renderer.release()
            ltwh[0] += ltwh[2] + text_pixel_size
    #
    def invert_white(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh):
        """
        NOTE: rgba is the color being inverted. For example, rgba should be black if black pixels are to be inverted.
        """
        # 'invert_white', DrawInvertWhite
        # result = (source * source_factor) + (destination * destination_factor)
        #gl_context.blend_func = (moderngl.ONE_MINUS_DST_COLOR, moderngl.ZERO, moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA)
        #gl_context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA, moderngl.ONE, moderngl.ZERO)
        #gl_context.blend_func = moderngl.ONE_MINUS_DST_COLOR, moderngl.ZERO
        #gl_context.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        #gl_context.blend_func = (moderngl.ONE_MINUS_DST_COLOR, moderngl.ZERO, moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        program = self.programs['invert_white'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
        #gl_context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA, moderngl.ONE, moderngl.ZERO)
        #gl_context.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
    #
    def editor_circle_outline(self, Screen: ScreenObject, gl_context: moderngl.Context, ltwh: list[int, int, int, int], circle_size: int, circle_outline_thickness: int, circle_pixel_size: int = 1, is_a_square: bool = False):
        # 'circle_outline', DrawCircleOutline
        #gl_context.blend_func = (moderngl.ONE_MINUS_DST_COLOR, moderngl.ZERO, moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        program = self.programs['circle_outline'].program
        renderable_object = self.renderable_objects['white_pixel']
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['width'] = ltwh[2]
        program['height'] = ltwh[3]
        program['circle_size'] = circle_size
        program['circle_pixel_size'] = circle_pixel_size
        program['circle_outline_thickness'] = circle_outline_thickness
        program['is_a_square'] = is_a_square
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
        #gl_context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA, moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
    #
    def draw_circle(self, Screen: ScreenObject, gl_context: moderngl.Context, ltwh: list[int, int, int, int], circle_size: int, circle_pixel_size: float, rgba):
        # 'draw_circle', DrawCircle
        program = self.programs['draw_circle'].program
        renderable_object = self.renderable_objects['black_pixel']
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['width'] = ltwh[2]
        program['height'] = ltwh[3]
        program['circle_size'] = circle_size
        program['circle_pixel_size'] = circle_pixel_size
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['alpha'] = rgba[3]
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def draw_ellipse(self, Screen: ScreenObject, gl_context: moderngl.Context, ltwh: list[int, int, int, int], ellipse_wh: list[int, int], pixel_size: float, rgba: list[float, float, float, float]):
        # 'draw_ellipse', DrawEllipse
        # only draw ellipses that are a pixel or bigger
        if any([dimension == 0 for dimension in ellipse_wh]) or any([dimension == 0 for dimension in ltwh]):
            return
        program = self.programs['draw_ellipse'].program
        renderable_object = self.renderable_objects['black_pixel']
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['width'] = ltwh[2]
        program['height'] = ltwh[3]
        program['ellipse_width'] = ellipse_wh[0]
        program['ellipse_height'] = ellipse_wh[1]
        program['pixel_size'] = pixel_size
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['alpha'] = rgba[3]
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def draw_hollow_ellipse(self, Screen: ScreenObject, gl_context: moderngl.Context, ltwh: list[int, int, int, int], ellipse_wh: list[int, int], pixel_size: float, ellipse_thickness: int, rgba: list[float, float, float, float]):
        # 'draw_hollow_ellipse', DrawHollowEllipse
        program = self.programs['draw_hollow_ellipse'].program
        renderable_object = self.renderable_objects['black_pixel']
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['width'] = ltwh[2]
        program['height'] = ltwh[3]
        program['ellipse_width'] = ellipse_wh[0]
        program['ellipse_height'] = ellipse_wh[1]
        program['pixel_size'] = pixel_size
        program['ellipse_thickness'] = ellipse_thickness
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['alpha'] = rgba[3]
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def draw_line(self, Screen: ScreenObject, gl_context: moderngl.Context, x1: int, y1: int, x2: int, y2: int, thickness: int, rgba, pixel_size: int | float = 1, circle_for_line_drawing = None, brush_style: int = LineTool.CIRCLE_BRUSH):
        # 'draw_line', DrawLine
        angle = (atan2(y2 - y1, x2 - x1) + 270) % 360
        if circle_for_line_drawing is None:
            match brush_style:
                case LineTool.CIRCLE_BRUSH:
                    circle_for_line_drawing = get_perfect_circle_edge_angles_for_drawing_lines(thickness)
                case LineTool.SQUARE_BRUSH:
                    circle_for_line_drawing = get_perfect_square_edge_angles_for_drawing_lines(thickness)
        # this function is inclusive of (x1, y1), (x2, y2)
        # dot, horizontal, or vertical
        if horizontal_or_vertical := ((x1 == x2) or (y1 == y2)):
            if ((x1 == x2) and (y1 == y2)):
                ltwh = [x1 - (((thickness - 1) // 2) * pixel_size), y1 - (((thickness - 1) // 2) * pixel_size), (thickness * pixel_size), (thickness * pixel_size)]
            if (x1 < x2):  # >
                x2 += pixel_size
                ltwh = [min(x1, x2) - (((thickness - 1) // 2) * pixel_size), y1 - (((thickness - 1) // 2) * pixel_size), abs(x2 - x1) + ((thickness - 1) * pixel_size), (thickness * pixel_size)]
            if (x1 > x2):  # <
                x1 += pixel_size
                ltwh = [min(x1, x2) - (((thickness - 1) // 2) * pixel_size), y1 - (((thickness - 1) // 2) * pixel_size), abs(x2 - x1) + ((thickness - 1) * pixel_size), (thickness * pixel_size)]
            if (y1 > y2):  # ^
                y1 += pixel_size
                ltwh = [x1 - (((thickness - 1) // 2) * pixel_size), min(y1, y2) - (((thickness - 1) // 2) * pixel_size), (thickness * pixel_size), abs(y2 - y1) + ((thickness - 1) * pixel_size)]
            if (y1 < y2):  # ↓
                y2 += pixel_size
                ltwh = [x1 - (((thickness - 1) // 2) * pixel_size), min(y1, y2) - (((thickness - 1) // 2) * pixel_size), (thickness * pixel_size), abs(y2 - y1) + ((thickness - 1) * pixel_size)]
        else:
            # octant 1 or 2
            if (y1 > y2) and (x1 < x2):
                y1 += pixel_size
                x2 += pixel_size
            # octant 3 or 4
            if (y1 > y2) and (x1 > x2):
                x1 += pixel_size
                y1 += pixel_size
            # octant 5 or 6
            if (y1 < y2) and (x1 > x2):
                x1 += pixel_size
                y2 += pixel_size
            # octant 7 or 8
            if (y1 < y2) and (x1 < x2):
                x2 += pixel_size
                y2 += pixel_size
        octant = ((angle // 45) + 1) if (not horizontal_or_vertical) else 0
        if (octant != 0):
            # get the ltwh
            if thickness % 2 == 0:
                ltwh = [min(x1, x2) - (((thickness - 1) // 2) * pixel_size), min(y1, y2) - (((thickness - 1) // 2) * pixel_size), abs(x2 - x1) + (2 * (((thickness // 2) - 0.5) * pixel_size)), abs(y2 - y1) + (2 * (((thickness // 2) - 0.5) * pixel_size))]
            if thickness % 2 == 1:
                ltwh = [min(x1, x2) - ((thickness // 2) * pixel_size), min(y1, y2) - ((thickness // 2) * pixel_size), abs(x2 - x1) + (2 * ((thickness // 2) * pixel_size)), abs(y2 - y1) + (2 * ((thickness // 2) * pixel_size))]
        # find two points on stamp 1 where bounds can be drawn for the line
        above_line_xy = [x1, y1, 0]
        below_line_xy = [x1, y1, 0]
        if not horizontal_or_vertical:
            center_x, center_y = thickness / 2, thickness / 2
            slope = ((y2 - y1) / (x2 - x1))
            intercept = (slope * -center_x) + center_y
            perpendicular_slope = -(1 / slope)
            for edge_pixel in circle_for_line_drawing:
                [column_index, row_index, radial_angle, [lower_angle, upper_angle]] = edge_pixel
                if (not angle_in_range(lower_angle, angle, upper_angle)) or (thickness < 4) or (brush_style == LineTool.SQUARE_BRUSH):
                    pixel_x = column_index + 0.5
                    pixel_y = row_index + 0.5
                    perpendicular_intercept = (perpendicular_slope * -pixel_x) + pixel_y
                    intersection_x = (perpendicular_intercept - intercept) / (slope - perpendicular_slope)
                    intersection_y = (slope * intersection_x) + intercept
                    distance_from_line = math.sqrt(((intersection_x - pixel_x) ** 2) + ((intersection_y - pixel_y) ** 2))
                    # above line
                    if pixel_y > (slope * pixel_x) + intercept:
                        if distance_from_line > above_line_xy[2]:
                            above_line_xy = [column_index, row_index, distance_from_line]
                    # below line
                    else:
                        if distance_from_line > below_line_xy[2]:
                            below_line_xy = [column_index, row_index, distance_from_line]
        program = self.programs['draw_line'].program
        renderable_object = self.renderable_objects['black_pixel']
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        program['red'] = rgba[0]
        program['green'] = rgba[1]
        program['blue'] = rgba[2]
        program['alpha'] = rgba[3]
        program['left'] = ltwh[0]
        program['top'] = ltwh[1]
        program['width'] = ltwh[2]
        program['height'] = ltwh[3]
        program['thickness'] = thickness
        program['px1'] = x1
        program['py1'] = y1
        program['px2'] = x2
        program['py2'] = y2
        program['outer_line_x1'] = above_line_xy[0]
        program['outer_line_y1'] = above_line_xy[1]
        program['outer_line_x2'] = below_line_xy[0]
        program['outer_line_y2'] = below_line_xy[1]
        program['octant'] = int(octant)
        program['pixel_size'] = pixel_size
        program['brush_style'] = brush_style
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def draw_collision_map_tile_in_editor(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ltwh):
        # 'draw_collision_tile', DrawCollisionTile
        program = self.programs['draw_collision_tile'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        program['aspect'] = Screen.aspect
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def draw_water_jet(self, Screen: ScreenObject, gl_context: moderngl.Context, object_name, ball_center: Iterable[float], ball_radius: float, max_length_from_center: float, current_length_from_center: float, rotation: float, minimum_water_jet_thickness: float, moment_in_wave_period: float):
        # 'draw_water_jet', DrawWaterJet
        ltwh = [ball_center[0] - current_length_from_center, ball_center[1] - current_length_from_center, 2 * current_length_from_center, 2 * current_length_from_center]
        program = self.programs['draw_water_jet'].program
        renderable_object = self.renderable_objects[object_name]
        topleft_x = (-1.0 + ((2 * ltwh[0]) / Screen.width)) * Screen.aspect
        topleft_y = 1.0 - ((2 * ltwh[1]) / Screen.height)
        topright_x = topleft_x + ((2 * ltwh[2] * Screen.aspect) / Screen.width)
        bottomleft_y = topleft_y - ((2 * ltwh[3]) / Screen.height)
        slope = -math.tan(math.radians(rotation))
        program['aspect'] = Screen.aspect
        program['width'] = ltwh[2]
        program['height'] = ltwh[3]
        program['slope'] = slope
        program['minimum_water_jet_thickness'] = minimum_water_jet_thickness
        program['current_length_from_center'] = current_length_from_center
        program['max_length_from_center'] = max_length_from_center
        program['rotation'] = rotation
        program['ball_radius'] = ball_radius
        program['moment_in_wave_period'] = moment_in_wave_period
        program['quad1'] = (315.0 <= rotation <= 360.0) or (0.0 <= rotation <= 135.0)
        program['quad2'] = (45.0 <= rotation <= 225.0)
        program['quad3'] = (135 <= rotation <= 315.0)
        program['quad4'] = (225.0 <= rotation <= 360.0) or (0.0 <= rotation <= 45.0)
        quads = gl_context.buffer(data=array('f', [topleft_x, topleft_y, 0.0, 0.0, topright_x, topleft_y, 1.0, 0.0, topleft_x, bottomleft_y, 0.0, 1.0, topright_x, bottomleft_y, 1.0, 1.0,]))
        renderer = gl_context.vertex_array(program, [(quads, '2f 2f', 'vert', 'texcoord')])
        renderable_object.texture.use(0)
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        quads.release()
        renderer.release()
    #
    def draw_rectangle(self, Screen: ScreenObject, gl_context: moderngl.Context, ltwh, border_thickness, border_color, coloring_border, inner_color, coloring_inside): # rectangle with border
        if coloring_border:
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0], ltwh[1], ltwh[2], border_thickness), border_color)
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0], ltwh[1] + border_thickness, border_thickness, ltwh[3] - border_thickness), border_color)
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0] + ltwh[2] - border_thickness, ltwh[1] + border_thickness, border_thickness, ltwh[3] - border_thickness), border_color)
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0] + border_thickness, ltwh[1] + ltwh[3] - border_thickness, ltwh[2] - (2 * border_thickness), border_thickness), border_color)
        if coloring_inside:
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0] + border_thickness, ltwh[1] + border_thickness, ltwh[2] - (2 * border_thickness), ltwh[3] - (2 * border_thickness)), inner_color)
    #
    def draw_part_of_rectangle(self, Screen: ScreenObject, gl_context, ltwh, border_thickness, border_color, coloring_up, coloring_left, coloring_down, coloring_right, inner_color, coloring_inside): # rectangle with border
        if coloring_up:
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0], ltwh[1], ltwh[2], border_thickness), border_color)
        if coloring_left:
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0], ltwh[1], border_thickness, ltwh[3]), border_color)
        if coloring_down:
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0], ltwh[1]+ltwh[3]-border_thickness, ltwh[2], border_thickness), border_color)
        if coloring_right:
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0]+ltwh[2]-border_thickness, ltwh[1], border_thickness, ltwh[3]), border_color)
        if coloring_inside:
            self.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', (ltwh[0] + border_thickness, ltwh[1] + border_thickness, ltwh[2] - (2 * border_thickness), ltwh[3] - (2 * border_thickness)), inner_color)
    #
    @staticmethod
    def clear_buffer(gl_context: moderngl.Context):
        gl_context.clear()


class DrawBasicRect():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = texture(tex, uvs);
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawRotationRect():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float rotation;
        uniform float offset_x;
        uniform float offset_y;
        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            vec2 sample_pos = vec2(
            offset_x + ((vert.x - offset_x) * cos(rotation)) - ((vert.y - offset_y) * sin(rotation)), 
            offset_y + ((vert.x - offset_x) * sin(rotation)) + ((vert.y - offset_y) * cos(rotation))
            );
            sample_pos.x /= aspect;
            gl_Position = vec4(sample_pos, 0.0, 1.0);
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(texture(tex, uvs).rgba);
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawBasicRectWithVariableColor():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float alpha;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(
            texture(tex, uvs).r + red, 
            texture(tex, uvs).g + green, 
            texture(tex, uvs).b + blue, 
            texture(tex, uvs).a + alpha
            );
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawImageWithColor():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float alpha;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(
            texture(tex, uvs).r + red, 
            texture(tex, uvs).g + green, 
            texture(tex, uvs).b + blue, 
            texture(tex, uvs).a * alpha
            );
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawText():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float alpha;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(
            texture(tex, uvs).r + red, 
            texture(tex, uvs).g + green, 
            texture(tex, uvs).b + blue, 
            texture(tex, uvs).a * alpha
            );
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawBasicRectGlow():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float glowing_pixels;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(
            texture(tex, uvs).r + red, 
            texture(tex, uvs).g + green, 
            texture(tex, uvs).b + blue, 
            min(abs((abs(0.5 - uvs.x) * 2) - 1), abs((abs(0.5 - uvs.y) * 2) - 1)) * (1 / glowing_pixels)
            );
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawBasicRectCircleGlow():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float brightness;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(
            texture(tex, uvs).r + red, 
            texture(tex, uvs).g + green, 
            texture(tex, uvs).b + blue, 
            abs(clamp(pow(pow(2*abs(uvs.x - 0.5), 2) + pow(2*abs(uvs.y - 0.5), 2), 0.5), 0 , 1) - 1) * brightness
            );
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawBasicOutline():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red;
        uniform float green;
        uniform float blue;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(
            texture(tex, uvs).r + red, 
            texture(tex, uvs).g + green, 
            texture(tex, uvs).b + blue, 
            texture(tex, uvs).a
            );
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawRGBAPicker():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADERS = {
        '0_0': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = 1;
            float green = 1 - ((1 - uvs.x) * uvs.y);
            float blue = (1 - uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '1_0': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = 1 - (uvs.x * uvs.y);
            float green = 1;
            float blue = (1 - uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '2_0': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = (1 - uvs.y);
            float green = 1;
            float blue = 1 - ((1 - uvs.x) * uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '3_0': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = (1 - uvs.y);
            float green = 1 - (uvs.x * uvs.y);
            float blue = 1;
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '4_0': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = 1 - ((1 - uvs.x) * uvs.y);
            float green = (1 - uvs.y);
            float blue = 1;
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '5_0': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = 1;
            float green = (1 - uvs.y);
            float blue = 1 - (uvs.x * uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '0_1': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = (1 - uvs.y);
            float green = uvs.x * (1 - uvs.y);
            float blue = 0;
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '1_1': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = (1-uvs.x) * (1-uvs.y);
            float green = (1 - uvs.y);
            float blue = 0;
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '2_1': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = 0;
            float green = (1 - uvs.y);
            float blue = uvs.x * (1 - uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '3_1': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = 0;
            float green = (1-uvs.x) * (1-uvs.y);
            float blue = (1 - uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '4_1': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = uvs.x * (1 - uvs.y);
            float green = 0;
            float blue = (1 - uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        ''',

        '5_1': 
        '''
        #version 430 core

        uniform sampler2D tex;
        uniform float saturation;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float red = (1 - uvs.y);
            float green = 0;
            float blue = (1-uvs.x) * (1-uvs.y);
            float max_color = max(max(red, green), blue);
            float min_color = min(min(red, green), blue);
            float middle_color = ((max_color - min_color) / 2) + min_color;
            float adjustment = (middle_color * (1 - saturation));
            red = (red * saturation) + adjustment;
            green = (green * saturation) + adjustment;
            blue = (blue * saturation) + adjustment;
            f_color = vec4(red, green, blue, texture(tex, uvs).a);
        }
        '''
        }
        self.PROGRAMS = {
        '0_0':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['0_0']),
        '1_0':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['1_0']),
        '2_0':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['2_0']),
        '3_0':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['3_0']),
        '4_0':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['4_0']),
        '5_0':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['5_0']),
        '0_1':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['0_1']),
        '1_1':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['1_1']),
        '2_1':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['2_1']),
        '3_1':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['3_1']),
        '4_1':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['4_1']),
        '5_1':  gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADERS['5_1'])
        }


class DrawSpectrumX():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red1;
        uniform float green1;
        uniform float blue1;
        uniform float alpha1;
        uniform float red2;
        uniform float green2;
        uniform float blue2;
        uniform float alpha2;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = vec4(
            ((1 - uvs.x) * red1) + (uvs.x * red2), 
            ((1 - uvs.x) * green1) + (uvs.x * green2), 
            ((1 - uvs.x) * blue1) + (uvs.x * blue2), 
            ((1 - uvs.x) * alpha1) + (uvs.x * alpha2)
            );
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawCheckerboard():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;
        uniform float red1;
        uniform float green1;
        uniform float blue1;
        uniform float alpha1;
        uniform float red2;
        uniform float green2;
        uniform float blue2;
        uniform float alpha2;
        uniform float offset_x;
        uniform float offset_y;
        uniform float two_tiles_x;
        uniform float two_tiles_y;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            float one_tile_x = two_tiles_x / 2;
            float one_tile_y = two_tiles_y / 2;
            f_color = vec4(red1, green1, blue1, alpha1);
            if ((mod(uvs.x + offset_x, two_tiles_x) < one_tile_x) ^^ (mod(uvs.y + offset_y, two_tiles_y) < one_tile_y)) {
                f_color = vec4(red2, green2, blue2, alpha2);
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawInvertWhite():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core
        #extension GL_EXT_shader_framebuffer_fetch : require

        uniform sampler2D tex;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            vec3 destination_color = gl_LastFragData[0].rgb;
            float luminosity = dot(destination_color, vec3(0.299, 0.587, 0.114));
            f_color = vec4(texture(tex, uvs).rgba);
            if (luminosity < 0.5) {
                f_color.rgb = vec3(1.0, 1.0, 1.0);
            } else {
                f_color.rgb = vec3(0.0, 0.0, 0.0);
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawCircleOutline():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core
        #extension GL_EXT_shader_framebuffer_fetch : require

        const vec3 BLACK = vec3(0.0, 0.0, 0.0);
        const vec3 WHITE = vec3(1.0, 1.0, 1.0);

        uniform sampler2D tex;
        uniform int width;
        uniform int height;

        uniform float circle_size;
        uniform float circle_pixel_size;
        uniform int circle_outline_thickness;

        uniform bool is_a_square;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            vec3 destination_color = gl_LastFragData[0].rgb;
            float luminosity = dot(destination_color, vec3(0.299, 0.587, 0.114));
            f_color = vec4(texture(tex, uvs).rgba);
            f_color.rgb = destination_color;

            float pixel_center = width / 2;
            float pixel_x = round(uvs.x * (width - 1)) + 0.5;
            float pixel_y = round(uvs.y * (height - 1)) + 0.5;

            float editor_center = circle_size / 2;
            float editor_pixel_x = floor((pixel_x - circle_outline_thickness) / circle_pixel_size) + 0.5;
            float editor_pixel_y = floor((pixel_y - circle_outline_thickness) / circle_pixel_size) + 0.5;

            if (is_a_square) {
                bool top_side_pixel = (pixel_x > circle_outline_thickness) && (pixel_x < width - circle_outline_thickness) && (pixel_y < circle_outline_thickness);
                bool left_side_pixel = (pixel_y > circle_outline_thickness) && (pixel_y < height - circle_outline_thickness) && (pixel_x < circle_outline_thickness);
                bool bottom_side_pixel = (pixel_x > circle_outline_thickness) && (pixel_x < width - circle_outline_thickness) && (pixel_y > height - circle_outline_thickness);
                bool right_side_pixel = (pixel_y > circle_outline_thickness) && (pixel_y < height - circle_outline_thickness) && (pixel_x > width - circle_outline_thickness);

                if (top_side_pixel || left_side_pixel || bottom_side_pixel || right_side_pixel) {
                    if (luminosity < 0.5) {
                        f_color.rgb = WHITE;
                    } else {
                        f_color.rgb = BLACK;
                    }
                }
            }

            if (!is_a_square) {
                float editor_radial_distance = pow(abs(editor_pixel_x - editor_center), 2) + pow(abs(editor_pixel_y - editor_center), 2);
                float editor_circle_radius = pow(((circle_size - 0.5) / 2), 2);

                // condition if the current point is outside of the circle
                if (editor_radial_distance >= editor_circle_radius) {
                    float one_pixel_uv_size = 1 / width;
                    for (int i = 1; i <= circle_outline_thickness; i++) {
                        // check if the right side is inside the circle
                        float pixel_x_i = pixel_x + i;
                        float pixel_y_i = pixel_y;
                        float editor_pixel_x_i = floor((pixel_x_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        float editor_pixel_y_i = floor((pixel_y_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        float editor_radial_distance_i = pow(abs(editor_pixel_x_i - editor_center), 2) + pow(abs(editor_pixel_y_i - editor_center), 2);
                        if (editor_radial_distance_i < editor_circle_radius) {
                            if (luminosity < 0.5) {
                                f_color.rgb = WHITE;
                            } else {
                                f_color.rgb = BLACK;
                            }
                        }

                        // check if the left side is inside the circle
                        pixel_x_i = pixel_x - i;
                        pixel_y_i = pixel_y;
                        editor_pixel_x_i = floor((pixel_x_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        editor_pixel_y_i = floor((pixel_y_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        editor_radial_distance_i = pow(abs(editor_pixel_x_i - editor_center), 2) + pow(abs(editor_pixel_y_i - editor_center), 2);
                        if (editor_radial_distance_i < editor_circle_radius) {
                            if (luminosity < 0.5) {
                                f_color.rgb = WHITE;
                            } else {
                                f_color.rgb = BLACK;
                            }
                        }
                        
                        // check if the top side is inside the circle
                        pixel_x_i = pixel_x;
                        pixel_y_i = pixel_y - 1;
                        editor_pixel_x_i = floor((pixel_x_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        editor_pixel_y_i = floor((pixel_y_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        editor_radial_distance_i = pow(abs(editor_pixel_x_i - editor_center), 2) + pow(abs(editor_pixel_y_i - editor_center), 2);
                        if (editor_radial_distance_i < editor_circle_radius) {
                            if (luminosity < 0.5) {
                                f_color.rgb = WHITE;
                            } else {
                                f_color.rgb = BLACK;
                            }
                        }

                        // check if the bottom side is inside the circle
                        pixel_x_i = pixel_x;
                        pixel_y_i = pixel_y + 1;
                        editor_pixel_x_i = floor((pixel_x_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        editor_pixel_y_i = floor((pixel_y_i - circle_outline_thickness) / circle_pixel_size) + 0.5;
                        editor_radial_distance_i = pow(abs(editor_pixel_x_i - editor_center), 2) + pow(abs(editor_pixel_y_i - editor_center), 2);
                        if (editor_radial_distance_i < editor_circle_radius) {
                            if (luminosity < 0.5) {
                                f_color.rgb = WHITE;
                            } else {
                                f_color.rgb = BLACK;
                            }
                        }
                    }
                }
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawCircle():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        const vec4 BLANK = vec4(0.0, 0.0, 0.0, 0.0);

        uniform sampler2D tex;
        uniform int width;
        uniform int height;

        uniform float circle_size;
        uniform float circle_pixel_size;
        uniform int circle_outline_thickness;

        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float alpha;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color.rgba = BLANK;

            float pixel_center = width / 2;
            float pixel_x = round(uvs.x * (width - 1)) + 0.5;
            float pixel_y = round(uvs.y * (height - 1)) + 0.5;

            float editor_center = circle_size / 2;
            float editor_pixel_x = floor((pixel_x - circle_outline_thickness) / circle_pixel_size) + 0.5;
            float editor_pixel_y = floor((pixel_y - circle_outline_thickness) / circle_pixel_size) + 0.5;
            float editor_radial_distance = pow(abs(editor_pixel_x - editor_center), 2) + pow(abs(editor_pixel_y - editor_center), 2);
            float editor_circle_radius = pow(((circle_size - 0.5) / 2), 2);

            if (editor_radial_distance < editor_circle_radius) {
                f_color = vec4(
                texture(tex, uvs).r + red, 
                texture(tex, uvs).g + green, 
                texture(tex, uvs).b + blue, 
                texture(tex, uvs).a * alpha
                );
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawEllipse():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;

        const vec4 BLANK = vec4(0.0, 0.0, 0.0, 0.0);

        // size of the image
        uniform int width;
        uniform int height;

        // size of the ellipse scaled by the pixel size
        uniform float ellipse_width;
        uniform float ellipse_height;

        uniform float pixel_size;

        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float alpha;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color.rgba = BLANK;

            float pixel_x = round(uvs.x * (width - 1)) + 0.5;
            float pixel_y = round(uvs.y * (height - 1)) + 0.5;

            float editor_center_x = ellipse_width / 2;
            float editor_center_y = ellipse_height / 2;
            float editor_pixel_x = floor(pixel_x / pixel_size) + 0.5;
            float editor_pixel_y = floor(pixel_y / pixel_size) + 0.5;
            float x_inside = (pow(editor_pixel_x - editor_center_x, 2)) / pow((ellipse_width / 2), 2);
            float y_inside = (pow(editor_pixel_y - editor_center_y, 2)) / pow((ellipse_height / 2), 2);

            if (x_inside + y_inside <= 1) {
                f_color = vec4(
                texture(tex, uvs).r + red, 
                texture(tex, uvs).g + green, 
                texture(tex, uvs).b + blue, 
                texture(tex, uvs).a * alpha
                );
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawHollowEllipse():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        uniform sampler2D tex;

        const vec4 BLANK = vec4(0.0, 0.0, 0.0, 0.0);

        // size of the image
        uniform int width;
        uniform int height;

        // size of the ellipse scaled by the pixel size
        uniform float ellipse_width;
        uniform float ellipse_height;

        uniform float pixel_size;
        uniform float ellipse_thickness;

        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float alpha;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color.rgba = BLANK;

            float pixel_x = round(uvs.x * (width - 1)) + 0.5;
            float pixel_y = round(uvs.y * (height - 1)) + 0.5;

            float editor_center_x = ellipse_width / 2;
            float editor_center_y = ellipse_height / 2;
            float editor_pixel_x = floor(pixel_x / pixel_size) + 0.5;
            float editor_pixel_y = floor(pixel_y / pixel_size) + 0.5;

            float x_inside_border = (pow(editor_pixel_x - editor_center_x, 2)) / pow((ellipse_width / 2), 2);
            float y_inside_border = (pow(editor_pixel_y - editor_center_y, 2)) / pow((ellipse_height / 2), 2);
            bool inside_border = x_inside_border + y_inside_border <= 1;

            float ellipse_thickness2 = ellipse_thickness + 1;

            if (inside_border) {
                f_color = vec4(
                texture(tex, uvs).r + red, 
                texture(tex, uvs).g + green, 
                texture(tex, uvs).b + blue, 
                texture(tex, uvs).a * alpha
                );
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawLine():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        const vec3 RED = vec3(1.0, 0.0, 0.0);
        const vec3 GREEN = vec3(0.0, 1.0, 0.0);
        const vec3 WHITE = vec3(1.0, 1.0, 1.0);
        const vec4 BLANK = vec4(0.0, 0.0, 0.0, 0.0);

        uniform sampler2D tex;
        uniform float red;
        uniform float green;
        uniform float blue;
        uniform float alpha;

        uniform float left;
        uniform float top;
        uniform float width;
        uniform float height;

        uniform float thickness;

        uniform float px1;
        uniform float py1;
        uniform float px2;
        uniform float py2;

        uniform float outer_line_x1;
        uniform float outer_line_y1;
        uniform float outer_line_x2;
        uniform float outer_line_y2;

        uniform int octant;
        uniform float pixel_size;

        // (1 = circle, 2 = square)
        uniform int brush_style;

        in vec2 uvs;
        out vec4 f_color;

        float round_close(highp float number) {
            if (mod(number, 1.0) > 0.999) {
                number = ceil(number);
            }
            if (mod(number, 1.0) < 0.001) {
                number = floor(number);
            }
            return number;
        }

        void main() {
            vec4 line_color = vec4(
                texture(tex, uvs).r + red, 
                texture(tex, uvs).g + green, 
                texture(tex, uvs).b + blue, 
                texture(tex, uvs).a * alpha
            );
        
            // set all pixels to be blank
            f_color.rgba = BLANK;

            // move xy-coordinates to top-left
            float x1 = (px1 - left) / pixel_size;
            float y1 = (py1 - top) / pixel_size;
            float x2 = (px2 - left) / pixel_size;
            float y2 = (py2 - top) / pixel_size;

            // get which pixel this is
            float index_x = round(uvs.x * (width - 1));
            float index_y = round(uvs.y * (height - 1));
            float pixel_x = index_x + 0.5;
            float pixel_y = index_y + 0.5;
            float editor_pixel_x = floor(pixel_x / pixel_size) + 0.5;
            float editor_pixel_y = floor(pixel_y / pixel_size) + 0.5;

            // items needed for all octants
            float delta_x = x2 - x1;
            float delta_y = y2 - y1;
            float slope = delta_y / delta_x;
            float inverse_slope = delta_x / delta_y;
            float recenter = (mod(thickness, 2.0) == 0.0) ? 0.5 : 0.0;

            // octants
            // .3.2.
            // 4...1
            // 5...8
            // .6.7.
            // 0 = horizontal or vertical

            if (brush_style == 2) {
                float thickness_left_top_adjustment = (mod(thickness, 2.0) == 0.0) ? -((thickness - 2) / 2) : -((thickness - 1) / 2);
                float stamp1_left = x1 + thickness_left_top_adjustment;
                float stamp1_top = y1 + thickness_left_top_adjustment;
                float stamp1_right = stamp1_left + thickness;
                float stamp1_bottom = stamp1_top + thickness;
                if ((stamp1_left <= editor_pixel_x - 0.5) && (editor_pixel_x - 0.5 < stamp1_right) && (stamp1_top <= editor_pixel_y - 0.5) && (editor_pixel_y - 0.5 < stamp1_bottom)) {
                    f_color.rgba = line_color;
                }

                float stamp2_left = x2 + thickness_left_top_adjustment;
                float stamp2_top = y2 + thickness_left_top_adjustment;
                float stamp2_right = stamp2_left + thickness;
                float stamp2_bottom = stamp2_top + thickness;
                if ((stamp2_left <= editor_pixel_x - 0.5) && (editor_pixel_x - 0.5 < stamp2_right) && (stamp2_top <= editor_pixel_y - 0.5) && (editor_pixel_y - 0.5 < stamp2_bottom)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 0) {
                // draw a dot
                if ((x1 == x2) && (y1 == y2)) {
                    float center_offset_xy1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_xy1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_xy1), 2);
                    float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                        f_color.rgba = line_color;
                    }
                }

                // draw line from left to right
                if ((x1 < x2) && (y1 == y2)) {
                    float center_offset_xy1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_xy1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_xy1), 2);
                    float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                        f_color.rgba = line_color;
                    }

                    float center_offset_x2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                    float center_offset_y2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_x2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_y2), 2);
                    float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                        f_color.rgba = line_color;
                    }

                    if ((x1 <= editor_pixel_x) && (editor_pixel_x <= x2)) {
                        f_color.rgba = line_color;
                    }
                }

                // draw line from right to left
                if ((x1 > x2) && (y1 == y2)) {
                    float center_offset_x1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                    float center_offset_y1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_x1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_y1), 2);
                    float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                        f_color.rgba = line_color;
                    }

                    float center_offset_xy2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_xy2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_xy2), 2);
                    float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                        f_color.rgba = line_color;
                    }

                    if ((x2 <= editor_pixel_x) && (editor_pixel_x <= x1)) {
                        f_color.rgba = line_color;
                    }
                }

                // draw line from top to bottom
                if ((x1 == x2) && (y1 < y2)) {
                    float center_offset_xy1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_xy1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_xy1), 2);
                    float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                        f_color.rgba = line_color;
                    }

                    float center_offset_x2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float center_offset_y2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                    float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_x2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_y2), 2);
                    float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                        f_color.rgba = line_color;
                    }

                    if ((y1 <= editor_pixel_y) && (editor_pixel_y <= y2)) {
                        f_color.rgba = line_color;
                    }
                }

                // draw line from bottom to top
                if ((x1 == x2) && (y1 > y2)) {
                    float center_offset_x1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float center_offset_y1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                    float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_x1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_y1), 2);
                    float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                        f_color.rgba = line_color;
                    }

                    float center_offset_x2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float center_offset_y2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                    float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_x2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_y2), 2);
                    float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                    if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                        f_color.rgba = line_color;
                    }

                    if ((y2 <= editor_pixel_y) && (editor_pixel_y <= y1)) {
                        f_color.rgba = line_color;
                    }
                }
            }

            if (octant == 1) {
                float center_offset_x1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float center_offset_y1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_x1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_y1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_x2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float center_offset_y2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_x2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_y2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                slope = (delta_y + 1) / (delta_x - 1);
                if (thickness == 1.0) {
                    float calculated_y = (slope * (editor_pixel_x - 0.5)) + y1 - 0.5;
                    calculated_y = round_close(calculated_y);
                    if ((calculated_y <= editor_pixel_y + 0.5) && (calculated_y > editor_pixel_y - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }

                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (slope * (editor_pixel_x - bottom_line_x - 0.5)) + bottom_line_y - 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line > editor_pixel_y - 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (slope * (editor_pixel_x - top_line_x - 0.5)) + top_line_y - 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line <= editor_pixel_y + 0.5;

                float perpendicular_slope = (top_line_y - bottom_line_y) / (top_line_x - bottom_line_x);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_x + 1) + bottom_line_y;
                bool right_of_stamp1 = editor_pixel_x + 0.5 >= ((1/perpendicular_slope) * (editor_pixel_y - bottom_line_y)) + bottom_line_x + 1;

                float stamp2_x = x1 + delta_x - 1 + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -stamp2_x) + stamp2_y;
                bool left_of_stamp2 = editor_pixel_x - 0.5 < ((1/perpendicular_slope) * (editor_pixel_y - stamp2_y)) + stamp2_x;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 2) {
                float center_offset_x1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float center_offset_y1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_x1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_y1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_x2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float center_offset_y2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_x2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_y2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                inverse_slope = (delta_x - 1) / (delta_y + 1);
                if (thickness == 1.0) {
                    float calculated_x = (inverse_slope * (editor_pixel_y - y1 + 0.5)) + 0.5;
                    calculated_x = round_close(calculated_x);
                    if ((calculated_x < editor_pixel_x + 0.5) && (calculated_x >= editor_pixel_x - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }

                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (inverse_slope * (editor_pixel_y - bottom_line_y + 0.5)) + bottom_line_x + 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line >= editor_pixel_x - 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (inverse_slope * (editor_pixel_y - top_line_y + 0.5)) + top_line_x + 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line < editor_pixel_x + 0.5;

                float perpendicular_slope = (top_line_x - bottom_line_x) / (top_line_y - bottom_line_y);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_y) + bottom_line_x - 1;
                bool right_of_stamp1 = editor_pixel_y - 0.5 < ((1/perpendicular_slope) * (editor_pixel_x - bottom_line_x - 1)) + bottom_line_y;

                float stamp2_x = x1 + delta_x - 1 + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -stamp2_y) + stamp2_x;
                bool left_of_stamp2 = editor_pixel_y + 0.5 >= ((1/perpendicular_slope) * (editor_pixel_x - stamp2_x)) + stamp2_y;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 3) {
                float center_offset_xy1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_xy1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_xy1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_xy2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_xy2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_xy2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                inverse_slope = (delta_x + 1) / (delta_y + 1);
                if (thickness == 1.0) {
                    float calculated_x = (inverse_slope * (editor_pixel_y - y1 + 0.5)) + x1 - 0.5;
                    calculated_x = round_close(calculated_x);
                    if ((calculated_x <= editor_pixel_x + 0.5) && (calculated_x > editor_pixel_x - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }

                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (inverse_slope * (editor_pixel_y - bottom_line_y + 0.5)) + bottom_line_x - 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line <= editor_pixel_x + 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (inverse_slope * (editor_pixel_y - top_line_y + 0.5)) + top_line_x - 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line > editor_pixel_x - 0.5;

                float perpendicular_slope = (top_line_x - bottom_line_x) / (top_line_y - bottom_line_y);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_y - 1) + bottom_line_x;
                bool right_of_stamp1 = editor_pixel_y - 0.5 < ((1/perpendicular_slope) * (editor_pixel_x - bottom_line_x)) + bottom_line_y - 1;

                float stamp2_x = x1 + delta_x + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -stamp2_y) + stamp2_x;
                bool left_of_stamp2 = editor_pixel_y + 0.5 >= ((1/perpendicular_slope) * (editor_pixel_x - stamp2_x)) + stamp2_y;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 4) {
                float center_offset_xy1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_xy1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_xy1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_xy2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_xy2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_xy2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                slope = (delta_y + 1) / (delta_x + 1);
                if (thickness == 1.0) {
                    float calculated_y = (slope * (editor_pixel_x - x1 + 0.5)) + y1 - 0.5;
                    calculated_y = round_close(calculated_y);
                    if ((calculated_y <= editor_pixel_y + 0.5) && (calculated_y > editor_pixel_y - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }

                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (slope * (editor_pixel_x - bottom_line_x + 0.5)) + bottom_line_y - 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line > editor_pixel_y - 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (slope * (editor_pixel_x - top_line_x + 0.5)) + top_line_y - 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line <= editor_pixel_y + 0.5;

                float perpendicular_slope = (top_line_y - bottom_line_y) / (top_line_x - bottom_line_x);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_x - 1) + bottom_line_y;
                bool right_of_stamp1 = editor_pixel_x - 0.5 < ((1/perpendicular_slope) * (editor_pixel_y - bottom_line_y)) + bottom_line_x - 1;

                float stamp2_x = x1 + delta_x + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -stamp2_x) + stamp2_y;
                bool left_of_stamp2 = editor_pixel_x + 0.5 >= ((1/perpendicular_slope) * (editor_pixel_y - stamp2_y)) + stamp2_x;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 5) {
                float center_offset_x1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float center_offset_y1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_x1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_y1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_x2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float center_offset_y2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_x2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_y2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                slope = (delta_y - 1) / (delta_x + 1);
                if (thickness == 1.0) {
                    float calculated_y = (slope * (editor_pixel_x - x1 + 0.5)) + y1 + 0.5;
                    calculated_y = round_close(calculated_y);
                    if ((calculated_y < editor_pixel_y + 0.5) && (calculated_y >= editor_pixel_y - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }

                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (slope * (editor_pixel_x - bottom_line_x + 0.5)) + bottom_line_y + 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line >= editor_pixel_y - 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (slope * (editor_pixel_x - top_line_x + 0.5)) + top_line_y + 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line < editor_pixel_y + 0.5;

                float perpendicular_slope = (top_line_y - bottom_line_y) / (top_line_x - bottom_line_x);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_x - 1) + bottom_line_y;
                bool right_of_stamp1 = editor_pixel_x + 0.5 < ((1/perpendicular_slope) * (editor_pixel_y - bottom_line_y)) + bottom_line_x;

                float stamp2_x = x1 + delta_x + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y - 1 + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -stamp2_x) + stamp2_y;
                bool left_of_stamp2 = editor_pixel_x + 0.5 >= ((1/perpendicular_slope) * (editor_pixel_y - stamp2_y)) + stamp2_x;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 6) {
                float center_offset_x1 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float center_offset_y1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_x1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_y1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_x2 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float center_offset_y2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_x2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_y2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                inverse_slope = (delta_x + 1) / (delta_y - 1);
                if (thickness == 1.0) {
                    float calculated_x = (inverse_slope * (editor_pixel_y - y1 - 0.5)) + x1 - 0.5;
                    calculated_x = round_close(calculated_x);
                    if ((calculated_x <= editor_pixel_x + 0.5) && (calculated_x > editor_pixel_x - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }
                
                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (inverse_slope * (editor_pixel_y - bottom_line_y - 0.5)) + bottom_line_x - 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line > editor_pixel_x - 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (inverse_slope * (editor_pixel_y - top_line_y - 0.5)) + top_line_x - 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line <= editor_pixel_x + 0.5;

                float perpendicular_slope = (top_line_x - bottom_line_x) / (top_line_y - bottom_line_y);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_y - 1) + bottom_line_x;
                bool right_of_stamp1 = editor_pixel_y - 0.5 >= ((1/perpendicular_slope) * (editor_pixel_x - bottom_line_x)) + bottom_line_y;

                float stamp2_x = x1 + delta_x + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y - 1 + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -stamp2_y) + stamp2_x;
                bool left_of_stamp2 = editor_pixel_y - 0.5 < ((1/perpendicular_slope) * (editor_pixel_x - stamp2_x)) + stamp2_y;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 7) {
                float center_offset_xy1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_xy1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_xy1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_xy2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_xy2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_xy2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                inverse_slope = (delta_x - 1) / (delta_y - 1);
                if (thickness == 1.0) {
                    float calculated_x = (inverse_slope * (editor_pixel_y - 0.5)) + 0.5;
                    calculated_x = round_close(calculated_x);
                    if ((calculated_x < editor_pixel_x + 0.5) && (calculated_x >= editor_pixel_x - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }

                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (inverse_slope * (editor_pixel_y - bottom_line_y - 0.5)) + bottom_line_x + 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line < editor_pixel_x + 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (inverse_slope * (editor_pixel_y - top_line_y - 0.5)) + top_line_x + 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line >= editor_pixel_x - 0.5;

                float perpendicular_slope = (top_line_x - bottom_line_x) / (top_line_y - bottom_line_y);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_y + 1) + bottom_line_x;
                bool right_of_stamp1 = editor_pixel_y + 0.5 >= ((1/perpendicular_slope) * (editor_pixel_x - bottom_line_x)) + bottom_line_y + 1;

                float stamp2_x = x1 + delta_x - 1 + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y - 1 + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -(bottom_line_y + delta_y - 1)) + (bottom_line_x + delta_x - 1);
                bool left_of_stamp2 = editor_pixel_y - 0.5 < ((1/perpendicular_slope) * (editor_pixel_x - stamp2_x)) + stamp2_y;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }

            if (octant == 8) {
                float center_offset_xy1 = (mod(thickness, 2.0) == 0.0) ? -1.0 : -0.5;
                float editor_radial_distance_xy1 = pow(abs(editor_pixel_x - x1 + center_offset_xy1), 2) + pow(abs(editor_pixel_y - y1 + center_offset_xy1), 2);
                float editor_circle_radius_xy1 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy1 < editor_circle_radius_xy1) {
                    f_color.rgba = line_color;
                }

                float center_offset_xy2 = (mod(thickness, 2.0) == 0.0) ? 0.0 : 0.5;
                float editor_radial_distance_xy2 = pow(abs(editor_pixel_x - x2 + center_offset_xy2), 2) + pow(abs(editor_pixel_y - y2 + center_offset_xy2), 2);
                float editor_circle_radius_xy2 = pow(((thickness - 0.5) / 2), 2);
                if (editor_radial_distance_xy2 < editor_circle_radius_xy2) {
                    f_color.rgba = line_color;
                }

                slope = (delta_y - 1) / (delta_x - 1);
                if (thickness == 1.0) {
                    float calculated_y = (slope * (editor_pixel_x - 0.5)) + 0.5;
                    calculated_y = round_close(calculated_y);
                    if ((calculated_y < editor_pixel_y + 0.5) && (calculated_y >= editor_pixel_y - 0.5)) {
                        f_color.rgba = line_color;
                    }
                }

                float left_top_edge_offset = (mod(thickness, 2.0) == 0.0) ? -((thickness / 2) - 1) : -floor(thickness / 2);
                float bottom_line_x = x1 + left_top_edge_offset + outer_line_x1;
                float bottom_line_y = y1 + left_top_edge_offset + outer_line_y1;
                float calculated_bottom_line = (slope * (editor_pixel_x - bottom_line_x - 0.5)) + bottom_line_y + 0.5;
                calculated_bottom_line = round_close(calculated_bottom_line);
                bool above_bottom_line = calculated_bottom_line >= editor_pixel_y - 0.5;

                float top_line_x = x1 + left_top_edge_offset + outer_line_x2;
                float top_line_y = y1 + left_top_edge_offset + outer_line_y2;
                float calculated_top_line = (slope * (editor_pixel_x - top_line_x - 0.5)) + top_line_y + 0.5;
                calculated_top_line = round_close(calculated_top_line);
                bool below_top_line = calculated_top_line < editor_pixel_y + 0.5;

                float perpendicular_slope = (top_line_y - bottom_line_y) / (top_line_x - bottom_line_x);
                float perpendicular_intercept_stamp1 = (perpendicular_slope * -bottom_line_x + 1) + bottom_line_y;
                bool right_of_stamp1 = editor_pixel_x + 0.5 >= ((1/perpendicular_slope) * (editor_pixel_y - bottom_line_y)) + bottom_line_x + 1;

                float stamp2_x = x1 + delta_x - 1 + left_top_edge_offset + outer_line_x1 + 0.5;
                float stamp2_y = y1 + delta_y - 1 + left_top_edge_offset + outer_line_y1 + 0.5;
                float perpendicular_intercept_stamp2 = (perpendicular_slope * -(bottom_line_x + delta_x - 1)) + (bottom_line_y + delta_y - 1);
                bool left_of_stamp2 = editor_pixel_x - 0.5 < ((1/perpendicular_slope) * (editor_pixel_y - stamp2_y)) + stamp2_x;

                if ((above_bottom_line) && (below_top_line) && (right_of_stamp1) && (left_of_stamp2) && (thickness != 1.0)) {
                    f_color.rgba = line_color;
                }
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawCollisionTile():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        // NO COLLISION
        const vec3 WHITE = vec3(1.0, 1.0, 1.0);
        // COLLISION
        const vec3 BLACK = vec3(0.0, 0.0, 0.0);
        // GRAPPLE
        const vec3 RED = vec3(1.0, 0.0, 0.0);
        // PLATFORM
        const vec3 YELLOW = vec3(1.0, 1.0, 0.0);
        // WATER
        const vec3 BLUE = vec3(0.0, 0.0, 1.0);

        const float one_bit = 1 / 255;

        uniform sampler2D tex;

        in vec2 uvs;
        out vec4 f_color;

        void main() {
            f_color = texture(tex, uvs);

            // NO COLLISION
            if (texture(tex, uvs).r == one_bit) {
                f_color.rgb = WHITE;
            }

            // COLLISION
            if ((texture(tex, uvs).r > one_bit) && (texture(tex, uvs).r < 0.004)) {
                f_color.rgb = BLACK;
            }

            // GRAPPLE
            if ((texture(tex, uvs).r > 0.007843) && (texture(tex, uvs).r < 0.008)) {
                f_color.rgb = RED;
            }

            // PLATFORM
            if ((texture(tex, uvs).r > 0.01176) && (texture(tex, uvs).r < 0.012)) {
                f_color.rgb = YELLOW;
            }

            // WATER
            if ((texture(tex, uvs).r > 0.01568) && (texture(tex, uvs).r < 0.016)) {
                f_color.rgb = BLUE;
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)


class DrawWaterJet():
    def __init__(self, gl_context):
        self.VERTICE_SHADER = '''
        #version 430 core

        uniform float aspect;

        in vec2 vert;
        in vec2 texcoord;
        out vec2 uvs;

        void main() {
            uvs = texcoord;
            gl_Position = vec4(
            vert.x / aspect, 
            vert.y, 0.0, 1.0
            );
        }
        '''
        self.FRAGMENT_SHADER = '''
        #version 430 core

        const float PI = 3.1415926535;
        const vec4 DARK_BLUE = vec4(0.0, 0.0, 1.0, 0.90);
        const vec4 LIGHT_BLUE = vec4(0.0, 0.5, 1.0, 0.35);
        const vec4 WHITE = vec4(0.8, 0.8, 1.0, 0.9);
        const vec4 BLANK = vec4(0.0, 0.0, 0.0, 0.0);

        uniform sampler2D tex;
        uniform float width;
        uniform float height;
        uniform float slope;
        uniform float intercept;
        uniform float minimum_water_jet_thickness;
        uniform float current_length_from_center;
        uniform float max_length_from_center;
        uniform float rotation;
        uniform float ball_radius;
        uniform float moment_in_wave_period;
        uniform bool quad1;
        uniform bool quad2;
        uniform bool quad3;
        uniform bool quad4;

        in vec2 uvs;
        out vec4 f_color;

        float get_point_to_line_distance(highp float slope, highp float intercept, highp float x_pos, highp float y_pos) {
            return abs((slope * x_pos) + (-1 * y_pos) + intercept) / sqrt(pow(slope, 2) + pow(-1, 2));
        }

        float get_closest_x(highp float slope, highp float intercept, highp float x_pos, highp float y_pos) {
            return ((-1 * ((-1 * x_pos) - (slope * y_pos))) - (slope * intercept)) / (pow(slope, 2) + pow(-1, 2));
        }

        float get_closest_y(highp float slope, highp float intercept, highp float x_pos, highp float y_pos) {
            return ((slope * ((1 * x_pos) + (slope * y_pos))) - (-1 * intercept)) / (pow(slope, 2) + pow(-1, 2));
        }

        bool get_side_of_line(highp float rotation, highp float slope, highp float intercept, highp float x_pos, highp float y_pos) {
            float multiplier1 = (slope >= 0.0) ? -1.0 : 1.0;
            float multiplier2 = ((0.0 <= rotation) && (rotation <= 180.0)) ? -1.0 : 1.0;
            float side_of_line = multiplier1 * multiplier2 * ((slope * x_pos) + (-1 * y_pos) + intercept);
            bool top_side = side_of_line >= 0.0;
            return top_side;
        }

        void main() {
            // set all pixels to be blank
            f_color.rgba = BLANK;

            // get which pixel this is
            float index_x = round(uvs.x * (width - 1));
            float index_y = round(uvs.y * (height - 1));
            float pixel_x = (index_x + 0.5);
            float pixel_y = (index_y + 0.5);
            float x_pos = (width / 2) - pixel_x;
            float y_pos = (height / 2) - pixel_y;

            // get the closest xy pixel on center of the jet line
            float point_to_line_distance = get_point_to_line_distance(slope, 0.0, x_pos, y_pos);
            float closest_x = get_closest_x(slope, 0.0, x_pos, y_pos);
            float closest_y = get_closest_y(slope, 0.0, x_pos, y_pos);

            // get how far along the jet the pixel is
            float distance_along_jet = sqrt(pow(closest_x, 2) + pow(closest_y, 2)) - ball_radius;
            float max_jet_length = max_length_from_center - ball_radius;
            float percentage_x = distance_along_jet / max_jet_length;

            // calculate how thick the water jet should be at each point in length
            bool top_side = get_side_of_line(rotation, slope, 0.0, x_pos, y_pos);
            float water_jet_thickness_top;
            float water_jet_thickness_bottom;
            float how_trumpet_shaped = 3.5;
            if (moment_in_wave_period <= 0.5) {
                water_jet_thickness_top = minimum_water_jet_thickness + pow(percentage_x * how_trumpet_shaped * (moment_in_wave_period * 2), 2.2);
                water_jet_thickness_bottom = minimum_water_jet_thickness + pow(percentage_x * how_trumpet_shaped * (1 - (moment_in_wave_period * 2)), 2.2);
            }
            if (moment_in_wave_period > 0.5) {
                water_jet_thickness_top = minimum_water_jet_thickness + pow(percentage_x * how_trumpet_shaped * (1 - ((moment_in_wave_period - 0.5) * 2)), 2.2);
                water_jet_thickness_bottom = minimum_water_jet_thickness + pow(percentage_x * how_trumpet_shaped * (((moment_in_wave_period - 0.5) * 2)), 2.2);
            }

            // remove pixels outside of water jet thickness
            if (((top_side) && (point_to_line_distance < water_jet_thickness_top)) || ((!top_side) && (point_to_line_distance < water_jet_thickness_bottom))) {
                // remove pixels in wrong quadrants
                bool acceptable_quad = ((quad1) && (-x_pos >= 0.0) && (y_pos >= 0.0)) || ((quad2) && (x_pos >= 0.0) && (y_pos >= 0.0)) || ((quad3) && (x_pos >= 0.0) && (-y_pos >= 0.0)) || ((quad4) && (-x_pos >= 0.0) && (-y_pos >= 0.0));
                if (acceptable_quad) {
                    // remove pixels too far away
                    float distance_from_ball_center = sqrt(pow(x_pos, 2) + pow(y_pos, 2));
                    if (distance_from_ball_center < current_length_from_center) {

                        // adjust center of trumpet shape to deformation
                        float distance_from_edge_to_middle_of_jet = (water_jet_thickness_top + water_jet_thickness_bottom) / 2;
                        float adjusted_point_to_line_distance = (top_side) ? point_to_line_distance + ((water_jet_thickness_bottom - water_jet_thickness_top) / 2) : point_to_line_distance + ((water_jet_thickness_top - water_jet_thickness_bottom) / 2);
                        float percentage_y = (distance_from_edge_to_middle_of_jet - abs(adjusted_point_to_line_distance)) / distance_from_edge_to_middle_of_jet;
                        float percentage = ((1 - percentage_x) * 0.15) + (percentage_y * 0.85);

                        // draw water
                        f_color.rgba = vec4(
                        (DARK_BLUE.r * percentage) + (LIGHT_BLUE.r * (1 - percentage)),
                        (DARK_BLUE.g * percentage) + (LIGHT_BLUE.g * (1 - percentage)),
                        (DARK_BLUE.b * percentage) + (LIGHT_BLUE.b * (1 - percentage)),
                        (DARK_BLUE.a * percentage) + (LIGHT_BLUE.a * (1 - percentage))
                        );
                    }
                }
            }
        }
        '''
        self.program = gl_context.program(vertex_shader = self.VERTICE_SHADER, fragment_shader = self.FRAGMENT_SHADER)