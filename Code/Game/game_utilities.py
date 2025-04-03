import pygame
from array import array
from copy import deepcopy
from Code.utilities import move_number_to_desired_range

class Map():
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

    def __init__(self, Screen, gl_context, Render, PATH: str, level_path: str):
        self.PATH: str = PATH
        self.level_path: str = level_path
        self.map_wh: array[int, int] = array('i', [11776, 5888])
        self.tiles_across: int = self.map_wh[0] // Map.TILE_WH
        self.tiles_high: int = self.map_wh[1] // Map.TILE_WH
        self.min_tile_x: int = 0
        self.min_tile_y: int = 0
        self.max_tile_x: int = self.tiles_across - 1
        self.max_tile_y: int = self.tiles_high - 1
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
        self.tiles: list[list[Tile]] = [[Tile(level_path, index_x, index_y) for index_y in range(self.tiles_high)] for index_x in range(self.tiles_across)]

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


class Tile():
    PRETTY_MAP_BYTES_PER_PIXEL = 4
    COLLISION_MAP_BYTES_PER_PIXEL = 1

    def __init__(self, level_path: str, index_x: int, index_y: int):
        self.loaded: bool = False
        self.index_x: int = index_x
        self.index_y: int = index_y
        self.tile_path: str = f"{level_path}\\t{index_x}_{index_y}"
        self.image_reference: str = f"{index_x}_{index_y}"
        self.pretty_bytearray: bytearray = None
        self.collision_bytearray: bytearray = None

    def load(self, Render, Screen, gl_context):
        with open(self.tile_path, mode='rb') as file:
            # get the byte array
            byte_array = bytearray(file.read())
            # separate the pretty map byte array
            self.pretty_bytearray = byte_array[0:(Map.TILE_WH**2)*4]  # (256*256*4); 256 = tile width/height; 4 = number of bytes per pixel
            # separate the collision map byte array
            self.collision_bytearray = byte_array[((Map.TILE_WH**2)*4)+1:((Map.TILE_WH**2)*5)+1]
            #
            # finished reading from the byte array; add image reference for moderngl
            Render.add_moderngl_texture_using_bytearray(Screen, gl_context, self.pretty_bytearray, Tile.PRETTY_MAP_BYTES_PER_PIXEL, Map.TILE_WH, Map.TILE_WH, self.image_reference)
        self.loaded = True

    def unload(self, Render):
        if self.loaded:
            self.pretty_bytearray = None
            self.collision_bytearray = None
            Render.remove_moderngl_texture_from_renderable_objects_dict(self.image_reference)
        self.loaded = False

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