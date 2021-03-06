import json

settings_json = json.dumps([
	{'type': 'string',
	 'title': 'Name',
	 'desc': 'Choose a name',
	 'section': 'game',
	 'key': 'username'},
	{'type': 'options',
	 'title': 'Number of Players',
	 'desc': 'Number of players',
	 'section': 'game',
	 'key': 'num_players',
	 'options': ['2', '3', '4'] },
	 {'type': 'bool',
	  'title': 'Networking',
	  'desc': 'Enable networked multiplayer',
	  'section': 'game',
	  'key': 'enable_networking'}
	 ])
