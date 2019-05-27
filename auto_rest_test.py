#!/usr/local/bin/python

import http.client
import json
from http.client import HTTPResponse
from urllib.parse import urlencode, quote

import requests
import oauth_util_v2 as oauth_util
from prettytable import PrettyTable
from requests import Response
from requests_oauthlib import OAuth1

from utils.configmanager import ConfigManager
from utils.parsingmanager import parse_options
from utils.stringutil import cut_msg


"""
====================== Main ===========================
"""
if __name__ == "__main__":
    configFilePath, testFilePath, detail = parse_options()
    config = ConfigManager(configFilePath).parse()
    if configFilePath is None:
        print ("No config file is provided.")
        exit(-1)
    if testFilePath is None:
        print ("No test file is provided.")
        exit(-1)
    oauth_host = config["OAuth"]["Host"]
    oauth_port = int(str(config["OAuth"]["Port"]))
    oauth_url = config["OAuth"]["URL"]
    oauth_use_http = config["OAuth"]["UseHTTP"]
    oauth_concept = config["OAuth"]["Concept"]
    oauth_user = config["OAuth"]["UserName"]
    oauth_pw = config["OAuth"]["Password"]
    oauth_version = config["OAuth"]["Version"]
    oauth_consumer_key = config["OAuth"]["consumer_key"]
    oauth_consumer_secret = config["OAuth"]["consumer_secret"]
    domain = config["OAuth"]["domain"]
    client = oauth_util.CernerOAuthUtil(oauth_host, oauth_port, oauth_url, oauth_user, oauth_pw,
        use_http=oauth_use_http,
        consumer_key=oauth_consumer_key,
        consumer_secret=oauth_consumer_secret,
        domain=domain)
    summaries = []

    with open(testFilePath) as data_file:
        data = json.load(data_file)
        for testCase in data["TestCases"]:
            req_url = testCase["url"]
            req_method = testCase["method"] if "method" in testCase else "GET"
            if "data" in testCase:
                result = client.req_oauth(req_url, method=req_method, data=testCase["data"])
            else:
                result = client.req_oauth(req_url, method=req_method)
            print(("Running : %s" % testCase["name"]))
            if detail:
                print(("Status: %s" % (str(result.status_code))))
                try:
                    print((json.dumps(json.loads(result.text), sort_keys=True, indent=4)))
                except ValueError as e:
                    print ("Response is not a JSON format. Displaying the plain text...")
                    print((result.text))
                except Exception as e:
                    print((str(type(e)) + ":" + str(e)))
                    print((result.text))
            summaries.append(
                {"RespCode": result.status_code, "TestName": testCase["name"], "Result": result.text}
                )

    t = PrettyTable(["TestName", "RCode", "Result"])
    for summary in summaries:
        t.add_row([cut_msg(summary["TestName"]), summary["RespCode"], cut_msg(summary["Result"], limit=100)])
    print(t)
