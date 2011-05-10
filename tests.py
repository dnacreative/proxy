import unittest
from pdb import set_trace 
from messages import HttpRequest

class TestMessages (unittest.TestCase):
	msg = 'GET /index.html HTTP/1.1\r\nHost: localhost:2000\r\nUser-Agent: Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Language: en-gb,en;q=0.5\r\nAccept-Encoding: gzip,deflate\r\nAccept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7\r\nKeep-Alive: 115\r\nConnection: keep-alive\r\nCookie: csrftoken=1ae9e2f30940541a6980f3084c1170bf; sessionid=5e75ecc97822f8f6d4c8fa1f33bcb031; djdt=hide\r\n\r\n'

	
	def setUp(self):
		self.request = HttpRequest (self.msg)
		self.request.build ()

	def test_init(self):
		self.request = HttpRequest (self.msg)
		self.assertRaises(Exception, self.request.get_header, 'accept')

	def test_headers(self):
		self.request.build ()
		req = self.request
		for name in ('host', 'Host', 'HOST', 'hOsT'):
			self.assertEquals('localhost:2000', req.get_header(name))

		self.assertEquals('localhost', req.get_host ())
		self.assertEquals(2000, req.get_port ())

	def test_add_header (self):
		req = self.request
		req.add_header('test_header1', 'some value  ')
		self.assertEquals('some value', req.get_header('test_header1'))

	def test_update_port (self):
		req = self.request
		req.update_port(12345)
		self.assertEquals(12345, req.get_port () )
		self.assertEquals('localhost:12345', req.get_header ('host') )

	def test_update_host (self):
		req = self.request
		req.update_host('newhost')
		self.assertEquals('newhost', req.get_host () )
		self.assertEquals('newhost:2000', req.get_header ('host') )

		req.update_host('some_new_host123_cba')
		self.assertEquals( 'some_new_host123_cba', req.get_host () ) 
		self.assertEquals( 'some_new_host123_cba:2000', req.get_header ('Host') ) 
	
	def test_get_text_repr (self):
		req = self.request
		req.update_host('newhost')
		req.update_port(123456)
		if 'newhost:123456' not in req.text_repr(): raise Exception()

if __name__ == "__main__":
	unittest.main ()
