import datetime
import random
import base64
import pickle

from Crypto.PublicKey import RSA


randomizer = random.SystemRandom()
CHALLENGE_TIME = datetime.timedelta(minutes=2)


def randstring():
	return base64.encodestring(
		str(randomizer.getrandbits(128))
	)

def encryptstring(s, key):
	# Assumes K-less RSA algorithm
	return base64.encodestring(
		key.encrypt(s, "")[0]
	)

def now():
	return datetime.datetime.now()

class User(object):
	def __init__(self, name, **kwargs):
		self.name = name
		self.password = None
		self.public = ""
		self.private = ""
		self.sig = ""
		self.key = None
		self._challenge = None

		self.set_from(kwargs)

	@property
	def signed(self):
		return self.sig != ""

	def set_from(self, d):
		for i in d:
			self[i] = d[i]

	def serialize(self):
		return pickle.dumps(dict(self))

	def unserialize(self, str):
		self.set_from(pickle.loads(str))

	def __iter__(self):
		''' For dict conversion '''
		return ['name',
			'password',
			'ips',
			'key',
			'challenge'].__iter__()

	def __getitem__(self, i):
		if i == "name":
			return self.name
		if i == "password":
			return self.password
		if i == "ips":
			return {
				"public": self.public,
				"private": self.private,
				"sig": self.sig
			}
		if i == "key":
			return self.get_key()
		if i == "challenge":
			c = self.challenge
			if c == None:
				return None
			else:
				return {
					"source": c[0],
					"encrypted": c[1],
					"expires": c[2]
				}
		raise KeyError(i)

	def set_key(self, keystr):
		self.key = RSA.importKey(keystr)

	def get_key(self):
		if self.key == None:
			return None
		else:
			return self.key.publicKey().exportKey()

	def has_challenge(self):
		if self._challenge == None or now() > self._challenge[2]:
			return False
		else:
			return True

	@property
	def challenge(self):
		if self.has_challenge():
			return self._challenge
		else:
			# Create challenge
			if self.key != None:
				source = randstring()
				encrypted = encryptstring(source, self.key)
				expires = now() + CHALLENGE_TIME

				self._challenge = (source, encrypted, expires)

				return self.challenge
			else:
				# No key, no challenge
				return None

def serialize(users):
	''' Accepts a list of Users, returns serialized list '''
	return pickle.dumps([u.serialize() for u in users])

def unserialize(str):
	''' Accepts serialized list, returns list of Users '''
	users = pickle.loads(str)
	return [makeuser(d) for d in users]

def makeuser(d):
	''' Converts a dict into a User '''
	return User(d['name'], d)
