# Application Server Herd using Python's [asyncio](https://docs.python.org/3/library/asyncio.html)

Project Spec: http://web.cs.ucla.edu/classes/fall17/cs131/hw/pr.html

## Start server
```
python3 server.py Alford
```

### Start all 5 servers
```
sh run-servers.sh
```

## Client requests

### IAMAT
Tell server where you are at what time.

Arguments:
- Client ID
- ISO 6709 location
- POSIX time
```
python3 client.py Alford 'IAMAT kiwi.cs.ucla.edu 40.79617-74.063124 1332423423.412014450'
```

### WHATSAT
Request a JSON list of locations near a client. Implemented using [Google Places API](https://developers.google.com/places/)

Arguments:
- Client ID
- Radius (km)
- Information bound
```
python3 client.py Alford 'WHATSAT kiwi.cs.ucla.edu 5 10'
```
