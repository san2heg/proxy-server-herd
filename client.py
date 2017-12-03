import asyncio
import sys
import config
import time

class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, loop):
        self.message = message
        self.loop = loop

    def connection_made(self, transport):
        transport.write(self.message.encode())
        print('Data sent: {!r}'.format(self.message))

    def data_received(self, data):
        print('Data received: {}'.format(data.decode()))

    def connection_lost(self, exc):
        print('The server closed the connection')
        print(str(exc))
        print('Stop the event loop')
        self.loop.stop()

if __name__ == '__main__':
    server_name = sys.argv[1]
    message = sys.argv[2]
    port_num = config.SERVER_PORT[server_name]

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(lambda: EchoClientProtocol(message, loop),
                                  '127.0.0.1', port_num)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
