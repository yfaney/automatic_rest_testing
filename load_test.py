#!/usr/local/bin/python

import http.client
import json
from http.client import HTTPResponse
from optparse import OptionParser
from urllib.parse import urlencode, quote

import requests
import oauth_util_v2 as oauth_util
from prettytable import PrettyTable
from requests import Response
from requests_oauthlib import OAuth1

import os
import time
from datetime import datetime
from multiprocessing import Process

from jinja2 import Template

from utils.configmanager import ConfigManager
from utils.parsingmanager import parse_options
from utils.stringutil import cut_msg
import logging
import sys

COLOR_TABLE = {
  "Black": "\u001b[30m",
  "Red": "\u001b[31m",
  "Green": "\u001b[32m",
  "Yellow": "\u001b[33m",
  "Blue": "\u001b[34m",
  "Magenta": "\u001b[35m",
  "Cyan": "\u001b[36m",
  "White": "\u001b[37m",
  "Reset": "\u001b[0m"
}

log = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
out_hdlr.setLevel(logging.DEBUG)
log.addHandler(out_hdlr)
log.setLevel(logging.DEBUG)

def color_text(color, text):
  return "%s%s%s" % (COLOR_TABLE[color], text, COLOR_TABLE["Reset"])


def color_status_code(status_code):
  if status_code >= 200 and status_code < 300:
    return color_text("Green", str(status_code))
  elif status_code >=400 and status_code < 500:
    return color_text("Yellow", str(status_code))
  elif status_code >=500 and status_code < 600:
    return color_text("Red", str(status_code))
  else:
    return status_code


def get_params(test_data, result, variables):
  updated_variables = {}
  for key_item in variables.keys():
    key_info = variables[key_item]
    result_point = result
    while True:
      #log.debug(key_info)
      #log.debug(result_point)
      if key_info["type"] == "dict":
        result_point = result_point[key_info["key"]]
        key_info = key_info["child"]
      elif key_info["type"] == "list":
        result_point = result_point[int(key_info["index"])]
        key_info = key_info["child"]
      else:
        test_data[key_item] = result_point[key_info["key"]]
        updated_variables[key_item] = result_point[key_info["key"]]
        break
  #log.debug("Now test_data has: %s" % test_data)
  return updated_variables


def print_variables(test_data, updated_variables):
  t = PrettyTable(test_data.keys())
  variables = []
  for key in test_data.keys():
    if key in updated_variables:
      variables.append(color_text("Yellow", str(test_data[key])))
    else:
      variables.append(str(test_data[key]))
  t.add_row(variables)
  return t


def run_test_case(test_data, scenario, iteration):
  proc = os.getpid()
  error_log = []
  process_name = "PID(%d)" % proc if "name" not in test_data else "PID(%d) <%s>" % (proc, test_data['name'])
  for i in range(0, iteration):
    log.info("%s Iteration:%d Start" % (process_name, i))
    for step in scenario:
      urlTemplate = Template(step['url'])
      renderedUrl = urlTemplate.render(**test_data)
      log.info("%s <%s>\tRequesting: %s, method=%s" % (process_name, step['name'], renderedUrl, step['method']))
      if "data" in step:
        dataTemplate = Template(json.dumps(step['data']))
        renderedData = dataTemplate.render(**test_data)
        log.debug("%s Data: %s" % (process_name, renderedData))
        result = client.req_oauth(renderedUrl, step['method'], json.loads(renderedData))
      else:
        result = client.req_oauth(renderedUrl, step['method'])
      log.info("%s Status: %s" % (process_name, color_status_code(result.status_code)))
      log.debug("%s Result: %s" % (process_name, result.text))
      if result.status_code >= 200 and result.status_code < 400:
        if len(result.text) > 0:
          variableTemplate = Template(json.dumps(step["variables"]))
          renderedVariable = variableTemplate.render(**test_data)
          updated_variables = get_params(test_data, json.loads(result.text), json.loads(renderedVariable))
          log.info("%s ---Variables---\n%s" % (process_name, print_variables(test_data, updated_variables)))
      else:
        error_log.append({"iteration": iteration, "status": result.status_code, "message": result.text})
      if "delayToNext" in step:
        log.info("%s Sleeping %d seconds..." % (process_name, step["delayToNext"]))
        time.sleep(step["delayToNext"])
    log.info("%s Iteration:%d End" % (process_name, i))
    
  if len(error_log) > 0:
    log.error("%s %d Error Occurred\n" % (process_name, len(error_log)))
    for error_item in error_log:
      log.error(
        "%s iteration: %d | status: %s\n %s" 
          % (process_name, error_item['iteration'], color_status_code(error_item['status']), error_item['message'])
      )


def run_test_main(data):  
  procs = []
  iteration = int(data["TestIteration"])
  # Do multi process run
  for test_data in data["TestData"]:
    proc = Process(target=run_test_case, args=(test_data, data["Scenario"],iteration))
    procs.append(proc)
    proc.start()
  for proc in procs:
    proc.join()


"""
====================== Main ===========================
"""
if __name__ == "__main__":
  configFilePath, testFilePath, detail = parse_options()

  if detail:
    log.setLevel(logging.DEBUG)
  else:
    log.setLevel(logging.INFO)

  if configFilePath is None:
    print ("No config file is provided.")
    exit(-1)
  if testFilePath is None:
    print ("No test file is provided.")
    exit(-1)
  
  config = ConfigManager(configFilePath).parse()
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

  # Logging file as well
  file_hdlr = logging.FileHandler('logs/load_test_%s_%s.log' % (oauth_user, datetime.now().strftime("%Y%m%d-%H%M%S")))
  file_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
  file_hdlr.setLevel(logging.DEBUG)
  log.addHandler(file_hdlr)

  client = oauth_util.CernerOAuthUtil(oauth_host, oauth_port, oauth_url, oauth_user, oauth_pw,
    use_http=oauth_use_http,
    consumer_key=oauth_consumer_key,
    consumer_secret=oauth_consumer_secret,
    domain=domain)
  
  with open(testFilePath) as data_file:
    data = json.load(data_file)
    log.info("Load testing:%s" % testFilePath)
    run_test_main(data)
