import pygame
import io
import math
from array import array
from copy import deepcopy
from glob import glob
from Code.utilities import move_number_to_desired_range, get_all_paths_in_directory, difference_between_angles, COLORS


class Map():
    TILE_EXTENSION = ''

    NO_COLLISION = 0
    COLLISION = 1
    GRAPPLEABLE = 2
    PLATFORM = 3
    WATER = 4

    NO_COLLISION_BINARY = b'\x00'
    COLLISION_BINARY = b'\x01'
    GRAPPLEABLE_BINARY = b'\x02'
    PLATFORM_BINARY = b'\x03'
    WATER_BINARY = b'\x04'

    NO_COLLISION_BYTEARRAY = bytearray(b'\x00')
    COLLISION_BYTEARRAY = bytearray(b'\x01')
    GRAPPLEABLE_BYTEARRAY = bytearray(b'\x02')
    PLATFORM_BYTEARRAY = bytearray(b'\x03')
    WATER_BYTEARRAY = bytearray(b'\x04')

    TILE_WH = 256
    LOAD_TILES_OUT_OF_VIEW_PIXELS = TILE_WH

    def __init__(self):
        self.level_path: str
        self.map_wh: array[int, int]
        self.tiles_across: int
        self.tiles_high: int
        self.min_tile_x: int
        self.min_tile_y: int
        self.max_tile_x: int
        self.max_tile_y: int
        self.tiles_loaded_x: list[int, int] = [0, 0]
        self.tiles_loaded_y: list[int, int] = [0, 0]
        self.last_tiles_loaded_x: list[int, int] = [0, 0]
        self.last_tiles_loaded_y: list[int, int] = [0, 0]
        self.reached_left_edge: bool = False
        self.reached_right_edge: bool = False
        self.reached_top_edge: bool = False
        self.reached_bottom_edge: bool = False
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.tiles: list[list[Tile]]
    #
    def load_level(self, Singleton, Render, gl_context, Screen, Time, Keys, Cursor, level_path: str, player_center_x: int | float, player_center_y: int | float):
        self.level_path = level_path
        # get the map size
        tile_size_generator = ([int(index_x), int(index_y)] for (index_x, index_y) in (str(path).split('\\')[-1][1:].split('_') for path in get_all_paths_in_directory(self.level_path) if path.suffix == Map.TILE_EXTENSION))
        max_tile_x = 0
        max_tile_y = 0
        for (tile_x, tile_y) in tile_size_generator:
            if tile_x > max_tile_x:
                max_tile_x = tile_x
            if tile_y > max_tile_y:
                max_tile_y = tile_y
        self.map_wh = array('i', [Map.TILE_WH + (max_tile_x * Map.TILE_WH), Map.TILE_WH + (max_tile_y * Map.TILE_WH)])
        self.tiles_across = max_tile_x + 1
        self.tiles_high = max_tile_y + 1
        self.min_tile_x = 0
        self.min_tile_y = 0
        self.max_tile_x = self.tiles_across - 1
        self.max_tile_y = self.tiles_high - 1
        # initialize tiles
        self.tiles = [[Tile(level_path, index_x, index_y) for index_y in range(self.tiles_high)] for index_x in range(self.tiles_across)]
        # initialize map offset and loaded tiles
        self.offset_x = -round(player_center_x - (Screen.width // 2))
        self.offset_y = -round(player_center_y - (Screen.height // 2))
        self.update_tile_loading(Singleton, Render, Screen, gl_context, Time, Keys, Cursor)
    #
    def update_tile_loading(self, Singleton, Render, Screen, gl_context, Time, Keys, Cursor):
        # adjust the offset depending on the map edges
        self.reached_left_edge = self.offset_x >= 0
        self.reached_right_edge = -self.offset_x >= self.map_wh[0] - Screen.width
        self.reached_top_edge = self.offset_y >= 0
        self.reached_bottom_edge = -self.offset_y >= self.map_wh[1] - Screen.height
        self.offset_x = move_number_to_desired_range(-self.map_wh[0]+Screen.width, self.offset_x, 0)
        self.offset_y = move_number_to_desired_range(-self.map_wh[1]+Screen.height, self.offset_y, 0)
        # get which tiles were loaded last frame
        self.last_tiles_loaded_x = deepcopy(self.tiles_loaded_x)
        self.last_tiles_loaded_y = deepcopy(self.tiles_loaded_y)
        # get the bounds of tiles being loaded in pixels
        loaded_tiles_left = -self.offset_x - Map.LOAD_TILES_OUT_OF_VIEW_PIXELS
        loaded_tiles_top = -self.offset_y - Map.LOAD_TILES_OUT_OF_VIEW_PIXELS
        loaded_tiles_right = -self.offset_x + Screen.width + Map.LOAD_TILES_OUT_OF_VIEW_PIXELS
        loaded_tiles_bottom = -self.offset_y + Screen.height + Map.LOAD_TILES_OUT_OF_VIEW_PIXELS
        # update the arrays showing which tiles should be loaded
        self.tiles_loaded_x[0] = move_number_to_desired_range(self.min_tile_x, loaded_tiles_left // Map.TILE_WH, self.max_tile_x)
        self.tiles_loaded_y[0] = move_number_to_desired_range(self.min_tile_y, loaded_tiles_top // Map.TILE_WH, self.max_tile_y)
        self.tiles_loaded_x[1] = move_number_to_desired_range(self.min_tile_x, loaded_tiles_right // Map.TILE_WH, self.max_tile_x)
        self.tiles_loaded_y[1] = move_number_to_desired_range(self.min_tile_y, loaded_tiles_bottom // Map.TILE_WH, self.max_tile_y)
        # unload unneeded tiles
        for index_x in range(self.last_tiles_loaded_x[0], self.last_tiles_loaded_x[1] + 1):
            for index_y in range(self.last_tiles_loaded_y[0], self.last_tiles_loaded_y[1] + 1):
                if (self.tiles_loaded_x[0] <= index_x <= self.tiles_loaded_x[1]) and (self.tiles_loaded_y[0] <= index_y <= self.tiles_loaded_y[1]):
                    continue
                self.tiles[index_x][index_y].unload(Render)
        # change how loading and drawing works depending on player direction
        range_x = range(self.tiles_loaded_x[0], self.tiles_loaded_x[1] + 1, 1) if (Singleton.player.velocity_x > 0) else range(self.tiles_loaded_x[1], self.tiles_loaded_x[0] - 1, -1)
        range_y = range(self.tiles_loaded_y[0], self.tiles_loaded_y[1] + 1, 1) if (Singleton.player.velocity_y < 0) else range(self.tiles_loaded_y[1], self.tiles_loaded_y[0] - 1, -1)
        # load and draw needed tiles
        load = True
        ltwh = [self.offset_x, self.offset_y, Map.TILE_WH, Map.TILE_WH]
        for index_x in range_x:
            ltwh[0] = self.offset_x + (Map.TILE_WH * index_x)
            for index_y in range_y:
                ltwh[1] = self.offset_y + (Map.TILE_WH * index_y)
                tile = self.tiles[index_x][index_y]
                priority_load = rectangles_overlap(ltwh, [0, 0, Screen.width, Screen.height])
                load = tile.draw(Render, Screen, gl_context, ltwh, load or priority_load)
    #
    def get_collision_tile_references_for_ball(self, player_object):
        # get the current tile and pixel
        origin_tile_x, pixel_x = divmod(round(player_object.ball_center_x), Map.TILE_WH)
        origin_tile_y, pixel_y = divmod(round(player_object.ball_center_y), Map.TILE_WH)
        # get the spout rotation
        rotation = player_object.spout.rotation
        # get distance to the edges of the tile
        distance_to_top = pixel_y
        distance_to_bottom = Map.TILE_WH - pixel_y
        distance_to_right = Map.TILE_WH - pixel_x
        distance_to_left = pixel_x
        # calculate which of these spaces the ball is in within the tile
        #  _________
        # |111|2|333|
        # |1|‾‾‾‾‾|3|
        # |-|55555|-|
        # |4|55555|6|
        # |-|55555|-|
        # |7|_____|9|
        # |777|8|999|
        #  ‾‾‾‾‾‾‾‾‾
        maximum_water_jet_length_from_ball_center = math.ceil(player_object.ball_radius + player_object.maximum_length_of_longest_tool)
        space123 = (distance_to_bottom > maximum_water_jet_length_from_ball_center)
        space147 = (distance_to_right > maximum_water_jet_length_from_ball_center)
        space369 = (distance_to_left > maximum_water_jet_length_from_ball_center)
        space789 = (distance_to_top > maximum_water_jet_length_from_ball_center)
        space = (
            1 if space123 and space147 else
            2 if space123 and not space147 and not space369 else
            3 if space123 and space369 else
            4 if space147 and not space123 and not space789 else
            6 if space369 and not space123 and not space789 else
            7 if space147 and space789 else
            8 if space789 and not space147 and not space369 else
            9 if space369 and space789 else
            5
            )
        # calculate the loading direction
        # 1 = upleft
        # 2 = upright
        # 3 = downleft
        # 4 = downright
        match space:
            case 1:
                loading_direction = 1
            case 2:
                loading_direction = 1 if (90.0 <= rotation <= 270.0) else 2
            case 3:
                loading_direction = 2
            case 4:
                loading_direction = 1 if (0.0 <= rotation <= 180.0) else 3
            case 5:
                loading_direction = (
                    2 if (0.0 <= rotation <= 90.0) else
                    1 if (90.0 < rotation <= 180.0) else
                    3 if (180.0 < rotation <= 270.0) else
                    4
                )
            case 6:
                loading_direction = 2 if (0.0 <= rotation <= 180.0) else 4
            case 7:
                loading_direction = 3
            case 8:
                loading_direction = 3 if (90.0 <= rotation <= 270.0) else 4
            case 9:
                loading_direction = 4
        # bind four tiles to buffers in the order shown below
        # get ball position relative to the top-left pixel of tiles 1, 2, 3, 4
        #  ___
        # |1|2|
        # |3|4|
        #  ‾‾‾
        match loading_direction:
            # tiles loading upleft; origin tile is 4
            case 1:
                tile_references = [
                    f"c{origin_tile_x-1}_{origin_tile_y-1}",
                    f"c{origin_tile_x}_{origin_tile_y-1}",
                    f"c{origin_tile_x-1}_{origin_tile_y}",
                    f"c{origin_tile_x}_{origin_tile_y}"
                ]
                player_position_x = Map.TILE_WH + pixel_x
                player_position_y = Map.TILE_WH + pixel_y
            # tiles loading upright; origin tile is 3
            case 2:
                tile_references = [
                    f"c{origin_tile_x}_{origin_tile_y-1}",
                    f"c{origin_tile_x+1}_{origin_tile_y-1}",
                    f"c{origin_tile_x}_{origin_tile_y}",
                    f"c{origin_tile_x+1}_{origin_tile_y}"
                ]
                player_position_x = pixel_x
                player_position_y = Map.TILE_WH + pixel_y
            # tiles loading downleft; origin tile is 2
            case 3:
                tile_references = [
                    f"c{origin_tile_x-1}_{origin_tile_y}",
                    f"c{origin_tile_x}_{origin_tile_y}",
                    f"c{origin_tile_x-1}_{origin_tile_y+1}",
                    f"c{origin_tile_x}_{origin_tile_y+1}"
                ]
                player_position_x = Map.TILE_WH + pixel_x
                player_position_y = pixel_y
            # tiles loading downright; origin tile is 1
            case 4:
                tile_references = [
                    f"c{origin_tile_x}_{origin_tile_y}",
                    f"c{origin_tile_x+1}_{origin_tile_y}",
                    f"c{origin_tile_x}_{origin_tile_y+1}",
                    f"c{origin_tile_x+1}_{origin_tile_y+1}"
                ]
                player_position_x = pixel_x
                player_position_y = pixel_y
        # player_position x and y are between 0-511 when tiles are 256x256
        player_position_x -= player_object.ball_radius
        player_position_y -= player_object.ball_radius
        return tile_references, player_position_x, player_position_y


class Tile():
    PRETTY_MAP_BYTES_PER_PIXEL = 4
    COLLISION_MAP_BYTES_PER_PIXEL = 1

    PRETTY_MAP_BYTES_PER_TILE = Map.TILE_WH * Map.TILE_WH * PRETTY_MAP_BYTES_PER_PIXEL
    COLLISION_MAP_BYTES_PER_TILE = Map.TILE_WH * Map.TILE_WH * COLLISION_MAP_BYTES_PER_PIXEL
    BYTES_PER_NEWLINE = 1

    def __init__(self, level_path: str, index_x: int, index_y: int):
        self.loaded: bool = False
        self.index_x: int = index_x
        self.index_y: int = index_y
        self.tile_path: str = f"{level_path}t{index_x}_{index_y}"
        self.image_reference: str = f"{index_x}_{index_y}"
        self.collision_image_reference: str = f"c{self.image_reference}"
        self.pretty_bytearray: bytearray = None
        self.collision_bytearray: bytearray = None
        self.file_reference: io.BufferedReader = open(self.tile_path, mode='rb')
    #
    def load(self, Render, Screen, gl_context):
        # reset reading from the file reference
        self.file_reference.seek(0)
        # get the pretty map
        self.pretty_bytearray = self.file_reference.read(Tile.PRETTY_MAP_BYTES_PER_TILE)
        # add the pretty map as a moderngl texture
        Render.add_moderngl_texture_using_bytearray(Screen, gl_context, self.pretty_bytearray, Tile.PRETTY_MAP_BYTES_PER_PIXEL, Map.TILE_WH, Map.TILE_WH, self.image_reference)
        # skip newline
        self.file_reference.read(Tile.BYTES_PER_NEWLINE)
        # separate the collision map byte array
        self.collision_bytearray = self.file_reference.read(Tile.COLLISION_MAP_BYTES_PER_TILE)
        # add the collision map as a moderngl texture
        Render.add_moderngl_texture_using_bytearray(Screen, gl_context, self.collision_bytearray, Tile.COLLISION_MAP_BYTES_PER_PIXEL, Map.TILE_WH, Map.TILE_WH, self.collision_image_reference)
        # report that the tile has been loaded
        self.loaded = True
    #
    def unload(self, Render):
        if self.loaded:
            self.pretty_bytearray = None
            self.collision_bytearray = None
            Render.remove_moderngl_texture_from_renderable_objects_dict(self.image_reference)
            Render.remove_moderngl_texture_from_renderable_objects_dict(self.collision_image_reference)
        self.loaded = False
    #
    def draw(self, Render, Screen, gl_context, ltwh, load):
        if not self.loaded:
            if load:
                self.load(Render, Screen, gl_context)
                load = False
            else:
                return False

        Render.basic_rect_ltwh_to_quad(Screen, gl_context, self.image_reference, ltwh)
        return load


class StoredDraws():
    def __init__(self):
        # lower order is drawn first, higher order is drawn later
        self.default_stored_draws = [[] for _ in range(10)]
        self.stored_draws_references = deepcopy(self.default_stored_draws)

    def add_draw(self, reference: str, order: int):
        self.stored_draws_references[order].append(reference)

    def draw(self, Render, Screen, gl_context):
        for current_level in self.stored_draws_references:
            for reference in current_level:
                Render.execute_stored_draw(Screen, gl_context, reference)
        self.stored_draws_references = deepcopy(self.default_stored_draws)


def rectangles_overlap(ltwh1, ltwh2):
    return (ltwh1[0] < ltwh2[0] + ltwh2[2]) and (ltwh1[0] + ltwh1[2] > ltwh2[0]) and (ltwh1[1] < ltwh2[1] + ltwh2[3]) and (ltwh1[1] + ltwh1[3] > ltwh2[1])

def get_vector_magnitude_in_direction(vector_length: int | float, vector_angle: int | float, resulting_angle: int | float):
    return vector_length * math.cos(math.radians(difference_between_angles(vector_angle, resulting_angle)))

def get_xy_vector_components(vector_length: int | float, vector_angle: int | float):
    return (vector_length * math.cos(math.radians(vector_angle)),
            vector_length * math.sin(math.radians(vector_angle)))
