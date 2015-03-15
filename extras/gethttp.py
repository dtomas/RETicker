#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

import urllib
import sys
import os

"""--------------------------------------------------------------------------------------------"""
"""------------------------------ The Funtion to fetch http data ------------------------------"""
"""----- it is started after a fork() as a special task to prevent blocking the Ticker --------"""
""" it will be called from tool.py with 4 arguments:
					       url_address, filename, use_proxy, proxy_address """

proxy = sys.argv[4]
if proxy.find("://") == -1: proxy = "http://" + proxy

# Depending on your Version of Python (?) the use_proxy field might be 'True' or '1' rsp 'False' or '0'
if sys.argv[3] == "True" or sys.argv[3] == "1":
	#print "use_proxy '" + proxy + "'"
	os.environ["http_proxy"]=proxy
else:
	#print "don't use proxy ('" + proxy + "')"
	os.environ["http_proxy"]=""

try: urllib.urlretrieve( sys.argv[ 1 ], sys.argv[ 2 ] )
except (IOError, EOFError): sys.exit(1)
