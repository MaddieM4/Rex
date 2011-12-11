from datetime import *

class Expiration(object):
	''' Hacky subclass of datetime.datetime '''

	def __init__(self, delta):
		self.dtobj = datetime(1970,1,1)
		self.delta = delta
		self.reset()

	def __getattr__(self, name):
		def reset():
			self.set(self.now() + self.delta)

		def set(other):
			self.dtobj = other

		def expired():
			return self.now() > self.dtobj

		if name =="reset":
			return reset
		elif name =="set":
			return set
		elif name =="expired":
			return expired()
		elif name in ("dtobj", "delta"):
			return object.__getattr__(self, name)
		else:
			return getattr(self.dtobj, name)
