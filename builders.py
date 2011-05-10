#The presence of a message-body in a request is signaled by the inclusion of a Content-Length or Transfer-Encoding header field in the request's message-headers. A message-body MUST NOT be included in a request if the specification of the request method (section 5.1.1) does not allow sending an entity-body in requests. A server SHOULD read and forward a message-body on any request; if the request method does not include defined semantics for an entity-body, then the message-body SHOULD be ignored when handling the request. 
from messages import HttpRequest, HttpResponse
from pdb import set_trace
LOCAL_DEBUG = False
class HTTPBuilder (object):
	def __init__(self):
		self._buffer = ''

	def feed(self, data):
		self._buffer += data
		#print 'httpbuilder_buffer: %s' % self._buffer

	def get_message (self):
		return self._msg

class HTTPRequestBuilder (HTTPBuilder):

	def _end_message_get(self):
		""" returns true if message ends with \r\n\r\n """
		if LOCAL_DEBUG:
			print '_end_message_get'
		return self._buffer[-4:] == '\r\n\r\n'

	def _end_message_post(self):
		if LOCAL_DEBUG:
			print '_end_message_post'
		if not hasattr(self, '_content_length'):
			try:
				self.build_message ()
				self._content_length = int( self._msg.get_header('content-Length') )
			except: #probably content_length not send yet - so it is not eom
				return False
		# \r\n\r\n separates headers and content, content-length specifies length of content only
		#set_trace ()
		return self._buffer[-(self._content_length + 4):-self._content_length] == '\r\n\r\n'
		
		

	def check_end (self, method):
		""" sets end message to proper method on the basis of message method """
		if method == 'GET':
			self.end_message = self._end_message_get # for speed
		elif method == 'POST':
			self.end_message = self._end_message_post 
		return self.end_message ()

	def end_message(self):
		try:
			self.build_message () # do sth like get_metohd_from _buffer, and then cache
			method = self._msg.method.upper ()
			self._method = method # save information about checking method name
			return self.check_end (self._method)
		except:
			return False

	def build_message (self):
		self._msg = HttpRequest( self._buffer )
		self._msg.build ()
	

class HttpResponseBuilder (HTTPBuilder):
	def build_message (self):
		self._msg = HttpResponse (self._buffer )
	
	def end_message (self):
		pattern = '\r\n\r\n'
		return self._buffer.count(pattern) == 2

