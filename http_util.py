import http.client
import logging
import ssl

def my_httpreq(host, port, headers, method, url, body=None):
  # type: (str, int, dict, str, str, str) -> HTTPResponse
  c = http.client.HTTPConnection(host, port)
  c.request(method=method, url=url, headers=headers, body=body)
  logging.debug("Got response: %s" % c.getresponse())
  return c.getresponse()

def my_httpsreq(host, port, headers, method, url, body=None):
  # type: (str, int, dict, str, str, str) -> HTTPSResponse
  c = http.client.HTTPSConnection(host, port, context=ssl._create_unverified_context())
  c.request(method=method, url=url, headers=headers, body=body)
  return c.getresponse()