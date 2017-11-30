# DEFAULT CONFIGURATION FOR SERVERS

# Google Places API Information
API_KEY = 'AIzaSyBXZj8pSVL82G08tUNVnBf4TigDIOZ-uIc'
API_ENDPOINT = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'

# Server List
SERVER_LIST = ['Alford', 'Hamilton', 'Holiday', 'Ball', 'Welsh']

# Server Flooding Mappings
SERVER_FLOODLIST = {}
SERVER_FLOODLIST['Alford'] = ['Hamilton', 'Welsh']
SERVER_FLOODLIST['Hamilton'] = ['Holiday']
SERVER_FLOODLIST['Holiday'] = []
SERVER_FLOODLIST['Ball'] = ['Welsh', 'Holiday']
SERVER_FLOODLIST['Welsh'] = []

# Server Port Mappings
SERVER_PORT = {}
SERVER_PORT['Alford'] = 9000
SERVER_PORT['Hamilton'] = 9001
SERVER_PORT['Holiday'] = 9002
SERVER_PORT['Ball'] = 9003
SERVER_PORT['Welsh'] = 9004

# Server Host
SERVER_HOST = '127.0.0.1'
