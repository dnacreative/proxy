#log13-16146
# solution to proxy ajax calls: 
# each time it gets readable socket as uid, it generates new sending request
# failure use case:
# read request on ajax call on socket 143, create socket 144 for sending to destination READ_1
# send request to destination on 144 WRITE_1
# on 143 there's no data so server thinks - ok end of message - write second message to dest2 - create for that socket 145 READ_2
# read all data incoming from 144 READ_2 - but won't send it to client since new dest_uid is 145 !
# send all data read from 144 to client - force closing socket 144 and deleting processor - but it wont be deleted since processors[145] would point for that processor WRITE_2
# write 


# also take in mind that when server is single threaded and not async (!) then if request from client wont be parsed well
# and would be sent incomplete request so that destination server would be waiting for complete request, 
# other request sent to server will queue and wait for that incomplete request to be completely sent

# probably should change some response to client header to work with twisted and ajax
import socket
import select
import sys
import traceback
import os
from pdb import set_trace

from builders import *
from helper import *
from mapping import *
import logging
from compressing import compress_string

log = logging.getLogger('main')
file_handler = logging.FileHandler('log/main')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(messages)s')
file_handler.setFormatter(formatter)
log.addHandler(file_handler)

LOCAL_DEBUG = False

class FileServer (object):
	def __init__(self, uid, server, path = os.getcwd ()):
		self._uid = uid
		self._server = server
		self._request_complete = False
		self.request_builder = HTTPRequestBuilder ()
		self._path = os.path.dirname (os.path.realpath (__file__))
		self._path = os.path.join (self._path, 'files')

	def get_content (self, uri):
		cnt, fpath = '', uri

		if fpath.startswith('/'): fpath = fpath[1:]
		fpath = os.path.join(self._path, fpath) #fpath - path of resource


		if uri[-1] == '/': uri = uri[:len(uri) - 2]# remove last '/' from uri
	
        # TODO: check permissions for fpath
		if os.path.isdir(fpath):
			if uri:
				puri = uri
				for i in range(len(uri)):
					if uri[len(uri) - i-1] == '/':
						puri = uri[:len(uri)-i-1] #cut last / and waht's after it
						break

				if puri and puri[0] != '/': #add / at the beginning
					puri = '/' + puri
				if not puri: puri = '/'
				cnt += r'<a href="%s">...</a><br>' % puri

			for name in os.listdir(fpath):
				add = '<a href="%s/%s">%s</a><br/>' % (uri, name.replace('/',''), name)
				cnt += add
		else:
			try:
				f = open( fpath, 'r' )
				cnt = ''.join([x for x in f])
				f.close ()
			except:
				return 'ERROR'
		return cnt


	def _feed_request(self, data):
		self.request_builder.feed (data)
		if not data or self.request_builder.end_message():
			if self._request_complete: return
			from messages import StaticResponse
			self._request_complete = True

			self.request_builder.build_message ()
			msg = self.request_builder.get_message ()
			
			cnt = self.get_content (msg.uri)
			log.debug ('contetn: %s' % cnt)

			ret = StaticResponse (cnt)

			acc, gzip = msg.get_header ('Accept-Encoding'), None
			if acc:
				gzip = 'gzip' in acc.split(',')
	
			if gzip:
				ret.add_header ('content-encoding', 'gzip')
				cnt = compress_string (cnt)
	
			ret.plain = cnt
			self._server.send_data_on_id (ret.text_repr (), self._uid)


	def data_received(self, socket_id, data):
		''' called when some data is received
		socket_id - id of socket on which data was received
		data - received data '''

		if socket_id == self._uid: # received data from client
			self._feed_request (data)


	def data_send(self, socket_id):
		''' called when data on given socket_id was sent '''
		if socket_id == self._uid:
			self._server.destroy(self._uid)


