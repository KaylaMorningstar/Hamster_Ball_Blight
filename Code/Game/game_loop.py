from Code.utilities import loading_and_unloading_images_manager, IMAGE_PATHS, LOADED_IN_MENU, LOADED_IN_GAME, LOADED_IN_EDITOR


class GameSingleton():
    def __init__(self, Render, Screen, gl_context, PATH):
        pass


def game_loop(Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor):
    if Api.setup_required:
        loading_and_unloading_images_manager(Screen, Render, gl_context, IMAGE_PATHS, [LOADED_IN_EDITOR], [LOADED_IN_MENU, LOADED_IN_EDITOR])
        Api.api_initiated_singletons['Game'] = Api.api_singletons['Game'](Render, Screen, gl_context, PATH)
        Api.setup_required = False
    print('s')