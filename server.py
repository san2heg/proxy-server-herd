import asyncio
import config
import sys
import logging

# Events to log:
# (1) Input / data received
# (2) Output / response
# (3) New connections
# (4) Dropped / closed connections

class ProxyServerClientProtocol(asyncio.Protocol):
    def __init__(self, server_name):
        self.name = server_name
        self.floodlist = config.SERVER_FLOODLIST[server_name]

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.info('New connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        logger.info('Received input data: {!r}'.format(message))

        logger.info('Sending output response: {!r}'.format(message))
        self.transport.write(data)

        self.flood()

        peername = self.transport.get_extra_info('peername')
        logger.info('Dropping connection from {}\n'.format(peername))
        self.transport.close()

    def flood(self):
        for server_name in self.floodlist:
            self.propagate(server_name, config.SERVER_PORT[server_name])

    def propagate(self, name, port):
        coro = loop.create_connection(lambda: ProxyClientProtocol('Propagating'), config.SERVER_HOST, port)
        loop.create_task(coro)

class ProxyClientProtocol(asyncio.Protocol):
    def __init__(self, message):
        self.message = message

    def connection_made(self, transport):
        transport.write(self.message.encode())
        self.transport = transport

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

    # Setup logging
    logger = logging.getLogger(server_name)

    log_format = '%(asctime)s - %(levelname)s (%(name)s) : %(message)s'
    formatter = logging.Formatter(log_format)

    log_dest = './logs/' + server_name.lower() + '.log'
    file_handler = logging.FileHandler(log_dest, mode='w')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel('INFO')
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Start server
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: ProxyServerClientProtocol(server_name), config.SERVER_HOST, port_num)
    server = loop.run_until_complete(coro)

    # Serve requests until KeyboardInterrupt
    logger.info('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
