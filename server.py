import asyncio
import config
import sys

class ProxyServerClientProtocol(asyncio.Protocol):
    def __init__(self, server_name, neighbors):
        self.name = server_name
        self.neighbors = neighbors

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        print('Data received: {!r}'.format(message))

        print('Send: {!r}'.format(message))
        self.transport.write(data)

        print('Close the client socket')
        self.transport.close()

if __name__ == '__main__':
    # Check for bad args
    if (len(sys.argv) != 2):
        print('Please provide an appropriate server name.')
        exit(1)

    # Check for invalid server name
    server_name = sys.argv[1]
    if not server_name in config.SERVER_LIST:
        print('Invalid server name. Use Alford, Ball, Hamilton, Holiday, or Welsh.')
        exit(1)
    port_num = config.SERVER_PORT[server_name]

    # Build server
    server_protocol = ProxyServerClientProtocol(server_name, config.SERVER_FLOODLIST[server_name])

    # Start server
    loop = asyncio.get_event_loop()
    coro = loop.create_server(server_protocol, config.SERVER_HOST, config.SERVER_PORT[server_name])
    server = loop.run_until_complete(coro)

    # Serve requests until KeyboardInterrupt
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
