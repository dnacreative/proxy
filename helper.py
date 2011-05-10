from pdb import set_trace as pdb_set_trace
import socket

DEBUG = False 
#def set_trace():
	#if DEBUG: pdb_set_trace ()
def dbg ( txt ):
	print txt

BUFFER = 200

def _create_socket():
	return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connected_socket(host, port):
	sock = _create_socket ()
	sock.connect ( (host, port) )
	return sock

def trim(string):
	return string.replace(" ", "");

max_uid = 0
def get_uid():
	global max_uid
	max_uid += 1
	return max_uid

create_socket = _create_socket
