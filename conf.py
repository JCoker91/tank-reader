'''
Configuration file for the project. Contains the settings for the project.
'''
import logging
from util.Enums.mode import Mode


class Settings:
    '''Settings for the project'''
    EXPORT_FOLDER = 'exports'
    LOG_FOLDER = 'logs'
    LOG_LEVEL = logging.INFO
    DATA_FOLDER = 'data'
    MODE = Mode.PROD
    PROD_FILE = 'fb_tanks.json'
    TEST_FILE = 'test_tanks.json'
    JSON_EXPORT_FOLDER = 'json_exports'
