# DEFAULT CONFIGURATION FOR SERVERS

# Google Places API Information
API_KEY = 'AIzaSyBXZj8pSVL82G08tUNVnBf4TigDIOZ-uIc'
API_TARGET = '/maps/api/place/nearbysearch/json?'
API_HOST = 'maps.googleapis.com'

# Server List
SERVER_LIST = ['Alford', 'Hamilton', 'Holiday', 'Ball', 'Welsh']

# Server Flooding Mappings
SERVER_FLOODLIST = {}
SERVER_FLOODLIST['Alford'] = ['Hamilton', 'Welsh']
SERVER_FLOODLIST['Hamilton'] = ['Holiday', 'Alford']
SERVER_FLOODLIST['Holiday'] = ['Ball', 'Hamilton']
SERVER_FLOODLIST['Ball'] = ['Welsh', 'Holiday']
SERVER_FLOODLIST['Welsh'] = ['Alford', 'Ball']

# Server Port Mappings
SERVER_PORT = {}
SERVER_PORT['Alford'] = 17415
SERVER_PORT['Hamilton'] = 17416
SERVER_PORT['Holiday'] = 17417
SERVER_PORT['Ball'] = 17418
SERVER_PORT['Welsh'] = 17419

HTTPS_PORT = 443

# Server Host
SERVER_HOST = '127.0.0.1'
