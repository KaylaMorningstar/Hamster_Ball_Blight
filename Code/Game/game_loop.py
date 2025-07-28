from Code.utilities import loading_and_unloading_images_manager, IMAGE_PATHS, LOADED_IN_MENU, LOADED_IN_GAME, LOADED_IN_EDITOR, COLORS
from Code.Game.game_utilities import Map, StoredDraws
from Code.Game.game_objects import Player
from copy import deepcopy


class GameSingleton():
    def __init__(self, Render, Screen, gl_context, Time, Keys, Cursor, PATH):
        #
        # player
        self.player: Player = Player(PATH)
        #
        # map
        #self.map: Map = Map(Screen, gl_context, Render, PATH, "C:\\Users\\Kayle\\Desktop\\Blight\\Hamster_Ball_Blight\\Projects\\Project1\\Level1\\")
        self.map: Map = Map()
        self.map.load_level(self, Render, gl_context, Screen, Time, Keys, Cursor, "C:\\Users\\Kayle\\Desktop\\Blight\\Hamster_Ball_Blight\\Projects\\Project1\\Level1\\", self.player.position_x, self.player.position_y)
        #
        # drawing
        self.stored_draws: StoredDraws = StoredDraws()


def game_loop(Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor):
    # check whether the API should be something else
    if Api.setup_required:
        loading_and_unloading_images_manager(Screen, Render, gl_context, IMAGE_PATHS, [LOADED_IN_GAME], [LOADED_IN_MENU, LOADED_IN_EDITOR])
        Api.api_initiated_singletons['Game'] = Api.api_singletons['Game'](Render, Screen, gl_context, Time, Keys, Cursor, PATH)
        Api.setup_required = False
    Cursor.add_cursor_this_frame('classic_cursor')
    # get the singleton for the game
    Singleton = Api.api_initiated_singletons[Api.current_api]

    # update objects (non-player)

    # update player
    Singleton.player.update(Singleton, Render, Screen, gl_context, Keys, Cursor, Time)

    # update map
    Singleton.map.update_tile_loading(Singleton, Render, Screen, gl_context, Time, Keys, Cursor)

    # execute stored draws
    Singleton.stored_draws.draw(Render, Screen, gl_context)
