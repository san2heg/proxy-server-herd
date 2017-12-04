import asyncio
import config
import sys
import logging
import datetime
import time
import ssl
import json

# Write message to transport
def send_response(transport, message):
    transport.write(message.encode())
    logger.info('Sent output response: {!r}'.format(message))

# Close connection identified by transport
def close_connection(transport):
    transport.close()
    peername = transport.get_extra_info('peername')
    logger.info('Dropped connection from {}\n'.format(peername))

# Catch exceptions that get thrown in the event loop
def catch_exceptions(loop, context):
    try:
        exception = context['exception']
        if isinstance(exception, ConnectionRefusedError):
            logger.error('Failed to connect, neighboring server might be down')
        else:
            logger.error('Generic Error => {}'.format(context['message']))
    except KeyError:
        logger.error('Generic Error => {}'.format(context['message']))

class ProxyServerClientProtocol(asyncio.Protocol):
    # Maps client IDs => most recent AT stamp
    client_stamps = {}

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

        input_list = message.split()
        cmd = input_list[0]
        args = input_list[1:]
        if (cmd == 'IAMAT' and self.check_IAMAT(args)):
            response_msg = self.response_IAMAT(input_list[1], input_list[2], input_list[3])
        elif (cmd == 'WHATSAT' and self.check_WHATSAT(args)):
            self.send_WHATSAT(input_list[1], input_list[2], input_list[3], message)
            return
        elif (cmd == 'AT'):
            response_msg = self.response_AT(input_list[3], message)
        else:
            response_msg = '? ' + message

        send_response(self.transport, response_msg)
        close_connection(self.transport)

    def flood(self, msg):
        counterlist = msg.split()[5:]
        for server_name in self.floodlist:
            if server_name not in counterlist:
                self.propagate(server_name, config.SERVER_PORT[server_name], msg)

    def propagate(self, name, port, msg):
        coro = loop.create_connection(lambda: ProxyClientProtocol(msg, name), config.SERVER_HOST, port)
        loop.create_task(coro)

    def get_client_location(self, client_id):
        loc_str = ProxyServerClientProtocol.client_stamps[client_id].split()[4]
        return self.parse_location(loc_str)

    def parse_stamp_time(self, stamp):
        return float(stamp.split()[5])

    def update_client_stamp(self, client_id, stamp):
        if stamp.split()[3] != client_id:
            logger.error('Bad call to update_client_stamp')
            return False
        update = False
        try:
            if self.parse_stamp_time(stamp) > self.parse_stamp_time(ProxyServerClientProtocol.client_stamps[client_id]):
                ProxyServerClientProtocol.client_stamps[client_id]
                update = True
        except KeyError:
            ProxyServerClientProtocol.client_stamps[client_id] = stamp
            update = True
        if update:
            logger.info('Updated location data for {}'.format(client_id))
        else:
            logger.warning('Did not update location data for {}'.format(client_id))
        return update

    # Returns lat, lng string tuple given latlng combined string
    def parse_location(self, loc_str):
        lat_str, lng_str = '', ''
        split_flag, first_flag = True, True
        for char in loc_str:
            if ((not first_flag) and (char == '+' or char == '-')):
                split_flag = False
            if split_flag:
                lat_str += char
            else:
                lng_str += char
            if first_flag: first_flag = False
        return lat_str, lng_str

    # Returns True if time_str is a valid ISO 6709 location stamp
    def check_location(self, loc_str, client_id):
        try:
            lat_str, lng_str = self.parse_location(loc_str)
            lat, lng = float(lat_str), float(lng_str)
        except ValueError:
            return False
        if lat > 90 or lat < -90: return False
        if lng > 180 or lat < -180: return False
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
        if (not self.check_location(args[1], args[0])):
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
            logger.error('Invalid number of args for WHATSAT')
            return False
        # Check if client_id location exists
        try:
            ProxyServerClientProtocol.client_stamps[args[0]]
        except KeyError:
            logger.error('Client does not yet have a location')
            return False
        # Check types
        try:
            radius = float(args[1])
            bound = int(args[2])
        except ValueError:
            logger.error('Incorrect type for radius or bound')
            return False
        # Check range
        if radius > 50 or radius < 0:
            logger.error('Radius out of range')
            return False
        if bound > 20 or bound < 0:
            logger.error('Bound out of range')
            return False
        return True

    def response_AT(self, client_id, msg):
        # Update client's AT stamp
        stamp = ' '.join(msg.split()[:6])
        self.update_client_stamp(client_id, stamp)

        flood_msg = msg + ' {}'.format(self.name)
        self.flood(flood_msg)
        return 'Received updated location'

    # Example response:
    # AT Alford +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1479413884.392014450
    def response_IAMAT(self, client_id, loc_str, time_str):
        # Calculate time difference
        time_difference = time.time() - float(time_str)
        time_diff_str = '{:.9f}'.format(time_difference)
        if time_difference > 0:
            time_diff_str = '+' + time_diff_str

        # Update client's AT stamp
        stamp = 'AT {} {} {} {} {}'.format(self.name, time_diff_str, client_id, loc_str, time_str)
        self.update_client_stamp(client_id, stamp)

        # Propagate AT stamp to neighboring servers
        self.flood(stamp + ' ' + self.name)
        return ProxyServerClientProtocol.client_stamps[client_id]

    def send_WHATSAT(self, client_id, radius_km, info_bound, err_msg):
        print('here')
        client_loc = self.get_client_location(client_id)

        # Convert km to m for radius
        radius_m = str(float(radius_km) * 1000)

        # Build raw HTTP GET request
        loc_str = '{},{}'.format(client_loc[0], client_loc[1])
        target = '{}location={}&radius={}&key={}'.format(config.API_TARGET, loc_str, radius_m, config.API_KEY)
        host = config.API_HOST
        request_str = self.build_http_request(host, target)

        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Build PlacesHTTPClientProtocol lambda
        protocol = lambda: PlacesHTTPClientProtocol(request_str, self.transport, int(info_bound), ProxyServerClientProtocol.client_stamps[client_id])

        # Make HTTP request on top of TCP
        logger.info('Sending HTTP request => ' + request_str)
        coro = loop.create_connection(protocol, config.API_HOST, config.HTTPS_PORT, ssl=context)
        loop.create_task(coro)

    # Returns a correctly formatted raw HTTP request given host and target
    def build_http_request(self, host, target):
        request = ''
        request += 'GET {} HTTP/1.1\r\n'.format(target)
        request += 'Host: {}\r\n'.format(host)
        request += '\r\n'
        return request

