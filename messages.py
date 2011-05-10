from helper import trim
from pdb import set_trace
import re
DEFAULT_PORT = 80
class HttpMessage( object ):
	regex = {
		'host': re.compile('^(\w)*$'),
	}

	def __init__(self, plain = None):
		self.plain = plain

		self.uri = None
		self.method = None
		self.protocol = None
		self.port = None


	def _get_header(self, key):
		for header in self._ordered_headers:
			if header[0] == key:
				return header

	def get_header(self, key): #getting header
		''' returns header with given key '''
		return self._get_header(key.lower())[1]
		raise Exception("Header %s not found" % key )

	def set_header(self, key, value): #edit existing header
		n = -1
		key = key.lower ()
		found = False
		for header in self._ordered_headers:
			n += 1
			if header[0] == key:
				found = True
				break
		if not found: raise ("Header %s not found" % key )
		self._ordered_headers[n] = (key, value)

	def add_header(self, key, value):#adding header
		pair = (key.lower(), value) 
		pair = tuple ( map (lambda x: x.strip(), pair ) )
		self._ordered_headers.append (pair)

	def _build_headers(self, list):
		self._buffer = self.plain
		self._ordered_headers = []
		for pair in list[1:]:
			if not pair: break
			try:
				key, value = pair.split(':', 1)
			except:
				break # probably not sended header yet
			self.add_header(key, value)

	def get_plain(self):
		return self.plain


	def get_host(self):
		return trim(self.get_header('Host').split(':')[0])

	def get_port(self):
		return int(self.get_header('Host').split(':')[1])
	
	def update_port(self, newport):
		''' updates port header '''
		host = self.get_header('Host')
		new_host = "%s:%s" % ( host.split(':')[0], newport )
		self.set_header('Host', new_host)

	def update_method(self, newmethod):
		self.method = newmethod
		
	def update_uri(self, newuri):
		self.uri = newuri
	
	def update_host(self, newhost):
		if not self.regex['host'].match(newhost): raise Exception("%s didn't match %s" % (newhost, self.regex['host']))
		host = self.get_header('Host')
		new_host = "%s:%s" % (newhost, host.split(':')[1])
		self.set_header('Host', new_host)

class HttpRequest( HttpMessage ):

	def build(self):
		''' builds message '''
		global DEFAULT_PORT
		list = self.plain.split('\r\n')
		self._build_headers (list)
		self.method, self.uri, self.protocol = list[0].split()
		try:
			self.port = self.get_port ()
		except:
			self.port = DEFAULT_PORT 

	def build_top(self):
		ret = ' '.join([self.method, self.uri, self.protocol])
		ret += '\r\n'
		return ret

	def build_headers (self):
		ret = ''
		for header in self._ordered_headers:
			ret += "%s: %s\r\n" % (header[0], header[1])
		ret = ret[:-2] # remove last \r\n
		return ret

	def text_repr(self):
		ret = self.build_top ()
		ret += self.build_headers ()
		ret += '\r\n\r\n'
		if self.method.upper() == 'POST':
			ret += self.plain.split('\r\n\r\n')[1]
		return ret

class HttpResponse( HttpMessage ):
	def __init__(self, plain):
		self.plain = plain

	def build():
		return

	def text_repr(self):
		return self.plain

	

# TODO: make uri as property - so that it would be returned without '/' at the end
class StaticResponse (HttpRequest):
	def __init__(self, *args, **kwargs):
		HttpRequest.__init__(self, *args, **kwargs)
		self._ordered_headers = []
	def text_repr(self):
		ret = 'HTTP/1.0 200 OK\r\n'
		ret += self.build_headers ()
		ret += '\r\n\r\n'
		ret += self.plain
		return ret


