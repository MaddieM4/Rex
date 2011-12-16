''' 

The HoldOpen part of Rex tells you your public IP address and maintains its validity.

'''

from gevent import spawn

import socket
import time

sends = {}

def sendlink(ip, url):
	sends[ip].append(url)

def server(host='0.0.0.0', port=7653, dropper=None):
	srv = socket.socket()
	addr = ('0.0.0.0', port)
	srv.bind(addr)
	if dropper != None:
		dropper.wait()
	srv.listen(500)
	while 1:
		print "Hosting holdopen on", addr
		conn, newaddr = srv.accept()
		print "New connection: ", repr(newaddr)
		spawn(handler, conn, newaddr)

def handler(sock, addr):
	ip = "%s:%d" % addr
	sock.sendall("%s\r\n" % ip)
	sends[ip] = []
	while 1:
		# Test for socket failure
		try:
			# do nothing with this, raises exception if closed
			sock.sendall("\x00" + "\r\n".join(sends[ip]))
			sends[ip] = []
		except socket.error:
			break
		time.sleep(1)

	sock.close()
	print "Connection ", addr, "terminated."
