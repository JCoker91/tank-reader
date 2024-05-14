'''Telnet Test Server'''
import asyncio
import telnetlib3

HOST = "localhost"
PORT = 6023


async def shell(reader, writer):
    '''Creates the shell environment'''
    writer.write('\r\nWould you like to play a game? ')
    inp = await reader.read(4)
    if inp:
        writer.echo(inp + ' was your input')
        print(inp + ' was your input')
        await writer.drain()
    writer.close()

loop = asyncio.get_event_loop()
coro = telnetlib3.create_server(port=6023, shell=shell)
server = loop.run_until_complete(coro)
loop.run_until_complete(server.wait_closed())
