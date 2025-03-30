from Code.utilities import loading_and_unloading_images_manager, IMAGE_PATHS, LOADED_IN_MENU, LOADED_IN_GAME, LOADED_IN_EDITOR
from Code.Game.game_utilities import Map
from Code.Game.game_objects import Player


class GameSingleton():
    def __init__(self, Render, Screen, gl_context, PATH):
        #
        # player
        self.player = Player(PATH)
        #
        # map
        self.map = Map(Screen, gl_context, Render, PATH, "C:\\Users\\Kayle\\Desktop\\Blight\\Hamster_Ball_Blight\\Projects\\Project1\\Level1\\")
        self.map_offset_x: int = 0
        self.map_offset_y: int = 0


def game_loop(Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor):
    if Api.setup_required:
        loading_and_unloading_images_manager(Screen, Render, gl_context, IMAGE_PATHS, [LOADED_IN_EDITOR], [LOADED_IN_MENU, LOADED_IN_EDITOR])
        Api.api_initiated_singletons['Game'] = Api.api_singletons['Game'](Render, Screen, gl_context, PATH)
        Api.setup_required = False
    Singleton = Api.api_initiated_singletons[Api.current_api]
    if (Keys.left.pressed):
        Singleton.map_offset_x -= 16
    if (Keys.right.pressed):
        Singleton.map_offset_x += 16
    if (Keys.sink_down.pressed):
        Singleton.map_offset_y += 16
    if (Keys.float_up.pressed):
        Singleton.map_offset_y -= 16
    Singleton.map.update_tile_loading(Render, Screen, gl_context, Time, Keys, Cursor, Singleton.map_offset_x, Singleton.map_offset_y)