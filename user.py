import expiration
import random
import base64
import pickle

from Crypto.PublicKey import RSA
from hashlib import sha1

randomizer = random.SystemRandom()
CHALLENGE_TIME        = expiration.timedelta(minutes=2)
UNCLAIMED_EXPIRE_TIME = expiration.timedelta(hours=1)
CLAIMED_EXPIRE_TIME   = expiration.timedelta(days=365)

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

def make_hash(str):
	return sha1(str).digest()

class User(object):
	def __init__(self, argname, **kwargs):
		self.name = argname # if we used "name", we'd just collide with the kwarg name.
		self.password = None
		self.public = ""
		self.private = ""
		self.sig = ""
		self.key = None
		self._challenge = None
		self.expires = expiration.Expiration(UNCLAIMED_EXPIRE_TIME)

		self.set_from(kwargs)

	@property
	def signed(self):
		return self.sig != ""

	def set_from(self, d):
		for i in d:
			self[i] = d[i]

	def __iter__(self):
		''' For dict conversion '''
		return self.keys().__iter__()

	def keys(self):
		''' For dict conversion '''
		return ['name',
			'password',
			'ips',
			'key',
			'challenge']

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
		if i == "expires":
			return self.expires
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

	def __setitem__(self, i, v):
		if i == "name":
			self.name = v
		elif i == "password":
			self.password = v
		elif i == "ips":
			self.public  = v['public']
			self.private = v['private']
			self.sog     = v['sig']
		elif i == "key":
			self.set_key(v)
		elif i == "challenge":
			if v == None:
				self._challenge = None
			else:
				self._challenge = (v['source'], v['encrypted'], v['expires'])
		else:
			raise KeyError(i)

	def set_password(self, pwd):
		self.password = make_hash(pwd)

	def check_password(self, pwd):
		return self.password == make_hash(pwd)

	def set_key(self, keystr):
		if keystr == None:
			self.key = None
		else:
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
	def expired(self):
		return self.expires.expired

	@property
	def challenge(self):
		if self.has_challenge():
			return self._challenge
		else:
			# Create challenge
			if self.key != None:
				source = randstring()
				encrypted = encryptstring(source, self.key)
				expires = Expiration(CHALLENGE_TIME)

				self._challenge = (source, encrypted, expires)

				return self.challenge
			else:
				# No key, no challenge
				return None

def serialize(users):
	''' Accepts a list of Users, returns serialized list '''
	return pickle.dumps([dict(u) for u in users])

def unserialize(str):
	''' Accepts serialized list, returns list of Users '''
	users = pickle.loads(str)
	#print users
	return [makeuser(d) for d in users]

def makeuser(d):
	''' Converts a dict into a User '''
	return User(d['name'], **d)

def save(ulist, filename):
	with open(filename, 'w') as f:
		f.write(serialize(ulist))

def load(filename):
	with open(filename, 'r') as f:
		return unserialize(f.read())

def udict(ulist):
	# Converts list into dict
	result = {}
	for i in ulist:
		result[i.name] = i
	return result

def udictf(filename):
	return udict(load(filename))

def save_udictf(filename, d):
	return save(d.values(), filename)

def clean_dict(d):
	''' Remove expired users '''
	keys = d.keys()
	for i in keys:
		if d[i].expired:
			del d[i]
	return d
