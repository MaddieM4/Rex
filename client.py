import urllib
import socket

import gevent
from gevent import monkey; monkey.patch_all()

def IP_tuple(text):
	split = text.split(":")
	return (split[0], int(split[1]))

def IP_text(tup):
	return "%s:%d" % tup

class Client(object):
	def __init__(self, server, hoport=7653, account = None):
		self._public = None
		self._buffer = ""
		self.peers = set()
		self.closed = False
		self.account = account or Account(server)

		self.hosocket = socket.create_connection((server, hoport))
		self.hosocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.server = socket.socket()
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind(self.private)

	def run(self):
		self.host()
		self.greenlets = [
			gevent.spawn(self.accept_loop),
			gevent.spawn(self.accept_wakes)
		]

	def join(self):
		gevent.joinall(self.greenlets)

	def host(self):
		# Make yourself publicly available
		print "Posting IP data to site got HTTP code ", self.account.host(self.public, self.private).getcode()

	def accept_loop(self):
		self.server.listen(5)
		while not self.closed:
			self.__on_connect(self.server.accept()[0])

	def accept_wakes(self):
		while not self.closed:
			self.read()
			if self._public:
				for frame in self._buffer.split('\x00')[:-1]:
					for url in frame.split("\r\n"):
						self.connect_peer(url)

	def connect_peer(self, url):
		if url == "":
			return
		# Wake peer (get it to try to connect to you)
		self.account.wake(url)

		self.__on_connect(self.connect(url))

	def connect(self, url):
		# Connect to a peer
		try:
			pair = urllib.urlopen(url).read()
			pub, priv = pair.split("\n")[:2]
		except Exception as e:
			print e
			# Could not get IP pair from URL
			raise IndexError("Could not get IP pair from page")

		return self.connect_ips(pub, priv)

	def connect_ips(self, *args):
		# Connect to one or more IP addresses, returning first successful socket
		for ip in args:
			addr = IP_tuple(ip)
			try:
				conn = socket.create_connection(addr)
				return conn
			except:
				print "Connection to %s failed" % repr(addr)
		raise IOError("No connections worked")

	def read(self):
		self._buffer += self.hosocket.recv(1024)

	def close(self):
		self.closed = True

	def on_connect(self, sock, url):
		pass

	def on_disconnect(self, sock):
		pass

	def __on_connect(self, sock):
		# Rex handshake
		path = self.url+"\r\n"
		sock.sendall(path)

		remotestart = ""
		while not "\r\n" in remotestart:
			remote += sock.recv(1)
		
		self.on_connect(self, sock, remotestart)
		if connected(sock):
			self.peers.add(sock)
			print self.peers

	def __on_disconnect(self, sock):
		self.peers.remove(sock)
		print self.peers
		self.on_disconnect(self, sock)

	def disconnect(sock):
		self.__on_disconnect(sock)

	@property
	def public(self):
		if not self._public:
			while not "\r\n" in self._buffer:
				self.read()
			split = self._buffer.split("\r\n")
			self._public = IP_tuple(split[0])
			self._buffer = "\r\n".join(split[1:])
		return self._public

	@property
	def private(self):
		return self.hosocket.getsockname()

	@property
	def url(self):
		return self.account.url

	@property
	def username(self):
		return self.account.username

	@property
	def password(self):
		return self.account.password

	@username.setter
	def username(self, value):
		self.account.username = value

	@password.setter
	def password(self, value):
		self.account.password = value

class Account(object):
	def __init__(self, server, username=None, password=None):
		self.server = server
		self.username = username
		self.password = password

	def host(self, public, private):
		if not self.username:
			raise AttributeError("Username not set")

		args = {
			"public_ip": IP_text(public),
			"private_ip":IP_text(private)
		}
		if self.password:
			args['password'] = self.password

		return self.post("/ip/"+self.username, args)

	def wake(self, theirurl):
		if not self.username:
			raise AttributeError("Username not set")

		# Compute wake URL
		slices = theirurl.split('/')
		slices[-2] = "wake"
		wakeurl = "/".join(slices)
		args = {
			"url": self.url,
		}
		print repr(wakeurl)
		print repr(args)

		return self.post(wakeurl, args)

	def claim(self, newpassword=""):
		if not self.username:
			raise AttributeError("Username not set")

		args = {
			"password": newpassword,
		}
		if self.password:
			args['password_old'] = self.password

		result = self.post("/ip/"+self.username, args)
		if result.getcode() == 200:
			self.password = newpassword
		return result

	def unclaim(self):
		if not self.username:
			raise AttributeError("Username not set")
		args = {}
		if self.password:
			args['password'] = self.password
		return self.post("/unclaim/"+self.username, args)

	def unhost(self):
		if not self.username:
			raise AttributeError("Username not set")
		args = {}
		if self.password:
			args['password'] = self.password
		return self.post("/unhost/"+self.username, args)

	def post(self, path, args={}):
		params = urllib.urlencode(args)
		if not "://" in path:
			path = self.path(path)
		return urllib.urlopen(path, params)

	def get(self, path):
		return urllib.urlopen(self.path(path))

	def path(self, the_path):
		return "http://" + self.server + the_path

	@property
	def url(self):
		return self.path("/ip/"+self.username)

def connected(sock):
	with gevent.Timeout(0, False):
		try:
			sock.recv(0)
		except:
			return False
	return True

