''' 

Class for dropping root priveleges on a delay, allowing other psuedothreads
to block until the drop after having a chance to get their root duties done.

'''

import os, pwd, grp
from gevent import event, spawn_later

def uidname(uid):
	return pwd.getpwuid(uid).pw_name

def gidname(gid):
	return grp.getgrgid(gid)[0]

def uid(name):
	return pwd.getpwnam(name)[2]

def gid(name):
	return grp.getgrnam(name)[2]

class Dropper(object):

	def __init__(self, delay=1, uid_name='nobody', gid_name='nogroup'):
		self.start_uid = os.getuid()
		self.start_gid = os.getgid()

		self.delay = float(delay)
		self.target_uid = uid(uid_name)
		self.target_gid = gid(gid_name)
		self.event = event.Event()

	def start(self):
		return spawn_later(self.delay, self.run)

	def run(self):
		''' Do not call directly, use start() '''
		if self.start_uid == 0:
			print "Dropping to %s and %s" % (uidname(self.target_uid), gidname(self.target_gid))
			try:
				os.setgid(self.target_gid)
			except OSError, e:
				print "Could not set effective group id: %s" % e
			try:
				os.setuid(self.target_uid)
			except OSError, e:
				print "Could not set effective user id: %s" % e
		self.event.set()
