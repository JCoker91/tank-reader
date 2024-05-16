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

    def write_to_json(self, file: str, export_file_name: str) -> None:
        '''Parses the text from tank file and writes it to json file'''
        data = []
        self.logger.info("Loading data from file: %s", file)
        try:
            with open(file, mode='r', encoding='utf-8') as f:
                data = f.readlines()
            self.logger.info("Successfully loaded data from file: %s", file)
        except FileNotFoundError as e:
            self.logger.critical("Data file not found.")
            raise SimpleError("Data file not found.") from e
        self.logger.debug("Data loaded from file.")
        self.logger.debug("Begin listing rows received:")
        for row in data:
            self.logger.debug("%s", row)
        self.logger.debug("End listing rows from response")
        remove_rows = 0
        for j in data:
            if j[:4] == 'TANK':
                self.logger.debug("Header row found at row %s", remove_rows)
                break
            remove_rows += 1
        data = data[remove_rows:]
        self.logger.debug("Data cleaned up. Begin listing rows in cleaned data:")
        for row in data:
            self.logger.debug("%s", row)
        self.logger.debug("End listing rows from cleaned data")
        try:
            header_row = data[0]
        except IndexError as e:
            self.logger.error("No data found in file.")
            raise SimpleError("No data found in file.") from e
        self.logger.debug("Header row: %s", header_row)
        headers = [
            'TANK',
            'PRODUCT',
            'GALLONS',
            'INCHES',
            'WATER',
            'DEG F',
            'ULLAGE'
        ]
        self.logger.debug("Headers: %s", headers)
        header_indexes = {}
        column_width = {}
        for index in headers:
            header_indexes[index] = header_row.index(index)
        self.logger.debug("Header Indexes found at the following: ")
        for key, value in header_indexes.items():
            self.logger.debug("%s: %s", key, value)

        headers.reverse()
        current_count = len(header_row)
        for index in headers:
            column_width[index] = current_count - header_indexes[index]
            current_count = header_indexes[index]
        headers.reverse()
        self.logger.debug("Column Widths found at the following: ")
        for key, value in column_width.items():
            self.logger.debug("%s: %s", key, value)
        json_data = []
        data_entries = {}
        for row in data[1:]:
            if len(row) == len(header_row):
                for index in headers:
                    value = row[header_indexes[index]:header_indexes[index]+column_width[index]].strip()
                    data_entries[index] = value
                copied_data = data_entries.copy()
                self.logger.debug("Data Entry Added: %s", copied_data)
                json_data.append(copied_data)
        self.logger.info("Successfully parsed data from file.")
        try:
            with open(export_file_name, mode='w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4)
            self.logger.info("Successfully wrote data to %s", export_file_name)
        except FileNotFoundError as e:
            self.logger.error("File path not found: %s", export_file_name)
            raise SimpleError("File path not found.") from e


if __name__ == '__main__':
    with open('data/test_tanks.json', 'r', encoding='utf-8') as fi:
        datas = json.load(fi)
        assert 'Host' in datas[0].keys()
        assert 'Location' in datas[0].keys()
        print(len(datas))