class ProxyClientProtocol(asyncio.Protocol):
    def __init__(self, message, name):
        self.message = message
        self.prop_name = name

    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(self.message.encode())
        logger.info('Propagated location data to {}\n'.format(self.prop_name))

    def connection_lost(self, exc):
        self.transport.close()

class PlacesHTTPClientProtocol(asyncio.Protocol):
    def __init__(self, request, first_transport, bound, header):
        self.request = request
        self.bound = bound
        self.header = header
        # self.first_tranport is the connection to original client
        self.first_transport = first_transport
        # Used to properly close connection from API
        self.double_crlf_count = 0
        # Accumulate data before writing to transport
        self.response_accum = ''

    def connection_made(self, transport):
        # self.transport is the connection to Google Places API
        self.transport = transport
        self.transport.write(self.request.encode())

    def data_received(self, data):
        self.response_accum += data.decode()
        self.double_crlf_count += data.decode().count('\r\n\r\n')
        # Manually close connection if a response body end is detected
        if (self.double_crlf_count >= 2):
            json_str = self.parse_data(self.response_accum)
            send_response(self.first_transport, json_str)
            close_connection(self.first_transport)
            self.transport.close()

    # Take raw data string from Google Places API and return bounded json
    # string with AT stamp
    def parse_data(self, data):
        # Process string to prepare for json conversion
        data_right = data.split('\r\n\r\n')[1]
        start, end = data_right.index('{'), data_right.rindex('}')
        json_str = data_right[start:end+1]
        json_str = json_str.strip().replace('\r\n', '').replace('\n', '')

        # Convert to json and limit results to bound
        json_obj = json.loads(json_str)
        if len(json_obj['results']) > self.bound:
            json_obj['results'] = json_obj['results'][:self.bound]

        return self.header + '\n' + json.dumps(json_obj, indent=2) + '\n\n'

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
    # loop.set_exception_handler(catch_exceptions)
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
