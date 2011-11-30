import gevent
from gevent import monkey; monkey.patch_all()

import bottle
from bottle import route

import time

@route('/')
def root():
	time.sleep(8)
	return ['Hello, world!']

@route('/generator')
def gen():
	yield "Hell"
	time.sleep(5)
	yield "o"
	time.sleep(5)
	yield ", world!"

def eternal():
	while True:
		time.sleep(5)
		print "Slept 5"

et = gevent.spawn(eternal)
http = gevent.spawn(bottle.run, host='0.0.0.0', port=8000, server='gevent')

try:
	gevent.joinall([et, http])
except KeyboardInterrupt:
	print "Shutting down all servers"
