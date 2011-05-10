from pdb import set_trace 
LOCAL_DEBUG = False
class Mapping (object):
	def __init__(self):
		pass
	
	def get_new_location(self, method, uri, port):
		if LOCAL_DEBUG:
			print 'uri: %s' % uri
		if uri.replace('/','') == 'ajax_url' or uri.replace('/', '').startswith('ajax_url'):
			return method, 'localhost', uri, 10500
		return method, 'localhost', None, 8000

	def get_mapped_message(self, msg):
		''' returns message containing mapped headers, changes given message!! '''
		method, host, uri, port = self.get_new_location (msg.method, msg.uri, msg.port)
		if port: msg.update_port (port)
		if uri: msg.update_uri (uri)
		if host: msg.update_host (host)
		if method: msg.update_method (method)
		return msg


