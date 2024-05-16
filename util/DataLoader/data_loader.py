'''Custom Data Loader Class to Handle Various Methods'''
import json
import logging
from typing import List

from util.Exceptions.custom_exceptions import CriticalError, SimpleError


class DataLoader:
    '''Class to handle data loading'''
    def __init__(self):
        self.logger = logging.getLogger()

    def verify_file_spec(self, data: dict) -> None:
        '''Verifies that the data is in the correct format'''
        assert 'Host' in data[0].keys()
        assert 'Location' in data[0].keys()
        assert 'Port' in data[0].keys()
        assert 'Command' in data[0].keys()
        self.logger.debug("Data format verified.")

    def load_json_file(self, file: str) -> dict:
        '''Reads a local json file and returns the data as a dictionary'''
        self.logger.info("Loading data from file: %s", file)
        try:
            with open(file, mode='r', encoding="utf-8") as f:
                tank_data = json.load(f)
                try:
                    self. verify_file_spec(tank_data)
                except AssertionError as e:
                    raise CriticalError("Data file is not in the correct format.") from e
                self.logger.info("Successfully loaded and verified data from %s", file)
                self.logger.debug("Loaded Data: %s", tank_data)
                return tank_data
        except FileNotFoundError as e:
            self.logger.critical("Data file not found.")
            raise CriticalError("Data file not found.") from e
        except json.JSONDecodeError as e:
            self.logger.critical("Data file is not a valid JSON file.")
            raise CriticalError("Data file is not a valid JSON file.") from e

    def write_list_to_file(self, data: List[str], file_name: str) -> None:
        '''Writes a list of strings to a file'''
        self.logger.debug("Begin listing rows received:")
        for row in data:
            self.logger.debug("%s", row)
        self.logger.debug("End listing rows from response")
        self.logger.info("Writing contents to %s...", file_name)
        try:
            with open(f"{file_name}", mode='w', encoding='utf-8') as file:
                for row in data:
                    file.write(row + '\n')
            self.logger.info("Successfully wrote contents to %s", file_name)
        except PermissionError as e:
            self.logger.error("Permission denied to write to file: %s", file_name)
            raise CriticalError("Permission denied to write to file.") from e
        except FileNotFoundError as e:
            self.logger.error("Provided file path not found: %s", file_name)
            raise SimpleError("Provided file path not found.") from e


if __name__ == '__main__':
    with open('data/test_tanks.json', 'r', encoding='utf-8') as fi:
        datas = json.load(fi)
        assert 'Host' in datas[0].keys()
        assert 'Location' in datas[0].keys()
        print(len(datas))
