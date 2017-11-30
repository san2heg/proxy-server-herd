import asyncio
import config
import sys
import logging

class ProxyServerClientProtocol(asyncio.Protocol):
    def __init__(self, server_name):
        self.name = server_name
        self.floodlist = config.SERVER_FLOODLIST[server_name]
        self.__init_logger()

    # Setup for logger
    def __init_logger(self):
        self.logger = logging.getLogger(self.name)
        formatter = logging.Formatter('%(asctime)s - (%(name)s) %(levelname)s : %(message)s')
        fileHandler = logging.FileHandler("./logs/" + self.name.lower() + ".log", mode='w')
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        self.logger.setLevel('INFO')
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)
        self.logger.info('Server Protocol Initialized')

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.logger.info('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        self.logger.info('Data received: {!r}'.format(message))

        self.logger.info('Send: {!r}'.format(message))
        self.transport.write(data)

        self.logger.info('Close the client socket')
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
    server_protocol = ProxyServerClientProtocol(server_name)

    # Start server
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: ProxyServerClientProtocol(server_name), config.SERVER_HOST, port_num)
    server = loop.run_until_complete(coro)

    # Serve requests until KeyboardInterrupt
    logger = logging.getLogger(server_name)
    logger.info('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
