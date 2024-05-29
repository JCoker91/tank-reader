'''Telnet Connection Class'''
import asyncio
import logging
import telnetlib3

from util.Exceptions.custom_exceptions import CriticalError, SimpleError


class TelnetConnector:
    '''Telnet Connector Class'''
    def __init__(self):
        self.logger = logging.getLogger()
        self.reader = None
        self.writer = None
        self.logger.debug("Telnet Connector Initialized")

    async def open_connection(self, host: str, port: int):
        '''Opens a new telnet connection'''
        if self.reader and self.writer:
            self.logger.debug("Closing existing connection")
            self.reader.close()
            self.writer.close()
        try:
            self.logger.debug("Establishing Telnet connection")
            self.logger.debug("HOST: %s PORT: %s", host, port)
            self.reader, self.writer = await telnetlib3.open_connection(host, port)
            self.logger.info("Successfully established connection to %s", host)
        except KeyboardInterrupt as e:
            self.logger.critical("Process Canceled by user. Exiting.")
            raise CriticalError("Process Canceled by user. Exiting.") from e
        except ConnectionRefusedError as e:
            self.logger.error("Connection refused by host %s on port %s", host, port)
            raise SimpleError from e

    async def close_connection(self, host):
        '''Closes the current telnet connection'''
        if not self.reader or not self.writer:
            self.logger.warning("No connection to close.")
            return
        self.reader.close()
        self.writer.close()
        self.reader, self.writer = None, None
        self.logger.debug("Connection to %s closed", host)

    async def retrieve_data(self, command: str) -> bytes:
        '''Get tank data from established connection'''
        if not self.reader or not self.writer:
            self.logger.error("No connection established.")
            raise SimpleError("No connection established.")
        try:
            action = f"\x01{command}"
            self.logger.debug("Command sent to host: %s", action)
            self.writer.write(action)
            response = await self.reader.readuntil(b'\x03')
            self.logger.info("Successfully received response received from host.")
            return response
        except KeyboardInterrupt as e:
            self.logger.critical("Process Canceled by user. Exiting.")
            raise CriticalError("Process Canceled by user. Exiting.") from e
        except asyncio.exceptions.IncompleteReadError as e:
            self.logger.error("Failed to receive a response from host.")
            raise SimpleError("Failed to receive a response from host.") from e
        except ConnectionResetError as e:
            self.logger.error("Connection reset by host.")
            raise SimpleError("Connection reset by host.") from e
        except asyncio.exceptions.TimeoutError as e:
            self.logger.error("Connection timed out.")
            raise SimpleError("Connection timed out.") from e
        except AssertionError as e:
            self.logger.error("Assertion Error: %s", e)
            raise SimpleError("Assertion Error.") from e

    async def get_tank_data(self, host, port, command) -> str:
        '''Gets tank data'''
        self.logger.info("Getting tank data for host %s on port %s", host, port)
        try:
            await self.open_connection(host, port)
            try:
                response = await self.retrieve_data(command)
                content = response.decode()
                content = content.replace('\x01' + command, '').replace('\x03', '')
                self.logger.debug("Response decoded")
                return content
            except CriticalError as e:
                raise CriticalError from e
            except KeyboardInterrupt as e:
                raise CriticalError from e
            except SimpleError as e:
                raise SimpleError from e
            finally:
                await self.close_connection(host)
        except SimpleError as e:
            self.logger.error("Failed to retreive data.")
            raise SimpleError from e
