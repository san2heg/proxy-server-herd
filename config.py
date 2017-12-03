# DEFAULT CONFIGURATION FOR SERVERS

# Google Places API Information
API_KEY = 'AIzaSyBXZj8pSVL82G08tUNVnBf4TigDIOZ-uIc'
API_TARGET = '/maps/api/place/nearbysearch/json?'
API_HOST = 'maps.googleapis.com'

# Server List
SERVER_LIST = ['Alford', 'Hamilton', 'Holiday', 'Ball', 'Welsh']

# Server Flooding Mappings
SERVER_FLOODLIST = {}
# SERVER_FLOODLIST['Alford'] = ['Hamilton', 'Welsh']
# SERVER_FLOODLIST['Hamilton'] = ['Holiday', 'Alford']
# SERVER_FLOODLIST['Holiday'] = ['Ball', 'Hamilton']
# SERVER_FLOODLIST['Ball'] = ['Welsh', 'Holiday']
# SERVER_FLOODLIST['Welsh'] = ['Alford', 'Ball']

SERVER_FLOODLIST['Alford'] = ['Hamilton']
SERVER_FLOODLIST['Hamilton'] = []
SERVER_FLOODLIST['Holiday'] = []
SERVER_FLOODLIST['Ball'] = []
SERVER_FLOODLIST['Welsh'] = []

# Server Port Mappings
SERVER_PORT = {}
SERVER_PORT['Alford'] = 9000
SERVER_PORT['Hamilton'] = 9001
SERVER_PORT['Holiday'] = 9002
SERVER_PORT['Ball'] = 9003
SERVER_PORT['Welsh'] = 9004

HTTPS_PORT = 443

# Server Host
SERVER_HOST = '127.0.0.1'
