import gevent
from gevent import monkey; monkey.patch_all()

import holdopen
import wsgi

if __name__ == "__main__":
	ho = gevent.spawn(holdopen.server)
	wizzy = wsgi.start(80)
	try:
		gevent.joinall([ho, wizzy])
	except KeyboardInterrupt:
		print "Shutting down servers."
