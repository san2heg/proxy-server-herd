import asyncio
import config
import sys
import logging
import datetime
import time

# Events to log:
# (1) Input / data received
# (2) Output / response
# (3) New connections
# (4) Dropped / closed connections

class ProxyServerClientProtocol(asyncio.Protocol):
    def __init__(self, server_name):
        self.name = server_name
        self.floodlist = config.SERVER_FLOODLIST[server_name]
        self.locations = {} # Maps client names => locations

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.info('New connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        logger.info('Received input data: {!r}'.format(message))

        input_list = message.split()
        cmd = input_list[0]
        args = input_list[1:]
        if (cmd == 'IAMAT' and self.check_IAMAT(args)):
            response_msg = self.response_IAMAT(input_list[1], input_list[2], input_list[3])
        elif (cmd == 'WHATSAT' and self.check_WHATSAT(args)):
            response_msg = self.response_WHATSAT(input_list[1], input_list[2], input_list[3])
        elif (cmd == 'AT' and self.check_AT(args)):
            origin_server = input_list[1]
            response_msg = 'AT...'
        else:
            response_msg = '? ' + message

        self.transport.write(response_msg.encode())
        logger.info('Sent output response: {!r}'.format(message))

        # self.flood('Propagating')

        peername = self.transport.get_extra_info('peername')
        self.transport.close()
        logger.info('Dropped connection from {}\n'.format(peername))

    # TODO
    # Returns True if time_str is a valid ISO 6709 location stamp
    def check_location(self, loc_str):
        return True

    # Returns True if time_str is a valid POSIX/UNIX timestamp
    def check_time(self, time_str):
        try:
            time = float(time_str)
            datetime.datetime.utcfromtimestamp(time)
        except ValueError:
            return False
        return True

    # Example request:
    # IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1479413884.392014450
    def check_IAMAT(self, args):
        if (len(args) != 3):
            logger.error('Invalid number of args for IAMAT')
            return False
        # Check ISO 6709 format
        if (not self.check_location(args[1])):
            logger.error('Invalid ISO 6709 location for IAMAT')
            return False
        # Check POSIX time
        if (not self.check_time(args[2])):
            logger.error('Invalid POSIX time for IAMAT')
            return False
        return True

    # Example request:
    # WHATSAT kiwi.cs.ucla.edu 10 5
    def check_WHATSAT(self, args):
        # Check number of args
        if (len(args) != 3):
            return False
        return True

    # Example request:
    # AT Alford +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1479413884.392014450
    def check_AT(self, args):
        return True

    # Example response:
    # AT Alford +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1479413884.392014450
    def response_IAMAT(self, client_id, loc_str, time_str):
        # Calculate time difference
        time_difference = time.time() - float(time_str)
        time_diff_str = '{:.9f}'.format(time_difference)
        if time_difference > 0:
            time_diff_str = '+' + time_diff_str

        # Add/update client location
        self.locations[client_id] = loc_str

        return 'AT {} {} {} {} {}'.format(self.name, time_diff_str, client_id, loc_str, time_str)

    def response_WHATSAT(self, client_id, radius, bound):
        return 'WHATSAT response'

    def flood(self, msg, origin_server):
        for server_name in self.floodlist:
            self.propagate(server_name, config.SERVER_PORT[server_name], msg)

    def propagate(self, name, port, msg):
        coro = loop.create_connection(lambda: ProxyClientProtocol(msg), config.SERVER_HOST, port)
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
