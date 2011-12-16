import gevent
from gevent import monkey; monkey.patch_all()

import holdopen
import wsgi
import dropprivelege

# Link this for waking
wsgi.sendlink = holdopen.sendlink

if __name__ == "__main__":
	droppy = dropprivelege.Dropper(uid_name="philip")

	ho = gevent.spawn(holdopen.server, dropper=droppy.event)
	wizzy = wsgi.start(80, dropper=droppy.event)
	saver = gevent.spawn(wsgi.saver)

	droppy_greenlet = droppy.start()
	try:
		gevent.joinall([ho, wizzy, saver, droppy_greenlet])
	except KeyboardInterrupt:
		print "Shutting down servers."
