import base64
import json
import requests
import random
import time
import hmac
from datetime import datetime, timedelta
from hashlib import sha1
from urllib.parse import urlencode, quote_plus
from requests_oauthlib import OAuth1
from http_util import my_httpreq, my_httpsreq

def cache_session(domain, username, session):
  with open('oauth_session_%s_%s.json' % (domain, username), 'w') as outfile:
    json.dump(session, outfile)


def load_session_from_cache(domain, username):
  try:
      fh = open('oauth_session_%s_%s.json' % (domain, username), 'r')
      with fh as cache_session_file:
        return json.load(cache_session_file)
  except FileNotFoundError:
      return None


def req_session(host, port, url_session, username, password, use_http = False, **kwargs):
  # type: (str, int, str, str, str, dict) -> Object
  req_hdr = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
  body = urlencode(
    {
      "username": username,
      "password": password,
      "login_method": "PASSWORD"
    }
  )
  res = my_httpreq(host, port, req_hdr, "POST", url_session, body=body) if use_http else my_httpsreq(host, port, req_hdr, "POST", url_session, body=body)
  res = res.read()
  res = json.loads(res)
  return res


def req_token(host, port, identityStatement, clientMnemonic, authority, **kwargs):
  # type: (str, int, str, dict) -> Object
  url_token = ("/oauth/%s/%s/tokens" % (clientMnemonic, authority))
  url = "https://%s%s" % (host, url_token)
  req_hdr = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
  timestamp = int(time.time())
  nonce = random.randint(0, 100000000)
  oauth_params = {
    "oauth_consumer_key": kwargs["consumer_key"],
    "oauth_consumer_secret": kwargs["consumer_secret"],
    "oauth_nonce": nonce,
    "oauth_signature_method": "HMAC-SHA1",
    "oauth_timestamp": timestamp,
    "oauth_version": "1.0",
    "x_auth_assertion": identityStatement
  }
  parameters = urlencode(oauth_params)
  # Prepare the signature base string using REST method encoded url and the encoded parameters list
  signatureBaseString = "POST&" + quote_plus(url) + "&" + quote_plus(parameters)
  signingKey = quote_plus(kwargs["consumer_secret"]) + "&"
  # Create the encoded signature using HMAC-SHA1 and then base 64
  oauthSignature = hmac.new(signingKey.encode('utf-8'), signatureBaseString.encode('utf-8'), sha1)
  oauthSignature64 = base64.b64encode(oauthSignature.digest())

  oauth_params["oauth_signature"] = oauthSignature64

  body = urlencode(oauth_params)
  res = my_httpsreq(host, port, req_hdr, "POST", url_token, body=body)
  res = res.read()
  res = json.loads(res)
  return res


def req_oauth(url_req, username, password, method=None, data=None, **kwargs):
  # type: (str, int, str, str, str, str, str, dict) -> Response
  req_hdr = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
  session = req_session(kwargs["host_session"], kwargs["port_session"], kwargs["url_session"], username, password)["session"]
  token = req_token(kwargs["host_token"], kwargs["port_token"], session["identityStatement"], session["clientMnemonic"], session["authority"], **kwargs)
  token = token["response"]["oauth_parameter"]
  auth = OAuth1(kwargs["consumer_key"], kwargs["consumer_secret"], token["oauth_token"], token["oauth_token_secret"])
  req_hdr = {"Accept": "application/json", "Content-Type": "application/json"}
  if data is not None and method is None:
    method = "POST"
  elif data is None and method is None:
    method = "GET"
  if method == "GET":
    return requests.get(url_req, auth=auth, headers=req_hdr)
  elif method == "POST":
    return requests.post(url_req, json=data, auth=auth, headers=req_hdr)
  elif method == "PUT":
    return requests.put(url_req, json=data, auth=auth, headers=req_hdr)
  elif method == "DELETE":
    return requests.delete(url_req, json=data, auth=auth, headers=req_hdr)
  else:
    raise RuntimeError("Unsupported HTTP request method.")


class CernerOAuthUtil:
  def __init__(self, host, port, url_session, username, password, use_http, consumer_key, consumer_secret, domain):
    self.host = host
    self.port = port
    self.username = username
    self.password = password
    self.url_session = url_session
    self.use_http = use_http
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.domain = domain
    self.session = None
    self.token = None
    self.token_expires = None
    self.session_expires = None
    self.get_session()
    self.get_token()

  def get_session(self):
    self.session = load_session_from_cache(self.domain, self.username)
    if self.session is None:
        self.session = req_session(self.host, self.port, self.url_session, self.username, self.password, self.use_http, domain=self.domain)["session"]
        cache_session(self.domain, self.username, self.session)
    else:
      print("Session cache hit: %s" % self.session)

  def get_token(self):
    self.token = req_token(self.host, self.port, self.session["identityStatement"], self.session["clientMnemonic"], self.session["authority"],
      consumer_key=self.consumer_key, consumer_secret=self.consumer_secret)['response']['oauth_parameter']
    self.session_expires = datetime.now() + timedelta(seconds=self.token['oauth_authorization_expires_in'])
    self.token_expires = datetime.now() + timedelta(seconds=self.token['oauth_expires_in'])

  def req_oauth(self, url_req, method=None, data=None, **kwargs):
    if self.session_expires is None or self.session_expires < datetime.now():
      self.get_session()
    if self.token_expires is None or self.token_expires < datetime.now():
      self.get_token()
    req_hdr = req_hdr = {"Accept": "application/json", "Content-Type": "application/json"}
    auth = OAuth1(self.consumer_key, self.consumer_secret, self.token["oauth_token"], self.token["oauth_token_secret"])
    if data is not None and method is None:
      method = "POST"
    elif data is None and method is None:
      method = "GET"
    if method == "GET":
      return requests.get(url_req, auth=auth, headers=req_hdr)
    elif method == "POST":
      return requests.post(url_req, json=data, auth=auth, headers=req_hdr)
    elif method == "PUT":
      return requests.put(url_req, json=data, auth=auth, headers=req_hdr)
    elif method == "DELETE":
      return requests.delete(url_req, json=data, auth=auth, headers=req_hdr)
    else:
      raise RuntimeError("Unsupported HTTP request method.")
