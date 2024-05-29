'''Custom Data Loader Class to Handle Various Methods'''
import json
import logging
from typing import List

from util.Exceptions.custom_exceptions import CriticalError, SimpleError


class DataLoader:
    '''Class to handle data loading'''
    def __init__(self):
        self.logger = logging.getLogger()

    def parse_full_string(self, content: str, command: str) -> dict:
        '''Parses the full string returned from the telnet command'''
        # command = "i20100"
        start_char = "\x01"
        end_char = "\x03"
        fixed_data_length = 65
        content = content.replace(start_char,
                                  "").replace(end_char,
                                              "").replace(command,
                                                          "").split("&&")[0]
        final_data = {'date': content[0:10], 'data': []}
        content = content[10:]
        data_strings = []
        while len(content) > 0:
            data_strings.append(content[0:fixed_data_length])
            content = content[fixed_data_length:]
        for data in data_strings:
            json_data = self.parse_data_string(data)
            final_data['data'].append(json_data)
        return final_data

    def parse_data_string(self, content: str) -> dict:
        '''Parses a string from a single tank'''
        tank_data = {}
        data_fields = [
            'Volume',
            'TC Volume',
            'Ullage',
            'Height',
            'Water',
            'Temperature',
            'Water Volume'
        ]
        tank_data['tank_number'] = content[0:2]
        tank_data['product_number'] = content[2:3]
        tank_data['tank_status'] = content[3:7]
        for index, field in enumerate(data_fields):
            ieee = content[9 + (index * 8): 9 + (index * 8) + 8]
            tank_data[field] = self.parse_ascii_floating_point(ieee)
        return tank_data

    def parse_ascii_floating_point(self, hex_num: str) -> float:
        '''
        Converts the floating point hex number to a decimal based off the format provided by
        TLS-300, TLS-350, and TLS-350R

        I am using bitwise operations to extract the values from the hex number. The format is as
        follows:

        -------------------------------------------------------------------------
        Byte    |       1       |       2       |       3       |       4       |
        -------------------------------------------------------------------------
                | S EEE | EEEE  | E MMM | MMMM  | MMMM  | MMMM  | MMMM  | MMMM  |
        -------------------------------------------------------------------------
        Nibble  |   1   |   2   |   3   |   4   |   5   |   6   |   7   |   8   |
        -------------------------------------------------------------------------

        S is the sign bit (0 if positive, 1 if negative).

        EEE EEEE E represents the 2's exponent. It is a 2's complement value biased by 127 (7F
        Hex). The exponent can be determined by subtracting 127 from the value of the E field and
        raising 2 to the resulting power.

        MMM MMMM MMMM MMMM MMMM MMMM represents the 23-bit mantissa. Since
        the mantissa describes a value which is greater than or equal to 1.0 and less than 2.0,
        the 24th bit is always assumed to be equal to 1 and is not transmitted or stored.
        The value of the mantissa can be determined by dividing the value of the M field by
        8,388,608 (223) and adding 1.0.

        The complete value of the floating point number can then be determined by multiplying the
        exponent by the mantissa and attaching the appropriate positive or negative sign.

        By convention, 00 00 00 00 represents the value 0.0 even though it actually converts to
        5.8775 x 10-39.

        The eight "nibbles" are transmitted in sequence from 1 through 8 as shown
        in section 6.3.1.2.
        '''
        self.logger.debug("Hex Number received: %s", hex_num)
        try:
            bit_number = int(hex_num, 16)
            self.logger.debug("Bit Number: %s", bit_number)
        except ValueError as e:
            raise CriticalError("Invalid hex number provided.") from e

        # Byte format. Shifting the bits to the right to get the value of the bits.
        format_b = {
            'S': (31, 1, 0b1),
            'E': (23, 255, 0b11111111),
            'M': (0, 8388607, 0b11111111111111111111111)
            }
        # Extracting the values from the bit number
        # S is the sign bit (0 if positive, 1 if negative).
        s_value = -1 if (bit_number >> format_b['S'][0]) & format_b['S'][1] == 1\
            else 1
        self.logger.debug("Sign Value: %s", s_value)
        # EEE EEEE E represents the 2's exponent. It is a 2's complement value biased by 127 (7F
        # Hex). The exponent can be determined by subtracting 127 from the value of the E field and
        # raising 2 to the resulting power.
        e_value = (bit_number >> format_b['E'][0]) & format_b['E'][1]
        self.logger.debug("Exponent Value: %s", e_value)
        # MMM MMMM MMMM MMMM MMMM MMMM represents the 23-bit mantissa. Since
        # the mantissa describes a value which is greater than or equal to 1.0 and less than 2.0,
        # the 24th bit is always assumed to be equal to 1 and is not transmitted or stored.
        m_value = (bit_number >> format_b['M'][0]) & format_b['M'][1]
        self.logger.debug("Mantissa Value: %s", m_value)

        decimal_value = s_value * (2 ** (e_value - 127)) * (m_value / 8388608 + 1)
        self.logger.debug("Decimal Value: %s", decimal_value)
        return decimal_value

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

    def write_string_to_file(self, data: str, file_name: str) -> None:
        ''''Writes a string to a file'''
        self.logger.debug("Data received: %s", data)
        self.logger.info("Writing contents to %s...", file_name)
        try:
            with open(f"{file_name}", mode='w', encoding='utf-8') as file:
                file.write(data)
            self.logger.info("Successfully wrote contents to %s", file_name)
        except PermissionError as e:
            self.logger.error("Permission denied to write to file: %s", file_name)
            raise CriticalError("Permission denied to write to file.") from e
        except FileNotFoundError as e:
            self.logger.error("Provided file path not found: %s", file_name)
            raise SimpleError("Provided file path not found.") from e

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

    def write_to_json_from_dict(self, data: dict, export_file_name: str) -> None:
        '''Writes a dictionary to a json file'''
        self.logger.info("Writing data to JSON file: %s", export_file_name)
        try:
            with open(export_file_name, mode='w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.logger.info("Successfully wrote data to %s", export_file_name)
        except FileNotFoundError as e:
            self.logger.error("File path not found: %s", export_file_name)
            raise SimpleError("File path not found.") from e
        except json.JSONDecodeError as e:
            self.logger.error("Failed to write data to JSON file.")
            raise SimpleError("Failed to write data to JSON file.") from e
