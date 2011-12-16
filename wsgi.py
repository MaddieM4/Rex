''' 

HTTP interface for public address storage.

'''

import gevent
import gevent.event
import bottle

import user

print "Loading users..."
try:
	hosted = user.udictf("users.save")
	print "Done loading users (%d)" % len(hosted)
except Exception, e:
	import traceback
	traceback.print_exc()
	hosted = {}

usersChanged = gevent.event.Event()

app = bottle.Bottle()

bottle.debug(True)

def sendlink(pub_ip, url):
	# Override this function to link to holdopen side
	raise Exception()

def getuser(name):
	if not name in hosted:
		hosted[name] = user.User(name)
	return hosted[name]

@app.get('/ip/:name')
def get_ip(name):
	if name in hosted:
		thisuser = hosted[name]
		if not thisuser.public or not thisuser.private:
			bottle.abort(503, "Reserved name, but user is not online right now")

		bottle.response.set_content_type('text/plain')
		yield thisuser.public + "\r\n"
		yield thisuser.private + "\r\n"
		if thisuser.signed:
			yield thisuser.sig + "\r\n"
	else:
		bottle.abort(404, "User not stored")

@app.post('/ip/:name')
def post_ip(name):
	thisuser = getuser(name)

	input = dict(bottle.request.forms)

	if not ('public_ip' in input and 'private_ip' in input):
		bottle.abort(400, "Missing required variables")
	thisuser.public = input['public_ip']
	thisuser.private = input['private_ip']

	if thisuser.password != None:
		if 'password' not in input:
			bottle.abort(401, "Not authorized - account is password protected")
		elif not thisuser.check_password(input['password']):
			bottle.abort(401, "Not authorized - wrong password")

	usersChanged.set()

	return ["Set successfully"]

@app.post('/wake/:name')
def wake(name):
	thisuser = getuser(name)
	input = dict(bottle.request.forms)

	if not (thisuser.public):
		bottle.abort(503, "User not logged in")

	if "url" not in input:
		bottle.abort(400, "Required variable: URL")

	try:
		sendlink(thisuser.public, input["url"])
		return ['Sent']
	except:
		bottle.abort(503, "Could not wake user")

@app.post('/claim/:name')
def post_claim(name):
	thisuser = getuser(name)
	input = dict(bottle.request.forms)

	if thisuser.password != None:
		if 'password_old' not in input:
			bottle.abort(401, "Not authorized - account is password protected")
		elif not thisuser.check_password(input['password_old']):
			bottle.abort(401, "Not authorized - wrong password")

	if 'password' in input:
		thisuser.set_password(input['password'])

	usersChanged.set()

	return ["Set successfully"]

@app.post('/unclaim/:name')
def unclaim(name):
	if name in hosted:
		thisuser = hosted[name]
		input = dict(bottle.request.forms)

		if thisuser.password != None:
			if not thisuser.check_password(input['password']):
				bottle.abort(401, "Not authorized - wrong password")

		del hosted[name]

		usersChanged.set()
		return ["Successfully unhosted the user"]
	else:
		bottle.abort(404, "User not stored")

@app.post('/unhost/:name')
def unhost(name):
	if name in hosted:
		thisuser = hosted[name]
		input = dict(bottle.request.forms)

		if thisuser.password != None:
			if not thisuser.check_password(input['password']):
				bottle.abort(401, "Not authorized - wrong password")

		if thisuser.claimed:
			thisuser.public  = ""
			thisuser.private = ""
		else:
			del hosted[name]

		usersChanged.set()
		return ["Successfully unhosted the user"]
	else:
		bottle.abort(404, "User not stored")

@app.route('/wizard/_/:action')
def wizard_redirect(action):
	return [
		"<html><head><title>Rex %s Wizard redirect</title></head><body>" % action,
		'Name: <input type="text" id="name"/><br/>',
		'<input type="button", value="Go!" onclick="window.location = \'/wizard/\'+document.getElementById(\'name\').value+\'/%s\'">' % action,
		"</body></html>"
	]	

@app.route('/wizard/:name/set')
def wizard_set(name):
	return [
		"<html><head><title>Rex Form Wizard: Host an IP</title></head><body>",
		'<form action="/ip/%s" method="post">' % name,
		'Public IP: <input type="text" name="public_ip" /><br/>',
		'Private IP: <input type="text" name="private_ip" /><br/>',
		'Password (if set): <input type="text" name="password" /><br/>',
		'<input type="submit" />',
		"</form></body></html>"
	]

@app.route('/wizard/:name/wake')
def wizard_wake(name):
	return [
		"<html><head><title>Rex Form Wizard: Connect to a Peer</title></head><body>",
		'<form action="/wake/%s" method="post">' % name,
		'URL: <input type="text" name="url" /><br/>',
		'<input type="submit" />',
		"</form></body></html>"
	]

@app.route('/wizard/:name/claim')
def wizard_claim(name):
	return [
		"<html><head><title>Rex Form Wizard: Claim an address</title></head><body>",
		'<form action="/claim/%s" method="post">' % name,
		'Password: <input type="text" name="password" /><br/>',
		'Old Password (if set): <input type="text" name="password_old" /><br/>',
		'<input type="submit" />',
		"</form></body></html>"
	]

@app.route('/wizard/:name/unclaim')
def wizard_unclaim(name):
	return [
		"<html><head><title>Rex Form Wizard: Destroy your account</title></head><body>",
		'<form action="/unclaim/%s" method="post">' % name,
		'Password (if set): <input type="text" name="password" /><br/>',
		'<input type="submit" />',
		"</form></body></html>"
	]

@app.route('/wizard/:name/unhost')
def wizard_unhost(name):
	return [
		"<html><head><title>Rex Form Wizard: Log Off</title></head><body>",
		'<form action="/unhost/%s" method="post">' % name,
		'Password (if set): <input type="text" name="password" /><br/>',
		'<input type="submit" />',
		"</form></body></html>"
	]

@app.route('/')
@app.route('/index')
@app.route('/index.htm')
def root():
	return bottle.static_file("root.html", "./static_html/")

@app.route('/wizard')
@app.route('/wizard/')
def wizard_root():
	return bottle.static_file("wizard.html", "./static_html/")

@app.route("/favicon.ico")
def favicon():
	return bottle.static_file("logo.ico", "./img/")

@app.route("/img/:name")
def favicon(name):
	return bottle.static_file(name, "./img/")

def start(port=8000, dropper=None):
	if dropper!=None:
		@app.hook('before_request')
		def wait_drop():
			dropper.wait()
	return gevent.spawn(bottle.run, app, server="gevent", host="0.0.0.0", port = port)

def saver():
	import time
	while True:
		time.sleep(5) # Rate limit
		usersChanged.wait()
		usersChanged.clear()
		print "Backing up users (%d)..." % len(hosted)
		user.save_udictf("users.save", hosted)
		print "Done"
