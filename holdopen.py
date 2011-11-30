''' 

The HoldOpen part of Rex tells you your public IP address and maintains its validity.

'''

from gevent import spawn

import socket
import time

def server(host='0.0.0.0', port=7653):
	srv = socket.socket()
	addr = ('0.0.0.0', port)
	srv.bind(addr)
	srv.listen(500)
	while 1:
		print "Hosting on", addr
		conn, newaddr = srv.accept()
		print "New connection: ", repr(newaddr)
		spawn(handler, conn, newaddr)

def handler(sock, addr):
	sock.sendall("%s:%d\r\n" % addr)
	while 1:
		# Test for socket failure
		try:
			# do nothing with this, raises exception if closed
			sock.sendall("k\r\n")
		except socket.error:
			break
		time.sleep(1)

	sock.close()
	print "Connection ", addr, "terminated."
