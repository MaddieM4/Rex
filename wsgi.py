''' 

HTTP interface for public address storage.

'''

import gevent
import bottle

import user

hosted = {}

app = bottle.Bottle()

bottle.debug(True)

@app.get('/ip/:name')
def get_ip(name):
	if name in hosted:
		bottle.response.set_content_type('text/plain')

		thisuser = hosted[name]
		yield thisuser.public + "\r\n"
		yield thisuser.private + "\r\n"
		if thisuser.signed:
			yield thisuser.sig + "\r\n"
	else:
		bottle.abort(404, "User not stored")

@app.post('/ip/:name')
def post_ip(name):
	if not name in hosted:
		hosted[name] = user.User(name)
	thisuser = hosted[name]

	input = dict(bottle.request.forms)

	thisuser.public = input['public_ip']
	thisuser.private = input['private_ip']

	return ["Set successfully"]

@app.route('/wizard/:name/set')
def wizard_set(name):
	return [
		"<html><head><title>Rex Form Wizard: Host an IP</title></head><body>",
		'<form action="/ip/%s" method="post">' % name,
		'Public IP: <input type="text" name="public_ip" /><br/>',
		'Private IP: <input type="text" name="private_ip" /><br/>',
		'<input type="submit" />',
		"</form></body></html>"
	]

@app.route("/favicon.ico")
def favicon():
	return bottle.static_file("logo.ico", "./img/")

def start(port=8000):
	return gevent.spawn(bottle.run, app, server="gevent", host="0.0.0.0", port = port)
