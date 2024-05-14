'''Test Telnet Client'''
import asyncio
import telnetlib3

EXPORT_FOLDER = 'exports'
HOST = '10.30.100.56'
PORT = 10001

HOST = '10.30.105.38'
PORT = 10002

HOST = '10.30.113.56'
PORT = 10001

HOST = '10.30.104.56'
PORT = 10001

HOST = '10.30.115.56'
PORT = 10001

HOST = '10.30.120.38'
PORT = 10002

HOST = '10.30.119.56'
PORT = 10001

HOST = '10.30.127.56'
PORT = 10001


async def main():
    '''Main Function'''
    reader, writer = await telnetlib3.open_connection(HOST, PORT)
    reply = ''
    try:
        action = "\x01200"
        writer.write(action)
        reply = await reader.readuntil(b'\x03')
    except KeyboardInterrupt as e:
        print(f"Canceled by user.\n{e}")
    except asyncio.exceptions.IncompleteReadError as e:
        print(f"Failed to fetch data.\n{e}")
    except Exception as e:
        print(f"Something unexpected happened:\n{e}")
        with open('errors.txt', mode='a', encoding='utf-8') as file:
            file.write(str(e) + '\n')
    finally:
        reader.close()
    content = reply.decode()
    list_content = content.split('\r\n')
    list_content = list_content[2:len(list_content)-2]
    with open(f"{EXPORT_FOLDER}/{list_content[0].strip()}.txt",
              mode='w',
              encoding='utf-8') as file:
        for item in list_content:
            file.write(item + '\n')

asyncio.run(main())
