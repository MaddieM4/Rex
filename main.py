import gevent
from gevent import monkey; monkey.patch_all()

import holdopen
import wsgi
import dropprivelege

if __name__ == "__main__":
	droppy = dropprivelege.Dropper()

	#print "droppy.event = ", repr(droppy.event)

	ho = gevent.spawn(holdopen.server, dropper=droppy.event)
	wizzy = wsgi.start(80, dropper=droppy.event)

	droppy_greenlet = droppy.start()
	try:
		gevent.joinall([ho, wizzy, droppy_greenlet])
	except KeyboardInterrupt:
		print "Shutting down servers."
