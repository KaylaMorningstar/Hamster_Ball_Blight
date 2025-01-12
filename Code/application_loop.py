import pygame
import sys
from Code.utilities import move_number_to_desired_range
from Code.drawing_functions import ScreenObject, RenderObjects
from Code.application_setup import CursorClass, TimingClass, KeysClass, ApiObject
import moderngl


def update_events(Api: ApiObject, Screen: ScreenObject):
    Api.scroll_x, Api.scroll_y = 0, 0
    Screen.window_resize = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        #
        if event.type == pygame.VIDEORESIZE:
            Screen.window_resize = True
            Screen.width = event.w
            Screen.height = event.h
            Screen.width = move_number_to_desired_range(Screen.ACCEPTABLE_WIDTH_RANGE[0], Screen.width, Screen.ACCEPTABLE_WIDTH_RANGE[1])
            Screen.height = move_number_to_desired_range(Screen.ACCEPTABLE_HEIGHT_RANGE[0], Screen.height, Screen.ACCEPTABLE_HEIGHT_RANGE[1])
            Screen.update_aspect()
            Screen.screen = pygame.display.set_mode((Screen.width, Screen.height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
            Screen.display = pygame.Surface((Screen.width, Screen.height))
        #
        if event.type == pygame.MOUSEWHEEL:
            if Api.current_api == Api.EDITOR:
                Api.scroll_x, Api.scroll_y = event.x, event.y


def application_loop(Api: ApiObject, PATH: str, Screen: ScreenObject, gl_context: moderngl.Context, Render: RenderObjects, Time: TimingClass, Keys: KeysClass, Cursor: CursorClass):
    while True:
        #
        # update events
        update_events(Api, Screen)
        #
        # update keys
        Keys.update_controls(Api)
        #
        # operate current API (e.g. Editor, Game, Menu)
        Api.api_options[Api.current_api](Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
        #
        # update cursor
        Cursor.update_cursor(Screen, gl_context, Render, Keys)


        Time.display_fps(Screen, Render, gl_context, [300, 300])
        # Render.add_moderngl_texture_to_renderable_objects_dict(Screen, gl_context, f"{PATH}\\Test\\Images\\test_64.png", "test")
        # Render.basic_rect_ltwh_to_quad(Screen, gl_context, "test", [350, 350, Render.renderable_objects["test"].ORIGINAL_WIDTH, Render.renderable_objects["test"].ORIGINAL_HEIGHT])
        # Render.remove_moderngl_texture_from_renderable_objects_dict("test")



        #
        # update screen
        gl_context.finish()
        Screen.update()
        Render.clear_buffer(gl_context)
        #
        # update timing
        Time.update()