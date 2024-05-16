'''Test Telnet Client'''
import sys
import logging
import asyncio

from conf import Settings
from util.Exceptions.custom_exceptions import CriticalError, SimpleError
from util.DataLoader.data_loader import DataLoader
from util.TelnetConnetor.telnet_connector import TelnetConnector
from util.Enums.mode import Mode


async def main():
    '''Main Function'''
    logger = logging.getLogger()
    logger.debug("Starting main process")
    logger.info("Running in mode: %s",
                "Production" if Settings.MODE == Mode.PROD
                else "Debug" if Settings.MODE == Mode.DEBUG
                else "Unknown")
    dl = DataLoader()
    file = f'{Settings.DATA_FOLDER}/{Settings.PROD_FILE}'\
        if Settings.MODE == Mode.PROD \
        else f'{Settings.DATA_FOLDER}/{Settings.TEST_FILE}' \
        if Settings.MODE == Mode.DEBUG \
        else ''
    try:
        tank_data = dl.load_json_file(file)
    except CriticalError:
        logger.critical("Critical Error loading data. Exiting.")
        sys.exit(1)
    logger.debug("Iterating over data.")
    telnet_connector = TelnetConnector()
    success_count = 0
    failed_list = []
    for tank in tank_data:
        logger.info("Retrieving data from %s....", tank['Location'])
        try:
            response_content = await telnet_connector.get_tank_data(host=tank['Host'],
                                                                    port=tank['Port'],
                                                                    command=tank['Command'])
        except CriticalError as e:
            logger.critical("Critical Error: %s", e)
            logger.critical("Exiting...")
            sys.exit(1)
        except SimpleError:
            logger.error(
                "Failed to retrieve data from %s at %s on port %s with command %s. Skipping...",
                tank['Location'],
                tank['Host'],
                tank['Port'],
                tank['Command'])
            failed_list.append(tank['Location'])
            continue
        try:
            data = response_content.split('\r\n')
            data = data[2:len(data)-2]
            dl.write_list_to_file(data, f"{Settings.EXPORT_FOLDER}/{tank['Location']}.txt")
        except SimpleError as e:
            logger.error("Failed to write data to file: %s", e)
            failed_list.append(tank['Location'])
            continue
        except CriticalError as e:
            logger.critical("Critical Error: %s", e)
            failed_list.append(tank['Location'])
            continue
        logger.info("Successfully wrote data for %s.", tank['Location'])
        logger.info("Writing data to JSON file...")
        try:
            dl.write_to_json(f"{Settings.EXPORT_FOLDER}/{tank['Location']}.txt",
                             f"{Settings.JSON_EXPORT_FOLDER}/{tank['Location']}.json")
            success_count += 1
        except CriticalError as e:
            logger.critical("Critical Error: %s", e)
            failed_list.append(tank['Location'])
            continue
        except SimpleError as e:
            logger.error("Failed to write data to JSON file: %s", e)
            failed_list.append(tank['Location'])
            continue
    logger.info("Successfully wrote data for %s out of %s tanks.", success_count, len(tank_data))
    if len(failed_list) > 0:
        logger.warning("Failed to write data for %s tanks.", len(tank_data) - success_count)
        logger.warning("Failed tanks: %s", failed_list)


if __name__ == '__main__':
    logger_formatter = logging.Formatter(
        '%(levelname)s::%(module)s::%(filename)s::%(funcName)s::%(message)s'
        )
    stream_logger = logging.StreamHandler(sys.stdout)
    file_logger = logging.FileHandler(
        filename=f'{Settings.LOG_FOLDER}/log.log',
        mode='w')
    stream_logger.formatter = logger_formatter
    file_logger.formatter = logger_formatter
    root_logger = logging.getLogger()
    root_logger.addHandler(stream_logger)
    root_logger.addHandler(file_logger)
    root_logger.level = Settings.LOG_LEVEL
    root_logger.debug("Provided Arguments: %s", list(sys.argv))
    root_logger.debug("Log Folder: %s", Settings.LOG_FOLDER)
    root_logger.debug("Export Folder: %s", Settings.EXPORT_FOLDER)
    asyncio.run(main())
    root_logger.info("Process complete.")
