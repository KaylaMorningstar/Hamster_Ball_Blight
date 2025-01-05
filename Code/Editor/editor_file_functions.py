import json
from jsonschema import validate
from __main__ import PATH
from Code.utilities import path_exists, create_folder


PROJECT_NAME_CHARACTER_LIMIT = 50

WRITE = 'w'
ENSURE_ASCII = False
INDENT = 4
ENCODING = 'utf-8'


def create_project(project_name):
    if project_name > PROJECT_NAME_CHARACTER_LIMIT:
        return False, f'project name must be less than {PROJECT_NAME_CHARACTER_LIMIT} characters'
    
    project_path = PATH + '\\Projects\\' + project_name
    if path_exists(project_path):
        return False, f'project named "{project_name}" already exists'

    create_folder(project_path)
    # create_project_data_file(project_path)

    return True, f'successfully created project "{project_name}"'


# def create_project_data_file(project_path):
#     with open(project_path, WRITE, encoding=ENCODING) as json_file:
#         json.dump(data, json_file, ensure_ascii=ENSURE_ASCII, indent=INDENT)