class AsyncMapper (object):

	def __init__(self, uid, server):
		''' uid - id of socket that client connected to the server with
		server - server instance '''

		self.uid = uid
		self._server = server
		self.request_builder = HTTPRequestBuilder ()
		self.response_bulider = HttpResponseBuilder()
		self.dest_uid = None
	
		self.method = None
	def map_request(self, msg):
		''' returns mapped version of request
		msg - HttpRequest instance '''
		mapper = Mapping ()
		return mapper.get_mapped_message(msg)

	def map_response(self, msg):
		''' returns mapped version of response got from destination server '''
		return msg

	def _feed_client_msg(self, data):
		''' responsible for building client's requests
		when request is received, makes message to destination and calls server to send that message to destination '''
		if LOCAL_DEBUG:
			log.debug( 'feed_client_msg: self.uid: %s\t self.dest_uid: %s\tdata: %s' % (self.uid, self.dest_uid, data))

		self.request_builder.feed (data)
		if not data or self.request_builder.end_message():
			if self.dest_uid: return # don't process if dest_uid is created since it means that data was received
			# TODO: indicate at server level not to read from self.uid socket when all request is once received

			# build message from client
			self.request_builder.build_message ()
			msg = self.request_builder.get_message ()
			
			# map message
			msg = self.map_request (msg)
	
			# request sending message to destination
			self.dest_uid = self._server.send_data(msg.text_repr(), (msg.get_host(), msg.get_port()), self)
			if LOCAL_DEBUG:
				print 'received request from client (plain form): %s' % msg.plain
				print 'self assigned self.dest_uid: %s' % self.dest_uid


	def _feed_destination_msg(self, data):
		''' responsible for building response from destination
		when response is all send, lets server to send response to client '''

		print 'feed destination msg: self.uid: %s\tself.dest_uid: %s' % ( self.uid, self.dest_uid)
		if LOCAL_DEBUG:
			print 'feed destination msg: self.uid: %s\tself.dest_uid: %s\tdata: %s' % ( self.uid, self.dest_uid,data)
			print 'len(data): %s' % len(data)
		self.response_bulider.feed (data)
		if not data or len(data) == 0 or self.response_bulider.end_message (): 
		#check here also if data from destination was all received 
		# TODO: check if end of message, because when not check that, and all message is received,
		# on sockets[self.dest_uid] there will be no more in readable since all data was sent and it will never get here
		# remember method also
#		if self.response_bulider.end_message ():
			self.response_bulider.build_message ()
			msg = self.response_bulider.get_message()

			if LOCAL_DEBUG:
				print 'got response from destination(plainform): %s' % msg.plain


			msg = self.map_response (msg)
			self._server.send_data_on_id(msg.text_repr(), self.uid)
			

	def data_received(self, socket_id, data):
		''' called when some data is received
		socket_id - id of socket on which data was received
		data - received data 
		
		if received data on client's socket - delegates processing data to _feed_client_msg, which builds client message 
		if received data on destination socket - delegates processing that data to _feed_destination_msg,
		which builds response from destination '''

		if socket_id == self.uid: # received data from client
			self._feed_client_msg (data)

		elif socket_id == self.dest_uid: # received data from destination socket
			# building response to client
			# writening response to client
			self._feed_destination_msg (data)

	def data_send(self, socket_id):
		''' called when data on given socket_id was sent '''
		if socket_id == self.dest_uid:
			pass

		elif socket_id == self.uid:
			# close connection - response to client was send
			for x in self.uid, self.dest_uid:
				self._server.destroy(x)
		
