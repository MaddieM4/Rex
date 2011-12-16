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
	def __init__(self, server, hoport=7653):
		self._public = None
		self._buffer = ""
		self.peers = set()
		self.closed = False
		self.account = Account(server)

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

	def listen(self):
		# Accept connections on self.server
		print "Listening..."
		self.server.listen(5)

	def accept_loop(self):
		while True:
			self.listen()
			self.peers.add(self.server.accept())
			print self.peers

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
		self.peers.add(self.connect(url))
		print self.peers

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

		return self.post("/ip/"+self.username, **args)

	def post(self, path, **kwargs):
		params = urllib.urlencode(kwargs)
		path = self.path(path)
		return urllib.urlopen(path, params)

	def get(self, path):
		return urllib.urlopen(self.path(path))

	def path(self, the_path):
		return "http://" + self.server + the_path
