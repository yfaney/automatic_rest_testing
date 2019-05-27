import http.client
import json
import requests
from urllib.parse import urlencode
from requests_oauthlib import OAuth1
from http_util import my_httpreq, my_httpsreq

def req_oauth(host, port, url_oauth, url_req, concept, username, password, method=None, data=None):
    # type: (str, int, str, str, str, str, str, str, str) -> Response
    req_hdr = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    body = urlencode({"concept": concept, "username": username, "password": password})
    res = my_httpreq(host, port, req_hdr, "POST", url_oauth, body=body)
    res = res.read()
    res = json.loads(res)
    auth = OAuth1(res["consumerKey"], res["consumerSecret"], res["token"], res["tokenSecret"])
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