class AsyncServer (object):
	def __init__(self, hostname, port):
		self.hostname = hostname
		self.port = port

		self.sockets = {} # uid -> socket
		self.processors = {} # uid -> AsyncMapper

		self.buff_to_send = {} # uid -> data
		self.buff_to_read = {} # uid -> data
		self.map_sock_buff = {} # sock -> uid

		self.processors_to_destroy = []

	def initialize (self):
		self.listener = create_socket ()
		self.listener.bind((self.hostname, self.port))
		self.listener.listen(50)

	def send_data_on_id(self, data, uid):
		''' sends given data to socket with given uid '''
		self.buff_to_send [uid] = data

	def send_data(self, data, destination, processor):
		''' returns number of socket at which data is to be send, associates given socket '''
		uid = get_uid ()
		sock = connected_socket(destination[0], destination[1])
		self.associate_socket ( uid, sock, processor )
		self.buff_to_send[uid] = data
		return uid

	def associate_socket(self, uid, socket, processor):
		self.sockets[uid] = socket
		self.processors[uid] = processor

		self.buff_to_read[uid] = ''
		self.buff_to_send[uid] = ''
		self.map_sock_buff[socket] = uid

	def destroy_processors(self):
		tmp = self.processors_to_destroy
		while(len(tmp)):
			uid = tmp.pop ()
			del self.processors[uid]

	def destroy(self, uid):
		#set_trace ()
		del self.buff_to_read[uid]
		del self.buff_to_send[uid]
		sock = 	self.sockets[uid]
		sock.close ()
		del self.map_sock_buff[sock]
		del self.sockets[uid]

		self.processors_to_destroy.append(uid)
		
		
	def print_info (self):
		if LOCAL_DEBUG:
			for attr in ('buff_to_read', 'buff_to_send', 'map_sock_buff', 'processors', 'sockets'):
				print 'self.%s: %s' % (attr, getattr(self, attr))

	def _process_readable (self, r):
		for sock in r:
			try:
				if sock == self.listener: # new readable on listener - create new AsyncMapper to process given request
					
					client, info = self.listener.accept()
					uid = get_uid ()
#					processor = AsyncMapper (uid, self)
					processor = FileServer (uid, self)
					self.associate_socket (uid, client, processor)
					self.print_info ()
				else:

					# get uid of given socket
					try:
						uid = self.map_sock_buff [sock]
					except KeyError, ke:
						#print ke
#						traceback.print_exc ()
						if LOCAL_DEBUG:
							print 'socket for reading not found, probably removed on destroy'
					
					# read data to buffer
					self.buff_to_read[uid] += sock.recv(BUFFER)
					
#					print 'received: \n%s\non uid: %s\n' % (self.buff_to_read[uid], uid)
					# inform proper processor about data received
					processor = self.processors [uid]
					processor.data_received ( uid, self.buff_to_read[uid] )
					
					# clear read buffer
					self.buff_to_read[uid] = ''
			except:
				traceback.print_exc ()
				raise


	def _process_writeable (self, w):
		for sock in w:

			try: # try in case processor.data_send( uid) would execute removing sockets 
				# get uid of given socket
				try:
					uid = self.map_sock_buff [sock]
				except KeyError, ke:
					#print ke
#					traceback.print_exc ()
					if LOCAL_DEBUG:
						print 'socket not found, probably deleted by destroy, continuing'
					continue

				# get data to send
				data = self.buff_to_send [uid]
				
				#TODO: optimize, so that w always contain only sockets where there's some data to send
				# if there's noting to send on given socket - return 
				if not data: 
					continue

				# send data
				if LOCAL_DEBUG:
					print 'sending data: %s on uid: %s' % (data, uid)
				sent = sock.send(data)

				# remove sent data from buffer
				data = data[sent:]

				# update data to send
				self.buff_to_send[uid] = data
			
				# check if all data was sent
				if not data:
					# inform proper processor about sending all data
					processor = self.processors [uid]
					processor.data_send (uid)
			except:
				traceback.print_exc ()
				raise
		
	def _read_connections (self):
		readable = [self.listener,]
		writable, error = [], []
		error = []
		while 1:
			r, w, e = select.select(readable, writable, error)

			self._process_readable ( r )
			self._process_writeable (w)
			self.destroy_processors ()

			# make list of sockets to listen for
			readable = [self.listener,]
			readable.extend( self.sockets.values() )
			writable = list( self.sockets.values() )
		
				

	def run(self):
		self.initialize ()
		self._read_connections ()




def serve(hostname = 'localhost', port = 2000):
	try:
		AsyncServer(hostname, port).run()
	except:
		traceback.print_exc ()
		exit (0)


if __name__ == '__main__':
	mapper = AsyncMapper (1, 'dwa')
	if len(sys.argv) == 2:
		serve ( port = int(sys.argv[1]) )
	else:
		serve ()

